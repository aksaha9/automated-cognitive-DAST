from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from app.models import ScanRequest, ScanStatus, ScanResult, ScanState, Vulnerability, ScanType, ReportFormat
from app.services.zap_service import ZapService
import uuid
from datetime import datetime
import asyncio

router = APIRouter()
zap_service = ZapService()

# In-memory store for MVP. 
scans = {}

async def run_scan_task(scan_id: str, target_url: str):
    """Background task to run ZAP spider and active scan."""
    try:
        scans[scan_id].state = ScanState.RUNNING
        
        # 1. Spider
        spider_id = zap_service.start_spider(target_url)
        scans[scan_id].spider_id = spider_id
        
        while True:
            if scans[scan_id].state == ScanState.STOPPED: # Check if stopped
                return 

            progress = zap_service.get_spider_status(spider_id)
            scans[scan_id].progress = int(progress) // 2 # Scale to 0-50%
            if int(progress) >= 100:
                break
            await asyncio.sleep(2)
            
        # 2. Active Scan
        ascan_id = zap_service.start_active_scan(target_url)
        scans[scan_id].ascan_id = ascan_id
        
        while True:
            if scans[scan_id].state == ScanState.STOPPED:
                return

            progress = zap_service.get_active_scan_status(ascan_id)
            scans[scan_id].progress = 50 + (int(progress) // 2) # Scale 50-100%
            if int(progress) >= 100:
                break
            await asyncio.sleep(2)

        scans[scan_id].state = ScanState.COMPLETED
        scans[scan_id].progress = 100
        
    except Exception as e:
        print(f"Scan failed: {e}")
        scans[scan_id].state = ScanState.FAILED

@router.post("/scan/{scan_id}/stop")
async def stop_scan(scan_id: str):
    if scan_id not in scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan = scans[scan_id]
    zap_service.stop_scan(spider_id=getattr(scan, 'spider_id', None), ascan_id=getattr(scan, 'ascan_id', None))
@router.post("/scan/{scan_id}/stop")
async def stop_scan(scan_id: str):
    if scan_id not in scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan = scans[scan_id]
    zap_service.stop_scan(spider_id=scan.spider_id, ascan_id=scan.ascan_id)
    scan.state = ScanState.STOPPED
    return scan


@router.post("/scan", response_model=ScanStatus)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    # Normalize URL: Ensure it starts with http:// or https://
    target_url = request.target_url
    if not target_url.startswith("http"):
        target_url = "https://" + target_url

    scan_id = str(uuid.uuid4())
    scan_status = ScanStatus(
        id=scan_id,
        state=ScanState.PENDING,
        progress=0,
        created_at=datetime.now(),
        target_url=target_url
    )
    scans[scan_id] = scan_status
    
    background_tasks.add_task(run_scan_task, scan_id, target_url)
    return scan_status

@router.get("/scan/{scan_id}", response_model=ScanStatus)
async def get_scan_status(scan_id: str):
    if scan_id not in scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scans[scan_id]

@router.get("/scans", response_model=list[ScanStatus])
async def list_scans():
    return list(scans.values())

def convert_to_sarif(scan_id: str, target_url: str, vulnerabilities: list[Vulnerability]):
    """Converts internal vulnerabilities to SARIF format."""
    rules = {}
    results = []
    
    for vuln in vulnerabilities:
        rule_id = vuln.cweid or "0"
        if rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "name": vuln.alert,
                "shortDescription": {
                    "text": vuln.alert
                },
                "fullDescription": {
                    "text": vuln.description
                },
                "help": {
                    "text": vuln.solution,
                    "markdown": vuln.solution
                },
                "properties": {
                    "risk": vuln.risk,
                    "confidence": vuln.confidence
                }
            }
            
        results.append({
            "ruleId": rule_id,
            "level": "error" if vuln.risk == "High" else "warning" if vuln.risk == "Medium" else "note",
            "message": {
                "text": vuln.description
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": vuln.url
                        }
                    }
                }
            ]
        })

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Automated Cognitive DAST (ZAP)",
                        "rules": list(rules.values())
                    }
                },
                "results": results
            }
        ]
    }

def convert_to_ocsf(scan_id: str, target_url: str, vulnerabilities: list[Vulnerability]):
    """Converts internal vulnerabilities to OCSF format (Vulnerability Finding)."""
    findings = []
    for vuln in vulnerabilities:
        findings.append({
            "activity_id": 1, # Create
            "category_uid": 2, # Findings
            "class_uid": 2001, # Vulnerability Finding
            "severity_id": 1, # Unknown mapping for now, plain mapping below
            "severity": vuln.risk,
            "status_id": 1, # New
            "time": int(datetime.now().timestamp() * 1000),
            "type_uid": 200101,
            "finding": {
               "title": vuln.alert,
               "desc": vuln.description,
               "remediation": {
                   "desc": vuln.solution
               }
            },
            "resource": {
                "type": "URL",
                "uid": vuln.url
            },
            "metadata": {
                "product": {
                    "name": "Automated Cognitive DAST",
                    "vendor_name": "Cognitive Security"
                },
                "profiles": ["security_control"]
            }
        })
    return {"findings": findings}

@router.get("/scan/{scan_id}/results") # Removed response_model to allow returning arbitrary JSON for SARIF/OCSF
async def get_scan_results(scan_id: str, format: ReportFormat = Query(ReportFormat.JSON, description="Output format: JSON, SARIF, or OCSF")):
    if scan_id not in scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan = scans[scan_id]
    
    # Retrieve alerts from ZAP for this target
    raw_alerts = zap_service.get_alerts(scan.target_url)
    
    vulnerabilities = []
    for alert in raw_alerts:
        vulnerabilities.append(Vulnerability(
            alert=alert.get('alert', 'Unknown'),
            risk=alert.get('risk', 'Unknown'),
            confidence=alert.get('confidence', 'Unknown'),
            description=alert.get('description', ''),
            solution=alert.get('solution', ''),
            url=alert.get('url', ''),
            cweid=alert.get('cweid', '0'),
            wascid=alert.get('wascid', '0')
        ))

    if format == ReportFormat.SARIF:
        return convert_to_sarif(scan_id, scan.target_url, vulnerabilities)
    elif format == ReportFormat.OCSF:
        return convert_to_ocsf(scan_id, scan.target_url, vulnerabilities)
    else:
        # Default JSON format
        return ScanResult(
            scan_id=scan_id,
            vulnerabilities=vulnerabilities,
            summary={"count": len(vulnerabilities)},
            format=ReportFormat.JSON
        )

# AI Integration
from app.services.llm_service import LLMService
from app.models import AnalyzeRequest, AnalysisResponse

llm_service = LLMService()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_intent(request: AnalyzeRequest):
    """
    Analyzes a natural language security requirement and returns a scan configuration.
    """
    analysis = llm_service.analyze_intent(request.prompt)
    return AnalysisResponse(
        scan_type=analysis.get("scan_type", "WEB"),
        checks=analysis.get("checks", []),
        reasoning=analysis.get("reasoning", "")
    )

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class ScanType(str, Enum):
    API = "API"
    WEB = "WEB"

class ScanState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"

class ReportFormat(str, Enum):
    JSON = "JSON"
    SARIF = "SARIF"
    OCSF = "OCSF"

class ScanRequest(BaseModel):
    target_url: str
    scan_type: ScanType
    report_format: Optional[ReportFormat] = ReportFormat.JSON
    scan_types: Optional[List[str]] = []

class AnalyzeRequest(BaseModel):
    prompt: str

class AnalysisResponse(BaseModel):
    scan_type: str
    checks: List[str]
    reasoning: Optional[str] = ""

class ScanStatus(BaseModel):
    id: str
    state: ScanState
    progress: int
    created_at: datetime
    target_url: str
    spider_id: Optional[str] = None
    ascan_id: Optional[str] = None

class Vulnerability(BaseModel):
    alert: str
    risk: str
    confidence: str
    description: str
    solution: str
    url: str
    cweid: Optional[str] = None
    wascid: Optional[str] = None

class ScanResult(BaseModel):
    scan_id: str
    vulnerabilities: List[Vulnerability]
    summary: Dict[str, Any]
    format: ReportFormat = ReportFormat.JSON
    raw_output: Optional[Dict[str, Any]] = None

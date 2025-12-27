import os
import subprocess
import tempfile
import json
import requests
from fastmcp import FastMCP

# Load LLM config from llm_config.json (copied by entrypoint.sh)
try:
    with open("llm_config.json", "r") as f:
        llm_config = json.load(f)
except FileNotFoundError:
    llm_config = {}

API_KEY = os.getenv("GEMINI_API_KEY") or llm_config.get("api_key")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY env var or api_key in llm_config.json is required.")

MODEL = llm_config.get("model", "gemini-3-pro-preview")
BASE_URL = llm_config.get("base_url", "https://generativelanguage.googleapis.com")

# Correct initialization for current fastmcp (2.x+)
mcp = FastMCP(
    name="ZAP DAST Scanner",
    instructions=(
        "This server performs automated Dynamic Application Security Testing (DAST) "
        "using OWASP ZAP in headless mode. It uses Google Gemini to interpret natural "
        "language requests and automatically generate custom active scan rule configurations. "
        "The only available tool is 'perform_dast_scan', which runs a full scan on a target URL "
        "focused on the described vulnerabilities and returns a detailed HTML report."
    )
)

# Known ZAP active scan rules
KNOWN_RULES = {
    "SQL Injection": ["40018", "SQL Injection"],
    "SQL Injection - MySQL": ["40019", "SQL Injection - MySQL"],
    "SQL Injection - Hypersonic SQL": ["40020", "SQL Injection - Hypersonic SQL"],
    "SQL Injection - Oracle": ["40021", "SQL Injection - Oracle"],
    "SQL Injection - PostgreSQL": ["40022", "SQL Injection - PostgreSQL"],
    "SQL Injection - SQLite": ["40024", "SQL Injection - SQLite"],
    "SQL Injection (RDBMS-independent advanced)": ["40042", "SQL Injection (RDBMS-independent advanced)"],
    "Absence of Anti-CSRF Tokens": ["10202", "Absence of Anti-CSRF Tokens"],
}

def call_llm(prompt: str) -> str:
    """Call Google Gemini API to generate ZAP config content."""
    url = f"{BASE_URL}/v1beta/models/{MODEL}:generateContent"
    full_url = f"{url}?key={API_KEY}"

    headers = {"Content-Type": "application/json"}

    system_prompt = (
        "You are an expert in OWASP ZAP active scan rule configuration. "
        "Generate ONLY the config lines setting relevant rules to FAIL. "
        "Format: one rule per line as 'rule_id\\tFAIL\\tRule Name' (use actual tabs). "
        "Use only the exact rule IDs and names provided. "
        "No explanations, no markdown, no extra text. "
        "If no rules match, include at least the main SQL Injection and Anti-CSRF rules."
    )

    data = {
        "contents": [{"role": "user", "parts": [{"text": system_prompt + "\n\n" + prompt}]}],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 8192
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    response = requests.post(full_url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()

    try:
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        raise ValueError(f"Unexpected Gemini response: {result}")


import datetime

def _get_timestamped_filename(format_ext: str) -> str:
    # scan_report_<format>_yyyymmdd_hhmm_tz.json
    now = datetime.datetime.now(datetime.timezone.utc)
    # Using UTC as tz
    ts_str = now.strftime("%Y%m%d_%H%M_UTC")
    return f"scan_report_{format_ext}_{ts_str}.json"

def _parse_scan_stats(report_path: str, report_format: str) -> str:
    """Parses JSON report (ZAP format or SARIF) to extract stats."""
    try:
        with open(report_path, "r") as f:
            data = json.load(f)
        
        # Detect ZAP JSON format (has "site" array)
        if "site" in data:
            alerts = []
            for site in data["site"]:
                alerts.extend(site.get("alerts", []))
                
            total = 0
            # Group by Name and Risk Code/Desc
            # Mapping: 3=High, 2=Med, 1=Low, 0=Info
            severity_counts = {"3": 0, "2": 0, "1": 0, "0": 0} 
            severity_names = {"3": "High", "2": "Medium", "1": "Low", "0": "Info"}
            
            finding_counts = {} # Key: Name, Value: {count, risk}

            for alert in alerts:
                risk_code = alert.get("riskcode", "0")
                risk_desc = alert.get("riskdesc", "Unknown")
                name = alert.get("name", "Unknown")
                try:
                    count = int(alert.get("count", 1))
                except (ValueError, TypeError):
                    count = 1
                
                total += count

                if risk_code in severity_counts:
                    severity_counts[risk_code] += count
                
                if name not in finding_counts:
                    finding_counts[name] = {"count": 0, "risk": risk_desc}
                finding_counts[name]["count"] += count

            stats = f"Total Vulnerabilities: {total}\n\nSeverity Breakdown:\n"
            for code in ["3", "2", "1", "0"]:
                stats += f"  {severity_names[code]}: {severity_counts[code]}\n"
            
            stats += "\nFinding Breakdown (Count | Risk | Name):\n"
            # Sort by risk code desc (3->0) then count
            def sort_key(item):
                name, data = item
                # Sort by count frequency
                return data["count"]

            for name, info in sorted(finding_counts.items(), key=lambda x: x[1]["count"], reverse=True):
                 stats += f"  - {info['count']} | {info['risk']} | {name}\n"
            
            return stats

        # Detect SARIF format (has "runs" array)
        elif "runs" in data:
            results = []
            for run in data.get("runs", []):
                results.extend(run.get("results", []))
            
            total = len(results)
            rule_counts = {}
            
            for res in results:
                rule_id = res.get("ruleId", "Unknown")
                # text message might contain risk info?
                msg = res.get("message", {}).get("text", "")
                level = res.get("level", "none") # warning, error, note
                
                key = f"{rule_id} ({level})"
                rule_counts[key] = rule_counts.get(key, 0) + 1
            
            stats = f"Total Results: {total}\n\nRule Breakdown:\n"
            for rkey, count in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True):
                stats += f"  - {rkey}: {count}\n"
            return stats
            
        return "(Report structure not recognized - neither ZAP JSON site[] nor SARIF runs[])"
    except Exception as e:
        return f"(Failed to parse stats: {e})"

def _perform_dast_scan_logic(target_url: str, vulnerability_description: str, report_format: str = "html") -> str:
    prompt = f"""
User wants to test for: {vulnerability_description}

Available rules (use exact IDs and names):
{json.dumps(KNOWN_RULES, indent=2)}

Generate only the relevant config lines with threshold FAIL.
"""
    config_content = call_llm(prompt).strip()

    if not config_content:
        return "Failed to generate ZAP configuration."

    reports_dir = os.path.abspath(os.getenv("REPORTS_DIR", "reports"))
    os.makedirs(reports_dir, exist_ok=True)

    # Write config to /zap/wrk/scan.conf
    conf_path = "/zap/wrk/scan.conf"
    with open(conf_path, "w") as f:
        f.write(config_content)

    # Determine format and Generate Timestamped Filename
    report_format = report_format.lower()
    
    if report_format == "json":
        report_flag = "-J"
        file_ext = "json"
    elif report_format == "md" or report_format == "markdown":
        report_flag = "-w"
        file_ext = "md"
    elif report_format == "xml":
        report_flag = "-x"
        file_ext = "xml"
    elif report_format == "sarif":
        # Use JSON output for SARIF
        report_flag = "-J"
        file_ext = "sarif" # Filename identifier
    else:
        report_flag = "-r"
        file_ext = "html"

    # Generate the requested filename pattern
    final_filename = _get_timestamped_filename(file_ext)
    
    # Internal filename for ZAP to write to (in /zap/wrk)
    
    # Pass absolute paths pointing to /zap/wrk
    cmd = [
        "/zap/zap-full-scan.py",
        "-t", target_url,
        "-c", conf_path,
        "-z", "-config api.disablekey=true -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true",
        report_flag, f"/zap/wrk/{final_filename}"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(conf_path):
        os.unlink(conf_path)

    # Move report to reports_dir
    src_report = f"/zap/wrk/{final_filename}"
    dest_report = os.path.join(reports_dir, final_filename)
    
    scan_success = False
    if os.path.exists(src_report):
        import shutil
        shutil.copy2(src_report, dest_report)
        os.unlink(src_report)
        scan_success = True
    elif result.returncode not in [0, 1]: 
        return f"ZAP scan failed:\n{result.stderr}"

    if not scan_success or not os.path.exists(dest_report):
        return f"Scan completed (Return Code: {result.returncode}) but report file not generated.\nStderr: {result.stderr}"

    # Generate Stats Preview (instead of raw text)
    if report_format in ["json", "sarif"]:
        preview = _parse_scan_stats(dest_report, report_format)
    else:
         # Fallback for HTML/MD/XML
        preview = "(Structured stats not available for this format)"

    # Upload to GCS if configured
    gcs_bucket = os.getenv("GCS_REPORT_BUCKET")
    gcs_uri = "Not configured"
    
    if gcs_bucket and os.path.exists(dest_report):
        try:
            from google.cloud import storage
            storage_client = storage.Client()
            bucket = storage_client.bucket(gcs_bucket)
            # Use same filename structure in GCS: scan_reports/<filename>
            blob_name = f"scan_reports/{final_filename}"
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(dest_report)
            gcs_uri = f"gs://{gcs_bucket}/{blob_name}"
            print(f"Report uploaded to: {gcs_uri}")
        except Exception as e:
            gcs_uri = f"Upload failed: {str(e)}"
            print(gcs_uri)

    summary = (
        f"DAST scan completed for {target_url}\n"
        f"Focus: {vulnerability_description}\n"
        f"Format: {report_format}\n\n"
        f"Generated config:\n{config_content}\n\n"
        f"Full report saved to (Local): ./reports/{final_filename}\n"
        f"GCS Report URI: {gcs_uri}\n"
        f"Scan Statistics:\n{preview}"
    )

    return summary


@mcp.tool(
    name="perform_dast_scan",
    description="Perform a full OWASP ZAP active scan on a target website using a custom rule configuration generated from a natural language description of vulnerabilities."
)
def perform_dast_scan(target_url: str, vulnerability_description: str, report_format: str = "html") -> str:
    """Entry point for MCP tool execution. report_format options: html, json, xml, md"""
    return _perform_dast_scan_logic(target_url, vulnerability_description, report_format)


if __name__ == "__main__":
    if os.getenv("ONE_SHOT_MODE") == "1":
        target = os.getenv("TARGET_URL_ONE_SHOT")
        desc = os.getenv("VULN_DESC_ONE_SHOT")
        fmt = os.getenv("REPORT_FORMAT_ONE_SHOT", "html")

        if not target or not desc:
            print("Error: TARGET_URL_ONE_SHOT and VULN_DESC_ONE_SHOT must be set in one-shot mode.")
            exit(1)

        print(f"Starting one-shot DAST scan (Format: {fmt})...")
        result = _perform_dast_scan_logic(target, desc, fmt)
        print("\n=== SCAN RESULT ===\n")
        print(result)
    else:
        mcp.run(transport="streamable-http", port=8000)
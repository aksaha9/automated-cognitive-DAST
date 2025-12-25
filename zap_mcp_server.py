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

    # Write config to /zap/wrk/scan.conf to satisfy ZAP's check
    conf_path = "/zap/wrk/scan.conf"
    with open(conf_path, "w") as f:
        f.write(config_content)

    # Determine report flag and filename based on format
    # zap-full-scan.py options: -r (html), -J (json), -w (md), -x (xml)
    report_format = report_format.lower()
    
    if report_format == "json":
        report_flag = "-J"
        report_filename = "zap_report.json"
    elif report_format == "md" or report_format == "markdown":
        report_flag = "-w"
        report_filename = "zap_report.md"
    elif report_format == "xml":
        report_flag = "-x"
        report_filename = "zap_report.xml"
    elif report_format == "sarif":
        # Note: zap-full-scan.py doesn't have a direct -sarif flag. 
        # We'll use JSON as a fallback/closest match for this script's scope
        # unless we use the API, which is complex here.
        # Alternatively, newer ZAP *might* support -r report.sarif? 
        # Let's use JSON to be safe and ensure data extraction works.
        report_flag = "-J"
        report_filename = "zap_report.sarif.json"
    else:
        # Default to HTML
        report_flag = "-r"
        report_filename = "zap_report.html"

    # Pass absolute paths pointing to /zap/wrk to satisfy ZAP's check
    cmd = [
        "/zap/zap-full-scan.py",
        "-t", target_url,
        "-c", conf_path,
        "-z", "-config api.disablekey=true -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true",
        report_flag, f"/zap/wrk/{report_filename}"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(conf_path):
        os.unlink(conf_path)

    # ZAP scan scripts might return 0, 1, or 2. 
    # Logic: if report is generated, we consider it a success for our purpose (extracting results).
    
    # Move report to reports_dir
    src_report = f"/zap/wrk/{report_filename}"
    dest_report = os.path.join(reports_dir, report_filename)
    
    if os.path.exists(src_report):
        import shutil
        shutil.copy2(src_report, dest_report)
        os.unlink(src_report)
    elif result.returncode not in [0, 1]: 
        # If report missing and return code indicates failure (not 0 or 1 usually means compliance fail)
        # Actually 1 means "issues found", 2 means "failure". 
        return f"ZAP scan failed:\n{result.stderr}"

    if not os.path.exists(dest_report):
        return f"Scan completed (Return Code: {result.returncode}) but report file not generated.\nStderr: {result.stderr}"

    # Read report content for summary (truncated)
    try:
        with open(dest_report, "r", encoding="utf-8") as f:
            report_content = f.read()
            preview = report_content[:2000] + "..." if len(report_content) > 2000 else report_content
    except Exception:
        preview = "(Preview unavailable)"

    summary = (
        f"DAST scan completed for {target_url}\n"
        f"Focus: {vulnerability_description}\n"
        f"Format: {report_format}\n\n"
        f"Generated config:\n{config_content}\n\n"
        f"Full report saved to: ./reports/{report_filename}\n"
        f"Report preview:\n{preview}"
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
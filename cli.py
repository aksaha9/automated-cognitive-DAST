#!/usr/bin/env python3
import argparse
import subprocess
import time
import sys
import requests
import json
import os

BACKEND_URL = "http://localhost:8000"
SCAN_ENDPOINT = f"{BACKEND_URL}/api/scan"
REPORT_ENDPOINT = f"{BACKEND_URL}/api/report"

def run_command(cmd, check=True):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if check and result.returncode != 0:
        print(f"Error executing command: {cmd}\n{result.stderr}")
        sys.exit(1)
    return result

def check_backend_health():
    print("Waiting for backend connectivity...")
    for _ in range(30):
        try:
            r = requests.get(f"{BACKEND_URL}/docs", timeout=2)
            if r.status_code == 200:
                print("Backend active.")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    return False

def main():
    parser = argparse.ArgumentParser(description="Ephemeral DAST Scan CLI")
    parser.add_argument("--target", required=True, help="Target URL to scan")
    parser.add_argument("--type", default="WEB", choices=["WEB", "API", "BASELINE"], help="Scan Type")
    parser.add_argument("--checks", nargs="*", help="List of checks to enable (e.g. 'SQL Injection' 'XSS')")
    parser.add_argument("--format", default="json", choices=["json", "sarif", "html"], help="Output format")
    parser.add_argument("--rules-file", help="Path to custom YAML rules file")
    parser.add_argument("--output", default="scan_report", help="Output filename prefix")
    parser.add_argument("--keep-alive", action="store_true", help="Do not spin down containers after scan")
    
    args = parser.parse_args()

    # Load Custom Rules if provided
    custom_rules = None
    if args.rules_file:
        try:
            import yaml
            with open(args.rules_file, 'r') as f:
                data = yaml.safe_load(f)
                custom_rules = data.get('rules', data) # Handle if wrapped in 'rules' or flat
                print(f"Loaded custom rules from {args.rules_file}")
        except ImportError:
            print("Error: PyYAML not installed. Cannot parse rules file.")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading rules file: {e}")
            sys.exit(1)

    # 1. Spin Up Containers (Backend + ZAP only)
    print("Spinning up scan infrastructure...")
    # Using docker-compose to start specific services
    run_command("docker compose up -d backend zap")

    if not check_backend_health():
        print("Failed to connect to backend. Exiting.")
        run_command("docker compose down")
        sys.exit(1)

    # 2. Trigger Scan
    payload = {
        "target_url": args.target,
        "scan_type": args.type,
        "checks": args.checks if args.checks else [],
        "custom_rules": custom_rules
    }
    
    print(f"Initiating scan for {args.target}...")
    try:
        r = requests.post(SCAN_ENDPOINT, json=payload)
        r.raise_for_status()
        data = r.json()
        scan_id = data["scan_id"]
        print(f"Scan started. ID: {scan_id}")
    except Exception as e:
        print(f"Failed to start scan: {e}")
        if not args.keep_alive:
            run_command("docker compose down")
        sys.exit(1)

    # 3. Poll Progress
    while True:
        try:
            r = requests.get(f"{SCAN_ENDPOINT}/{scan_id}")
            status = r.json()
            state = status["state"]
            progress = status["progress"]
            
            print(f"Status: {state} ({progress}%)")
            
            if state in ["COMPLETED", "FAILED", "STOPPED"]:
                break
            
            time.sleep(5)
        except Exception as e:
            print(f"Polling error: {e}")
            break

    # 4. Retrieve Report
    if state == "COMPLETED":
        print("Scan completed. Downloading report...")
        try:
            # Correct endpoint is /api/report (generated from current session state)
            report_url = REPORT_ENDPOINT
            print(f"Fetching report from {report_url}...")
            r = requests.get(report_url, params={"format": args.format})
            if r.status_code == 200:
                fname = f"{args.output}.{args.format}"
                with open(fname, "wb") as f:
                    f.write(r.content)
                print(f"Report saved to {fname}")
            else:
                print(f"Failed to fetch report: {r.status_code} {r.text}")
        except Exception as e:
            print(f"Report download error: {e}")
    else:
        print("Scan did not complete successfully.")

    # 5. Teardown
    if not args.keep_alive:
        print("Tearing down infrastructure...")
        run_command("docker compose down")

if __name__ == "__main__":
    main()

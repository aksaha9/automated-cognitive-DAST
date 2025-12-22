import os
import sys
import time
import json
import argparse
import yaml
from app.services.zap_service import ZapService
from app.services.llm_service import LLMService
# Mocking FastAPI models usage if needed, or importing
from app.models import ScanType

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    from google.cloud import storage
    print(f"Uploading {source_file_name} to gs://{bucket_name}/{destination_blob_name}")
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print("Upload complete.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--type", default="WEB", help="Scan Type (WEB/API/BASELINE)")
    parser.add_argument("--checks", nargs="*", help="Specific checks to enable")
    parser.add_argument("--rules-file", help="Path to custom YAML scan rules")
    parser.add_argument("--ai-prompt", help="Natural language prompt for AI configuration")
    parser.add_argument("--bucket", help="GCS Bucket to upload report")
    parser.add_argument("--format", default="json", choices=["json", "sarif", "html"], help="Output format")
    parser.add_argument("--output", help="Full path to save the report file")
    args = parser.parse_args()

    print(f"Starting Ephemeral Scan for {args.url}")

    # 1. Config & AI Analysis
    scan_type_str = args.type
    checks = args.checks if args.checks else []
    
    if args.ai_prompt:
        print(f"AI Assist Enabled. Analyzing prompt: '{args.ai_prompt}'")
        try:
            llm_service = LLMService()
            # Ensure model is ready (API key from env/config)
            if not llm_service.model and not llm_service.settings.ai_api_key:
                 print("Error: AI Prompt provided but no API Key configured.")
                 sys.exit(1)
                 
            analysis = llm_service.analyze_intent(args.ai_prompt)
            print("AI Analysis Result:")
            print(json.dumps(analysis, indent=2))
            
            # Application Logic: AI Config overrides defaults, but CLI args override AI?
            # Usually CLI specific args should win, but if user asked AI, they likely want AI's choice.
            # Strategy: Use AI result, unless CLI arg was EXPLICITLY provided (hard to track with argparse defaults).
            # We will treat AI as the "Configuration", so it overrides default WEB.
            
            scan_type_str = analysis.get("scan_type", scan_type_str)
            if not checks: # Only use AI checks if user didn't specify manual checks
                checks = analysis.get("checks", [])
                
        except Exception as e:
            print(f"AI Analysis Failed: {e}")
            sys.exit(1)

    # 2. Rule Loading
    custom_rules = None
    if args.rules_file:
        try:
            with open(args.rules_file, 'r') as f:
                data = yaml.safe_load(f)
                custom_rules = data.get('rules', data)
                print(f"Loaded custom rules from {args.rules_file}")
        except Exception as e:
            print(f"Failed to load rules file: {e}")
            sys.exit(1)

    # 3. Initialize Service
    service = ZapService()
    
    scan_id = "job-" + str(int(time.time()))
    
    # Map string type to Enum
    scan_type_enum = ScanType.WEB
    if scan_type_str.upper() == "API":
        scan_type_enum = ScanType.API
    elif scan_type_str.upper() == "BASELINE":
        scan_type_enum = ScanType.BASELINE
    
    print(f"Configuring Scan: Type={scan_type_enum.value}, Checks={checks}")
    
    # Configure Policy
    # We use the service's internal method via start_scan logic or direct configure
    # Since we are running in a script, we can just call start_scan which handles logic
    # BUT we need to wait for it.
    
    print("Launching Scan Task...")
    service.start_scan(scan_id, args.url, scan_type_enum, checks, custom_rules)
    
    # 4. Poll Progress
    print("Polling progress...")
    while True:
        status = service.get_scan_status(scan_id)
        if status.state == "RUNNING":
             # Print simplified progress bar
             bar = "#" * (status.progress // 5)
             sys.stdout.write(f"\rProgress: [{bar:<20}] {status.progress}%")
             sys.stdout.flush()
        else:
             print(f"\nState: {status.state}")
             
        if status.state in ["COMPLETED", "FAILED", "STOPPED"]:
            break
        time.sleep(5)
    
    # 5. Report & Teardown
    if status.state == "COMPLETED":
        print("Scan Complete. Generating Report...")
        report_data = service.generate_report(args.format)
        
        # Determine output file
        if args.output:
            report_file = args.output
        else:
            report_file = f"scan_report.{args.format}"
            
        mode = "w" if args.format != "pdf" else "wb"
        
        try:
            with open(report_file, mode) as f:
                if isinstance(report_data, (dict, list)):
                    json.dump(report_data, f, indent=2)
                else:
                    f.write(report_data)
            print(f"Report saved to {report_file}")
        except Exception as e:
            print(f"Failed to write report to {report_file}: {e}")
        
        # Upload if bucket provided
        bucket = args.bucket or os.environ.get("GCS_BUCKET")
        if bucket:
            dest = f"reports/{scan_id}.{args.format}"
            try:
                upload_to_gcs(bucket, report_file, dest)
            except Exception as e:
                print(f"Failed to upload to GCS: {e}")
        else:
             print("No GCS bucket provided. Report is local only.")
            
    else:
        print("Scan Failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()

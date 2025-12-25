# Walkthrough: Automated Cognitive DAST

## 1. Public Live Demo
We have deployed a live instance of the application on Google Cloud Run. You can access it here:
👉 **[https://automated-cognitive-dast-service-510071073932.us-central1.run.app/](https://automated-cognitive-dast-service-510071073932.us-central1.run.app/)**

## 2. AI Assisted Scan Verification
The following recording demonstrates an AI-Assisted scan running on the public instance.
**Scenario**: The user asks the AI to **"Can this target site be exploited for getting unauthorised data out and leaked?"** on `https://example.com`.
**Process**:
1.  User inputs natural language prompt.
2.  Gemini analyzes intent and configures ZAP.
3.  Scan executes and results are displayed.

![AI Assisted Scan Demo](docs/images/ai_scan_data_leak_check.webp)

## 3. Ephemeral Headless Scan Verification
We verified the **Ephemeral Job** functionality using the Google Cloud CLI. This mode bypasses the UI and runs the scan as a serverless job.

**Command Executed:**
```bash
gcloud run jobs execute zap-mcp-server-job \
  --region us-central1 \
  --args="--target=https://example.com" \
  --args="--vuln=I want to check if this target is susceptible to data harvesting attacks" \
  --args="--format=sarif" \
  --args="--output=report.json"
```

**Execution Output:**
```console
✓ Creating execution...
  ✓ Provisioning resources... Provisioned imported containers.
Done.
Execution [zap-mcp-server-job-5xs7m] has successfully started running.

View details about this execution by running:
gcloud run jobs executions describe zap-mcp-server-job-5xs7m
```

## 4. Cloud Run Deployment Guide

### Configuration Prerequisites
To run this application successfully on Cloud Run, ensure the following configurations are set in your `cloudbuild.yaml` or deployment command:

1.  **Memory**: **4Gi** (Critical for ZAP stability).
2.  **Concurrency**: **`--max-instances 1`** (Critical for shared state/progress tracking).
3.  **Environment Variables**:
    *   `PYTHONUNBUFFERED=1` (For real-time logs).
    *   `ZAP_URL=http://127.0.0.1:8090` (Internal).
    *   `AI_PROVIDER=google` (For Gemini).
4.  **Frontend Build**:
    *   Ensure API calls fall back to relative paths (`/api/...`) instead of `localhost`.

### Deployment Command
```bash
gcloud builds submit --config cloudbuild.yaml .
```
This builds the unified Docker image and deploys both the **Service** (UI) and the **Job** (Ephemeral).

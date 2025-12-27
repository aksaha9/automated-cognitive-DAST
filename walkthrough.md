# Walkthrough: Automated Cognitive DAST

## 1. Public Live Demo
We have deployed a live instance of the application on Google Cloud Run. You can access it here:
👉 **[https://automated-cognitive-dast-service-510071073932.us-central1.run.app/](https://automated-cognitive-dast-service-510071073932.us-central1.run.app/)**

## 2. AI Assisted Scan Verification

**Verification Sequence (Manual):**

1.  **Enable AI Mode**: Toggled the "AI Assisted" slider on the dashboard.
2.  **Input Requirement**: Entered the natural language prompt: *"I want to check for data leaks against the target https://example.com"*.
3.  **Analyze Intent**: Clicked the "Analyze Intent" button.
    *   **Backend Action**: The system triggered an MCP call to the LLM (Gemini).
    *   **Result**: The LLM interpreted the intent and automatically selected relevant ZAP scan policies (e.g., Information Disclosure, Sensitive Data Exposure).
4.  **Execute Scan**: Confirmed the selection and started the scan.
    *   **Outcome**: The scan ran successfully, focusing only on the interpreted risks.

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
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_SERVICE_ACCOUNT=your-service-account@your-project.iam.gserviceaccount.com,_GCS_REPORT_BUCKET=your-reports-bucket \
  .
```
This builds the unified Docker image and deploys both the **Service** (UI) and the **Job** (Ephemeral).

## 5. Metrics Fix & Verification

### Issue Identified
Ephemeral scans were reporting a vulnerability count of "1" for all vulnerability types, treating ZAP alert groups as single findings.

### Fix Verification
We updated the parser to respect the `count` field in ZAP alerts and verified it in both environments.

#### Local Verification
Built the `dast-ephemeral` image from scratch and ran it detached from the main stack:
```bash
docker build --no-cache -f Dockerfile.ephemeral -t dast-ephemeral .
docker run --rm -e GEMINI_API_KEY=$GEMINI_API_KEY dast-ephemeral --target https://example.com --vuln "I want to check for weaknesses in the target for data harvesting attacks" --format sarif
```

#### Cloud Verification
Deployed the fix and executed the Cloud Run Job:
```bash
gcloud builds submit --config cloudbuild.yaml --substitutions=_SERVICE_ACCOUNT=<REDACTED>,_GCS_REPORT_BUCKET=<REDACTED> .
gcloud run jobs execute zap-mcp-server-job --region us-central1 --args="--target=https://example.com" --args="--vuln=I want to check if this target is susceptible to data harvesting attacks" --args="--format=sarif" --args="--output=report.json"

# Read Logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=zap-mcp-server-job AND labels.\"run.googleapis.com/execution_name\"=<EXECUTION_NAME>" --limit 100 --format="value(textPayload)"
```
**Result**: The cloud logs verified correct aggregated counts (Total: 35).

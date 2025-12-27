# Automated Cognitive DAST

> **Next-Generation Dynamic Application Security Testing powered by Generative AI.**

This platform bridges the gap between traditional security scanning tools (OWASP ZAP) and modern Large Language Models (Google Gemini). It enables security engineers to express testing requirements in natural language, which the system translates into precise, optimized, and compliant security scans.

---

## 🚀 Key Features

*   **🧠 Cognitive Intelligence**: Translates natural language prompts (e.g., *"Check for IDOR in the payment flow"*) into specific ZAP Active Scan policies.
*   **🛡️ Enterprise Ready**:
    *   **Secure**: Zero hardcoded secrets using Google Secret Manager.
    *   **Compliant**: Auto-uploads timestamped SARIF/JSON reports to Google Cloud Storage (GCS).
    *   **Scalable**: Built on Google Cloud Run with a unified container architecture.
*   **⚡ Dual Operations Mode**:
    *   **Interactive (GUI)**: Real-time analysis and feedback for engineers.
    *   **Ephemeral (Headless)**: "Fire-and-forget" jobs optimized for CI/CD pipelines.

---

## 🏗️ Architecture

The system uses a unified container design to deliver both the UI and the Ephemeral logic.

*   **📖 [Deep Dive Architecture](docs/ARCHITECTURE.md)**: Detailed breakdown of components, topology diagrams (Mermaid), and execution flows.
*   **🛠️ [Design Resources](Design/)**: Editable Source PUML files for system topology and sequence diagrams.

---

## 🚦 Getting Started

### 1. Local Development
Run the full stack (Frontend, Backend, ZAP) locally using Docker Compose.

**Prerequisites**: Docker Desktop, Google Gemini API Key.

1.  Clone the repository:
    ```bash
    git clone https://github.com/aksaha9/automated-cognitive-DAST.git
    cd automated-cognitive-DAST
    ```
2.  Set your API Key:
    ```bash
    export GEMINI_API_KEY="your_api_key_here"
    ```
3.  Launch:
    ```bash
    docker compose up --build
    ```
4.  Access the UI at `http://localhost:5173`.

### 2. Cloud Deployment (Secure)
Deploy to Google Cloud Run using Cloud Build. This method ensures **no sensitive data is hardcoded** in your repository.

**Prerequisites**: 
*   Google Cloud Project with Cloud Run & Secret Manager APIs enabled.
*   A Service Account with necessary permissions.
*   A GCS Bucket for report storage.

**Deployment Command**:
```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_SERVICE_ACCOUNT=your-sa@project.iam.gserviceaccount.com,_GCS_REPORT_BUCKET=your-report-bucket \
  .
```

---

## 🧪 Verification & Walkthrough

We verify functionality using both manual UI tests and automated CLI jobs.

*   **📄 [Verification Walkthrough](walkthrough.md)**: See detailed steps on how we verified the AI capabilities and Ephemeral job execution.

### Verification Commands

#### 1. Local Ephemeral Verification
Build the ephemeral image from scratch and run a containerized scan:
```bash
# Build
docker build --no-cache -f Dockerfile.ephemeral -t dast-ephemeral .

# Run (requires GEMINI_API_KEY env var)
docker run --rm -e GEMINI_API_KEY=$GEMINI_API_KEY dast-ephemeral \
  --target https://example.com \
  --vuln "I want to check for weaknesses in the target for data harvesting attacks" \
  --format sarif
```

#### 2. Cloud Ephemeral Verification
Deploy the fix to Google Cloud and execute the Cloud Run Job:
```bash
# Deploy (Substitutions required)
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_SERVICE_ACCOUNT=<YOUR_SERVICE_ACCOUNT_EMAIL>,_GCS_REPORT_BUCKET=<YOUR_GCS_BUCKET_NAME> .

# Execute Job
gcloud run jobs execute zap-mcp-server-job \
  --region us-central1 \
  --args="--target=https://example.com" \
  --args="--vuln=I want to check if this target is susceptible to data harvesting attacks" \
  --args="--format=sarif" \
  --args="--output=report.json"

# Read Logs (Get Scan Summary)
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=zap-mcp-server-job AND labels.\"run.googleapis.com/execution_name\"=<EXECUTION_NAME>" --limit 100 --format="value(textPayload)"
```

---

## 📜 License
MIT License

# Automated Cognitive DAST

**Author**: Ashish Kumar Saha  
*API Security Engineering Lead*

## Introduction

### Why?
Security testing is often complex, requiring deep expertise to configure tools like OWASP ZAP correctly. "One-size-fits-all" scans take too long and miss context.

### What?
**Automated Cognitive DAST** is a next-generation security scanner that combines the power of the **OWASP ZAP** engine with the intelligence of **Google Gemini 1.5 Pro**. It uses Generative AI to translate natural language intentions (e.g., "Check for data leaks") into precise, optimized security scans.

### How?
The system runs in a unified container on Google Cloud Run. It accepts high-level prompts, consults an LLM to design a scan policy, and then orchestrates ZAP to execute that policy against the target.

---

## 🚀 Live Demo
Access the public instance running on Google Cloud Run:
👉 **[Public Cloud Instance](https://automated-cognitive-dast-service-510071073932.us-central1.run.app/)**

---

## Architecture & Topology

The system uses a unified container architecture to deliver low-latency performance in a serverless environment.

![System Topology](designs/topology.svg)

For a detailed breakdown of the internal components and execution flow, see:
📄 **[Architecture Documentation](docs/ARCHITECTURE.md)**

---

## Ephemeral Mode

In addition to the UI, this tool supports **Ephemeral Headless Scans**. These are "fire-and-forget" jobs perfect for CI/CD pipelines.

![Ephemeral Topology](designs/ephemeral_topology.svg)

Learn how to trigger automated jobs via CLI or Cloud Scheduler:
📄 **[Ephemeral Mode Documentation](docs/EPHEMERAL_MODE.md)**

---

## Usage Instructions

### 1. Web App & API Scanning (UI)
The primary way to use the tool is via the Dashboard.

1.  **Launch**: Open the [Live Demo](https://automated-cognitive-dast-service-510071073932.us-central1.run.app/) or your local instance.
2.  **Target**: Enter the URL to scan (e.g., `https://example.com`).
3.  **Mode Selection**:
    *   **Standard**: Choose "Web App" or "API".
    *   **AI Assisted**: Select the "AI Assisted" tab.
4.  **Prompt (AI Mode)**: Describe your goal.
    *   *Example*: "Can this target site be exploited for getting unauthorised data out and leaked?"
5.  **Scan**: Click "Start Scan". The system will analyze your request, configure ZAP, and stream progress.
6.  **Results**: View findings in the interactive report or export to JSON/SARIF.

### 2. Local Deployment
To run the full stack locally:

```bash
# Clone the repo
git clone https://github.com/aksaha9/automated-cognitive-DAST.git

# Start with Docker Compose
docker compose up --build
```
Access at `http://localhost:5173`.

---

## License
MIT License

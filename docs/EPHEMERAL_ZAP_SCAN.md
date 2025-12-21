# Ephemeral Headless MCP ZAP Scan

This document describes the design, flow, and usage of the **Ephemeral Headless Container Native MCP ZAP Scan** functionality included in this repository.

## Design

This solution provides a lightweight, ephemeral way to run OWASP ZAP scans powered by AI. It runs as a single Docker container that:

1.  **AI Orchestration**: Uses Google Gemini (via `fastmcp`) to interpret natural language vulnerability descriptions (e.g., "Check for SQL injection in the login form") and translates them into a precise ZAP active scan configuration.
2.  **Native Execution**: Runs the ZAP scan natively inside the container using `zap-full-scan.py`, eliminating the complexity of Docker-in-Docker.
3.  **Ephemeral Nature**: The container is designed to run a single scan and exit ("One-Shot Mode") or run as a persistent MCP server.
4.  **Flexible Reporting**: Supports exporting reports in HTML, JSON, Markdown, XML, and SARIF formats, with automatic logging to a mounted volume.

## Flow

1.  **Input**: Users provide a target URL and a natural language description of vulnerabilities via CLI arguments.
2.  **Configuration Generation**:
    *   The entrypoint script initializes the Python-based MCP server.
    *   The server sends the vulnerability description to the Gemini API.
    *   Gemini selects the specific ZAP active scan rules (IDs and thresholds) that match the description.
3.  **Execution**:
    *   The generated configuration is saved to disk.
    *   The script executes `zap-full-scan.py` with the generated config.
4.  **Output**:
    *   The full report is generated in the requested format (default: HTML).
    *   The report and execution logs are copied to the mounted `/reports` directory on the host.
    *   The container exits.

## Usage

### Prerequisites

1.  **Docker**: Ensure Docker is installed and running.
2.  **Configuration**:
    *   Create a `config` directory in your project root.
    *   Copy `config/llm_config.json.example` to `config/llm_config.json`.
    *   Edit `config/llm_config.json` and add your Google Gemini API key.

    ```json
    {
        "api_key": "YOUR_GEMINI_API_KEY",
        "model": "gemini-3-pro-preview",
        "base_url": "https://generativelanguage.googleapis.com"
    }
    ```

### Building the Image

Build the Docker image using the provided ephemeral Dockerfile:

```bash
docker build -t zap-mcp-server -f Dockerfile.ephemeral .
```

### Running a Scan

Run the container using `docker run`. You must mount the `config` and `reports` directories.

#### Arguments
*   `--target`: The URL to scan.
*   `--vuln`: Natural language description of what to test for.
*   `--format`: Report format (`html`, `json`, `md`, `xml`, `sarif`). Default is `html`.

#### Examples

**1. Basic HTML Scan (Default)**
Scans for SQL injection vulnerabilities and saves an HTML report.

```bash
docker run --rm \
  -v "$(pwd)/config":/config:ro \
  -v "$(pwd)/reports":/reports:rw \
  zap-mcp-server \
  --target https://example.com \
  --vuln "Check for SQL injection"
```

**2. JSON Report**
Scans for XSS and saves a JSON report for programmatic processing.

```bash
docker run --rm \
  -v "$(pwd)/config":/config:ro \
  -v "$(pwd)/reports":/reports:rw \
  zap-mcp-server \
  --target https://example.com \
  --vuln "Check for Cross Site Scripting (XSS)" \
  --format json
```

**3. SARIF Report**
Generates a report compatible with GitHub Security Scanning (output as JSON).

```bash
docker run --rm \
  -v "$(pwd)/config":/config:ro \
  -v "$(pwd)/reports":/reports:rw \
  zap-mcp-server \
  --target https://example.com \
  --vuln "Check for all critical vulnerabilities" \
  --format sarif
```

### Outputs

After the scan completes, check your local `reports/` directory:
*   `zap_report.<format>`: The full scan report.
*   `scan_stdout.log`: Full execution logs including the AI-generated configuration and ZAP console output.

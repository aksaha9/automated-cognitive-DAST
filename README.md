# Automated Cognitive DAST

**Author**: Ashish Kumar Saha, API Security Engineering Lead

A modern, containerized Dynamic Application Security Testing (DAST) solution leveraging the OWASP ZAP engine. This system provides a React-based dashboard for orchestrating scans, monitoring progress in real-time, and exporting results in industry-standard formats.

## Features

-   **Dashboard**: A responsive React UI for managing scans.
-   **Multi-Mode Scanning**:
    -   **Web App Scan**: Traditional spidering and scanning of web applications.
    -   **API Scan**: Targeted scanning of REST APIs (internal or external).
-   **Reporting**: Export vulnerabilities in JSON, SARIF (GitHub Security), or OCSF formats.
-   **Containerized**: Fully Docker-based architecture for easy deployment.
-   **Cognitive Logic**: Python-based orchestration layer that handles scan logic, state management, and error recovery.

## Architecture

The system consists of three main containers:
1.  **Frontend**: React + Vite (Port 5173)
2.  **Backend**: FastAPI + Python (Port 8000)
3.  **Engine**: OWASP ZAP (Port 8090/8080)

## Getting Started

### Prerequisites
-   Docker & Docker Compose

### Quick Start

1.  Clone the repository:
    ```bash
    git clone https://github.com/aksaha9/automated-cognitive-DAST.git
    cd automated-cognitive-DAST
    ```

2.  Start the services:
    ```bash
    docker compose up --build -d
    ```

3.  Access the Dashboard:
    Open [http://localhost:5173](http://localhost:5173) in your browser.

## Documentation

For a detailed visual guide on how to run web app and API scans, please refer to the [Walkthrough Document](walkthrough.md).

## Usage

### Running a Web App Scan
1.  Navigate to "New Scan".
2.  Enter the target URL (e.g., `https://example.com`).
3.  Select "Web App Scan".
4.  Click "Launch".

### Running an API Scan (Internal/Local)
To scan a service running within the same Docker network (like the provided `vulnerable-api` stub):
1.  Use the internal service name: `http://vulnerable-api:8000`.
2.  Select "API Scan".

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

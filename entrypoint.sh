#!/bin/bash
set -e
set -o pipefail

# Default values
TARGET_URL=""
VULN_DESC=""
REPORT_FORMAT="html"
REPORTS_DIR="/reports"
export REPORTS_DIR
CONFIG_DIR="/config"

# Help message
show_help() {
    echo "Usage: docker run zap-mcp-wrapper \\"
    echo "  -v /path/to/llm_config:/config \\"
    echo "  -v /path/to/reports:/reports \\"
    echo "  zap-mcp-wrapper \\"
    echo "  --target https://example.com \\"
    echo "  --vuln \"Check for SQL injection...\" \\"
    echo "  --format html|json|md|xml|sarif"
    echo ""
    echo "Required:"
    echo "  --target URL     Target website to scan"
    echo "  --vuln DESC      Natural language description of vulnerabilities to check"
    echo "  --format FMT     Report format (default: html). Options: html, json, md, xml, sarif"
    echo ""
    echo "Mounts:"
    echo "  /config          Directory containing llm_config.json (mounted from host)"
    echo "  /reports         Directory where reports and logs will be saved (mounted from host)"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET_URL="$2"
            shift 2
            ;;
        --vuln)
            VULN_DESC="$2"
            shift 2
            ;;
        --format|-f)
            REPORT_FORMAT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

# Validate required args
if [[ -z "$TARGET_URL" || -z "$VULN_DESC" ]]; then
    echo "Error: --target and --vuln are required."
    show_help
fi

# Ensure config and reports dirs exist
mkdir -p "$REPORTS_DIR"

# Copy llm_config.json into working dir if it exists
if [[ -f "$CONFIG_DIR/llm_config.json" ]]; then
    cp "$CONFIG_DIR/llm_config.json" /home/zap/llm_config.json
elif [[ -n "$GEMINI_API_KEY" ]]; then
    echo "Info: llm_config.json not found, using GEMINI_API_KEY from environment."
else
    echo "Error: llm_config.json not found in mounted /config directory AND GEMINI_API_KEY not set!"
    exit 1
fi

# Override perform_dast_scan to run once and exit
export ONE_SHOT_MODE=1
export TARGET_URL_ONE_SHOT="$TARGET_URL"
export VULN_DESC_ONE_SHOT="$VULN_DESC"
export REPORTS_DIR_ONE_SHOT="$REPORTS_DIR"
export REPORT_FORMAT_ONE_SHOT="$REPORT_FORMAT"

# Run the MCP server in one-shot mode
cd /home/zap
python zap_mcp_server.py | tee "$REPORTS_DIR/scan_stdout.log"
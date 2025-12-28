# Examples

## Example Ephemeral Job Scans

### 1. Data Harvesting Check (Cloud Run)
Example of an ephemeral job scan command with a natural language prompt *"I want to check if this target is susceptible to data harvesting attacks"* on the target `https://example.com` with output and retrieval of results.

**1. Command to execute the ephemeral job scan**
```bash
$ gcloud run jobs execute zap-mcp-server-job --region us-central1 --args="--target=https://example.com" --args="--vuln=I want to check if this target is susceptible to data harvesting attacks" --args="--format=sarif" --args="--output=report.json"
✓ Creating execution... Done.                                                                                                                                      
  ✓ Provisioning resources... Provisioned imported containers.                                                                                                     
Done.                                                                                                                                                              
Execution [zap-mcp-server-job-*****] has successfully started running.

View details about this execution by running:
gcloud run jobs executions describe zap-mcp-server-job-*****

Or visit https://console.cloud.google.com/run/jobs/executions/details/us-central1/zap-mcp-server-job-*****/tasks?project=my-project-id
```

**2. Command to fetch the job details along with status of job using the job id from previous command**
```bash
$ gcloud run jobs executions describe zap-mcp-server-job-*****
… Execution zap-mcp-server-job-***** in region us-central1
1 task currently running
0 tasks completed successfully
 
Log URI: https://console.cloud.google.com/logs/viewer?project=my-project-id&advancedFilter=resource.type%3D%22cloud_run_job%22...
 
Image:              gcr.io/my-project-id/zap-mcp-server@sha256:*****
Tasks:              1
Args:               --target=https://example.com --vuln=I want to check if this target is susceptible to data harvesting attacks --format=sarif --output=report.json
Memory:             4Gi
CPU:                2
Task Timeout:       30m
Max Retries:        0
Parallelism:        1
Service account:    my-service-account@my-project-id.iam.gserviceaccount.com
Env vars:
  GCS_REPORT_BUCKET my-reports-bucket
  REPORTS_DIR       /home/zap/reports
Secrets:
  /config           llm_config:latest
… Waiting for execution to complete.
```

**3. Command to fetch the results summary once the scan is completed (status obtained from the previous command)**
```bash
$ gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=zap-mcp-server-job AND labels.\"run.googleapis.com/execution_name\"=zap-mcp-server-job-*****" --limit 100 --format="value(textPayload)"

Container called exit(0).
  - 2 | Informational (Low) | Re-examine Cache-control Directives
  - 2 | Low (Medium) | X-Content-Type-Options Header Missing
  - 2 | Low (Medium) | HTTPS Content Available via HTTP
  - 2 | Medium (Medium) | Missing Anti-clickjacking Header
  - 4 | Informational (Medium) | Storable and Cacheable Content
  - 4 | Low (High) | Strict-Transport-Security Header Not Set
  - 4 | Low (Medium) | Permissions Policy Header Not Set
  - 4 | Medium (High) | Content Security Policy (CSP) Header Not Set
  - 5 | Informational (Medium) | Retrieved from Cache
  - 6 | Low (Medium) | Insufficient Site Isolation Against Spectre Vulnerability
Finding Breakdown (Count | Risk | Name):
  Info: 11
  Low: 18
  Medium: 6
  High: 0
Severity Breakdown:
Total Vulnerabilities: 35
Scan Statistics:
GCS Report URI: gs://my-reports-bucket/scan_reports/scan_report_sarif_20251228_0908_UTC.json
Full report saved to (Local): ./reports/scan_report_sarif_20251228_0908_UTC.json
10202   FAIL    Absence of Anti-CSRF Tokens
40042   FAIL    SQL Injection (RDBMS-independent advanced)
40024   FAIL    SQL Injection - SQLite
40022   FAIL    SQL Injection - PostgreSQL
40021   FAIL    SQL Injection - Oracle
40020   FAIL    SQL Injection - Hypersonic SQL
40019   FAIL    SQL Injection - MySQL
40018   FAIL    SQL Injection
Generated config:
Format: sarif
Focus: I want to check if this target is susceptible to data harvesting attacks
DAST scan completed for https://example.com
=== SCAN RESULT ===
Report uploaded to: gs://my-reports-bucket/scan_reports/scan_report_sarif_20251228_0908_UTC.json
Starting one-shot DAST scan (Format: sarif)...
Info: Using mounted configuration from /config.
```

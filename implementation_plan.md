# Implementation Plan - Automated Cognitive DAST (Phase 2)

## Goal Description
Enhance the existing MVP to have a "Professional & High-End" UI and support standardized security reporting formats (SARIF and OCSF).

## User Review Required
> [!NOTE]
> **Artifacts Location**: The artifacts (`task.md`, `implementation_plan.md`, `walkthrough.md`) are currently stored in a hidden directory: `~/.gemini/antigravity/brain/...`. I can copy them to your project folder if you wish.

## Proposed Changes

### UI Redesign (Frontend)
Refactor the generic Tailwind UI to a premium, polished design.
#### [MODIFY] [frontend/src/index.css](file:///Users/aksaha21/Dropbox/My Mac (Ashishs-MBP)/Documents/mycode/Ashish/Hackathon/December2025/automated-cognitive-DAST/frontend/src/index.css)
- Add modern fonts (Inter/Outfit).
- Define a sophisticated color palette (slate/indigo/rose).
- Add generic utility classes for "glassmorphism" or card styles.

#### [MODIFY] [frontend/src/App.jsx](file:///Users/aksaha21/Dropbox/My Mac (Ashishs-MBP)/Documents/mycode/Ashish/Hackathon/December2025/automated-cognitive-DAST/frontend/src/App.jsx)
- Update layout shell (sidebar or top nav) with better spacing and shadows.

#### [MODIFY] [frontend/src/components/Dashboard.jsx](file:///Users/aksaha21/Dropbox/My Mac (Ashishs-MBP)/Documents/mycode/Ashish/Hackathon/December2025/automated-cognitive-DAST/frontend/src/components/Dashboard.jsx)
- Replace standard table with a styled data grid.
- Use animated status pills.

### Reporting Formats (Backend)
Add support for exporting scan results in different standards.
#### [MODIFY] [backend/app/models.py](file:///Users/aksaha21/Dropbox/My Mac (Ashishs-MBP)/Documents/mycode/Ashish/Hackathon/December2025/automated-cognitive-DAST/backend/app/models.py)
- Add `ReportFormat` Enum (JSON, SARIF, OCSF).

#### [MODIFY] [backend/app/api/endpoints.py](file:///Users/aksaha21/Dropbox/My Mac (Ashishs-MBP)/Documents/mycode/Ashish/Hackathon/December2025/automated-cognitive-DAST/backend/app/api/endpoints.py)
- Update `GET /scan/{id}/results`: Accept `?format=` query param.
- Implement transformation logic:
    - **SARIF**: Map ZAP alerts to SARIF `runs`, `results`, and `rules`.
    - **OCSF**: Map ZAP alerts to OCSF `Vulnerability Finding` class.

## Verification Plan

### Automated Tests
- **Backend**: Test the `get_results` endpoint with `format=SARIF` and `format=OCSF` to ensure valid JSON structure.

### Manual Verification
1.  **UI Check**: Verify the application looks "premium" (fonts, spacing, colors).
2.  **Export Test**:
    - Run a scan.
    - On Results page, select "SARIF" and download/view.
    - Validate the output against a SARIF viewer (online or VS Code).
    - Repeat for OCSF.

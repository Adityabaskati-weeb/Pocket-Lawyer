# Pocket Lawyer Roadmap

## Phase 0: Foundation

- Verify repository.
- Add project docs.
- Add Python package scaffold.
- Add test setup.

Exit criteria:

- Repo has a clear README, PRD, roadmap, package metadata, and test layout.
- `python -m pytest` runs.

## Phase 1: Employment Contract Analyzer Core

- Build a deterministic rule-based analyzer.
- Detect high-risk employment clause patterns.
- Produce structured report data.
- Generate negotiation script text.
- Add tests for representative clauses.

Exit criteria:

- Analyzer tests pass.
- Sample contract returns red/yellow/green findings.

## Phase 2: Local API and CLI

- Add a CLI for paste-text/file analysis.
- Add a lightweight local API surface.
- Return JSON report output.

Exit criteria:

- CLI analyzes a sample contract.
- API contract is documented or tested.

## Phase 3: Web Report UI

- Add an upload/paste screen.
- Add traffic-light report view.
- Add clause cards and negotiation script copy area.

Exit criteria:

- User can paste text in the browser and see a report.
- UI uses the same analyzer output as the tests.

## Phase 4: PDF Intake and Persistence

- Add PDF text extraction.
- Store uploaded contracts locally or in a database.
- Add scan history.

Exit criteria:

- Text PDFs can be analyzed.
- User can reopen previous reports.

## Phase 5: Six Contract-Type Demo Expansion

- Add selectable contract types.
- Add rule-backed demo coverage for freelancer/client, rent, NDA, vendor/service, and loan agreements.
- Keep employment as the strongest wedge.
- Add tests for red and green findings across all six types.

Exit criteria:

- User can select any of the six contract types in the browser.
- Analyzer filters rules by selected contract type.
- Tests cover every contract type.

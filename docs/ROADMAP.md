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

## Phase 6: V2 Architecture Foundation

- Introduce application settings and service configuration.
- Replace JSON-only persistence with repository interfaces and database-backed storage.
- Preserve current CLI and report JSON behavior while preparing for V2 modules.

Exit criteria:

- Current functionality still works through the same user-facing flows.
- Internal module boundaries exist for API, storage, intake, and analysis.

## Phase 7: Document Pipeline Hardening

- Add DOCX support.
- Add OCR for scanned PDFs and image uploads.
- Preserve page metadata for extracted text.
- Move heavy document parsing to background jobs when needed.

Exit criteria:

- Image-based or scanned documents can be processed.
- Extracted text retains page-level provenance.

## Phase 8: Clause Segmentation and Evidence Spans

- Segment contracts into clause candidates instead of analyzing only full-document text.
- Track clause offsets, pages, and source spans.
- Render exact supporting evidence in reports.

Exit criteria:

- Every material finding points to a source clause.
- Reports show supporting snippets, not only generic summaries.

## Phase 9: Legal Playbooks and Retrieval

- Convert hardcoded rules into structured playbook entries.
- Add jurisdiction notes and source references.
- Start with metadata and keyword retrieval for clause-family lookup.

Exit criteria:

- Legal knowledge is loaded from structured data rather than only Python constants.
- Findings can cite playbook entries and jurisdiction notes.

## Phase 10: Hybrid Analysis Engine

- Keep deterministic rules as the foundation.
- Add structured LLM assistance for ambiguous clauses and clearer explanations.
- Merge rule findings, retrieved context, and model outputs into one report.

Exit criteria:

- LLM output is schema-validated.
- Rule-only analysis remains available as a fallback path.

## Phase 11: Accounts and Private Vault

- Add user accounts and authenticated history.
- Encrypt saved contracts and extracted text at rest.
- Support contract versions and reminder metadata.

Exit criteria:

- Users can access only their own saved contracts.
- Sensitive contract data is no longer stored in plain local JSON files.

## Phase 12: Lawyer Review Workflow

- Add escalation for high-risk or low-confidence reports.
- Generate pre-brief summaries for lawyers.
- Track lawyer review requests and status.

Exit criteria:

- A risky report can be escalated into a structured review workflow.
- Lawyer handoff does not require manual report rewriting.

## Phase 13: Billing and Entitlements

- Add subscriptions for premium features.
- Add one-time billing for lawyer review workflows.
- Verify access via backend webhooks instead of client-only state.

Exit criteria:

- Entitlements are enforced server-side.
- Payment success is driven by verified backend events.

## Phase 14: Evaluation and Release Hardening

- Add benchmark-driven evaluation sets.
- Add regression tests for extraction, retrieval, and report generation.
- Define latency and cost budgets for the hybrid system.

Exit criteria:

- Releases are blocked on evaluator regressions.
- Cost and latency remain within defined thresholds.

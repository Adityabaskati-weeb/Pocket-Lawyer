# Pocket Lawyer PRD

## Vision

Pocket Lawyer helps people in India understand risky contract clauses before they sign. The first demo version supports common contract types and returns a traffic-light report that explains each important clause in plain language.

Pocket Lawyer provides legal information, not legal advice. High-risk reports should recommend consulting a qualified lawyer.

## MVP Audience

The initial wedge remains a fresher or employee reviewing an Indian employment agreement before joining a company. For demos and funding conversations, the MVP also covers freelancers, tenants, NDA reviewers, vendors, and borrowers with rule-backed first-pass scanning.

## MVP Problem

Employment contracts often contain clauses that users do not fully understand, including non-compete restrictions, broad IP ownership, long notice periods, salary-change rights, bonds, and termination traps. Most users cannot afford a lawyer for a quick review.

## MVP Goal

Let a user choose a contract type, paste or upload contract text, and receive a useful red/yellow/green clause report within one minute.

## MVP Scope

In scope:

- Employment contracts.
- Freelancer/client contracts.
- Rent agreements.
- NDAs.
- Vendor/service agreements.
- Loan agreements.
- Paste-text analysis.
- TXT/PDF upload for readable text documents.
- Rule-backed risk detection.
- Overall risk score.
- Clause-by-clause report.
- Plain-language explanations.
- Suggested replacement wording.
- Negotiation script.
- Legal-information disclaimer.

Out of scope for the first milestone:

- Mobile app.
- Lawyer marketplace.
- Payments.
- User accounts.
- PDF OCR.
- Lawyer-reviewed jurisdiction-specific advice.
- OCR for scanned image-only contracts.

## User Flow

1. User chooses the contract type.
2. User pastes contract text or uploads a readable TXT/PDF file.
3. System detects relevant clauses.
4. System classifies each clause as red, yellow, or green.
5. User sees an overall report.
6. User copies a negotiation message for risky clauses.

## Risk Levels

- Red: dangerous, unusually broad, or user-hostile.
- Yellow: needs attention or negotiation.
- Green: standard or generally fair.

## Initial Clause Categories

Employment:

- IP ownership and side projects.
- Non-compete.
- Non-solicit.
- Notice period.
- Termination.
- Salary changes.
- Bond or training repayment.
- Confidentiality.
- Arbitration and jurisdiction.
- Probation.

Freelancer/client:

- IP transfer before payment.
- Unlimited revisions.
- Vague acceptance and payment control.
- Milestone payment timing.

Rent:

- Security deposit forfeiture.
- Lock-in penalties.
- Landlord entry/privacy.
- Term and notice basics.

NDA:

- Perpetual confidentiality.
- Missing standard exclusions.
- Residual knowledge restrictions.
- One-way vs mutual obligations.

Vendor/service:

- Unlimited liability.
- Payment withholding.
- Scope changes.
- Invoice payment timing.

Loan:

- Blank/security cheque risk.
- Unilateral interest changes.
- Immediate default/acceleration.
- EMI schedule clarity.

## Success Criteria

- Analyzer produces deterministic structured output for all six demo contract types.
- At least 20 representative contract snippets are covered by tests.
- Every report includes disclaimer text.
- Risk score is explainable from matched findings.
- No legal conclusion is presented as guaranteed legal advice.

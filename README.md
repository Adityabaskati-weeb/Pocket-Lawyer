---
title: Pocket Lawyer
colorFrom: green
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Pocket Lawyer

Pocket Lawyer is an India-first legal-tech MVP that helps people understand risky contract clauses before they sign. A user can paste or upload a contract, choose the agreement type, and receive a plain-language red/yellow/green risk report with negotiation wording they can actually use.

The product is designed for people who usually cannot afford a lawyer for every small contract: freshers joining their first job, freelancers signing client agreements, tenants reviewing rent agreements, founders checking NDAs, vendors reading service terms, and borrowers looking at loan documents.

Live demo:

```text
https://prodigyhuh-pocket-lawyer.hf.space
```

Pocket Lawyer provides legal information, not legal advice. High-risk contracts should still be reviewed by a qualified lawyer.

## Why This Matters

Contracts are written in language that benefits the person who drafted them. Most users sign because they are short on time, money, legal access, or confidence. The result is avoidable harm: unfair non-competes, broad IP grabs, security deposit traps, blank cheque risks, unlimited liability, payment delays, and one-sided confidentiality terms.

Pocket Lawyer turns that black box into a first-pass safety layer. It does not replace lawyers. It helps users know when they need one, what to ask for, and which clauses deserve attention before the damage is done.

## What Exists Today

The current MVP already includes:

- A premium browser-based contract scanner.
- Six agreement types: employment, freelancer/client, rent, NDA, vendor/service, and loan.
- Paste-text and TXT/PDF upload intake.
- Rule-backed clause detection with deterministic tests.
- Overall risk score and red/yellow/green breakdown.
- Plain-language explanation for each finding.
- Suggested replacement wording.
- Copyable negotiation message.
- Recent scan history and starter examples.
- CLI, local API, Docker deployment, and Hugging Face demo deployment.

## Funding Vision

Pocket Lawyer can become the legal safety layer for everyday agreements in India. The MVP proves the core behavior: contract in, risk report out, negotiation language ready. Funding helps turn this from a strong demo into a trusted product.

With support, the next version will focus on:

- Better legal intelligence with lawyer-reviewed clause playbooks.
- More contract categories for students, renters, freelancers, consumers, and small businesses.
- Secure user accounts and private contract vaults.
- OCR for scanned PDFs and mobile-first uploads.
- Indian language support for users who do not think in legal English.
- Human lawyer escalation for high-risk contracts.
- Institution and startup partnerships for distribution.

## Future Plans

### 1. Hybrid AI plus Rule Engine

The current analyzer is deterministic and explainable. The next system should combine rules, retrieval, and LLM assistance so Pocket Lawyer can understand more natural contract language while still showing exactly which clause triggered each warning.

Planned upgrades:

- Clause extraction with exact source highlighting.
- Lawyer-reviewed risk playbooks for each contract category.
- Safer generated negotiation language with guardrails.
- Confidence scoring and "needs lawyer review" escalation.
- Evaluation datasets for Indian contract patterns.

### 2. India-First Contract Coverage

The MVP supports six common agreement types. Future coverage should expand into the agreements people actually face every month.

Planned categories:

- Internship and fresher offer letters.
- Founder agreements and ESOP letters.
- Startup vendor and SaaS contracts.
- Consumer loan and BNPL terms.
- Rent agreements by state-specific patterns.
- Influencer, creator, and agency contracts.
- College, hostel, coaching, and training agreements.

### 3. Uploads That Work in the Real World

Many users do not have clean text PDFs. They have WhatsApp files, scans, photos, screenshots, and messy documents.

Planned intake:

- OCR for scanned PDFs and phone photos.
- DOCX support.
- Mobile camera upload flow.
- Clause-by-clause document highlighting.
- Exportable PDF report for sharing with family, founders, employers, or lawyers.

### 4. Private Contract Vault

Contracts are sensitive. A real product needs privacy, trust, and continuity.

Planned vault:

- User accounts.
- Encrypted saved contracts.
- Version comparison between draft and revised contracts.
- Deadline reminders for notice periods, renewals, lock-ins, and payment dates.
- Personal risk dashboard across all contracts.

### 5. Lawyer Escalation Network

Pocket Lawyer should not pretend to be a lawyer. The right model is human-in-the-loop: software handles fast first-pass review, and qualified lawyers handle important decisions.

Planned marketplace:

- "Ask a lawyer" escalation for high-risk reports.
- Fixed-price review packages.
- Lawyer dashboard with the AI-generated risk summary.
- Region and contract-type matching.
- Clear separation between legal information and legal advice.

### 6. Distribution and Business Model

The strongest wedge is trust at the moment before signing. Pocket Lawyer can distribute through communities where contracts are frequent and legal access is low.

Potential channels:

- Colleges and placement cells for offer-letter review.
- Freelancer communities and creator agencies.
- Coworking spaces and startup incubators.
- Tenant/renter communities.
- Fintech and loan marketplaces.
- Small business platforms.

Potential revenue:

- Freemium scans for individuals.
- Paid deep reviews and lawyer escalation.
- B2B dashboards for colleges, coworking spaces, and startup programs.
- API access for platforms that want contract-risk checks inside their workflow.

## Build Roadmap

1. Foundation and product docs.
2. Employment contract analyzer core.
3. Local CLI/API analysis surface.
4. Web report UI.
5. PDF intake and persistence.
6. Six contract-type demo expansion.
7. OCR, accounts, and secure contract vault.
8. Hybrid AI/legal-rule engine.
9. Lawyer escalation and partner distribution.

See [docs/PRD.md](docs/PRD.md) and [docs/ROADMAP.md](docs/ROADMAP.md) for the product scope and implementation plan.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

## MVP Scope

The first useful version supports six demo contract types:

- employment contracts
- freelancer/client contracts
- rent agreements
- NDAs
- vendor/service agreements
- loan agreements

A user can paste contract text or upload TXT/PDF and receive:

- overall risk score
- red/yellow/green clause findings
- plain-language explanations
- suggested replacement wording
- negotiation script
- legal-information disclaimer

Scans are saved locally to `data/reports.json` when using the local web app.

## CLI Usage

Analyze direct text:

```powershell
python -m pocket_lawyer --contract-type employment --text "The employee agrees to a non-compete for 24 months after employment."
```

Analyze another contract type:

```powershell
python -m pocket_lawyer --contract-type rent --text "The landlord may retain the security deposit at sole discretion."
```

Analyze a text file:

```powershell
python -m pocket_lawyer --file .\tests\fixtures\sample_green_contract.txt
```

## Local API

Run the local web app and JSON API:

```powershell
$env:PYTHONPATH="src"
python -m pocket_lawyer.api --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

PDF uploads require `pypdf`, which is installed by the project dependency setup:

```powershell
python -m pip install -e .
```

Analyze text:

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8765/analyze `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"contract_type":"loan","text":"The borrower shall provide a blank cheque as security."}'
```

---
title: Pocket Lawyer
colorFrom: green
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Pocket Lawyer

Pocket Lawyer is an MVP contract scanner for common Indian agreements. It helps users spot risky clauses before signing by producing a red/yellow/green report with plain-language explanations and negotiation suggestions.

This product provides legal information, not legal advice. High-risk contracts should be reviewed by a qualified lawyer.

## Current Build Plan

We are building in gated phases:

1. Foundation and product docs.
2. Employment contract analyzer core.
3. Local CLI/API analysis surface.
4. Web report UI.
5. PDF intake and persistence.
6. Six contract-type demo expansion.

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

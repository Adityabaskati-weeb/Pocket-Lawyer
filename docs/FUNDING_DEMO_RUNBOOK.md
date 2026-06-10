# Pocket Lawyer Funding Demo Runbook

## Demo Goal

Show that Pocket Lawyer turns risky contract language into negotiation-ready guidance for Indian users.

The main demo should use the local hybrid build with Ollama enabled. The Hugging Face Space is the public rule-based demo and backup proof that the product is deployed.

## Audience

Mixed audience:

- non-technical funders who need to understand user pain and market value
- technical evaluators who will ask how the system avoids being a black-box legal chatbot

## Positioning

Pocket Lawyer is a contract safety layer for everyday Indian agreements. It uses deterministic legal-risk rules for explainability, playbooks for plain-language guidance, and an optional structured LLM pass for wording variation and ambiguity.

Hosted LLM is intentionally not enabled in the public Hugging Face demo yet because the prototype is controlling API and GPU cost. The local demo shows the latest hybrid rule plus LLM build using Ollama.

## Local Setup

Run Ollama and pull the local model:

```powershell
ollama pull qwen3:1.7b
ollama run qwen3:1.7b "Reply with READY."
```

Start Pocket Lawyer locally:

```powershell
cd "C:\Users\baska\OneDrive\Documents\New project\Pocket-Lawyer"
$env:PYTHONPATH="src"
$env:POCKET_LAWYER_ENABLE_LLM="1"
$env:POCKET_LAWYER_LLM_PROVIDER="ollama"
$env:POCKET_LAWYER_LLM_MODEL="qwen3:1.7b"
$env:POCKET_LAWYER_LLM_API_BASE="http://127.0.0.1:11434/api"
$env:POCKET_LAWYER_LLM_TIMEOUT_SECONDS="90"
python -u -m pocket_lawyer.api --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

Health check from another PowerShell window:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8765/health
```

## Main Demo Flow

1. Open the Hugging Face Space for 30 seconds to show there is a public prototype.
2. Switch to the local build for the strongest AI-assisted demo.
3. Paste the employment mini contract below.
4. Show the report: overall risk, clause cards, evidence snippets, and negotiation script.
5. Point out `rule+llm` when using the API output or developer view.
6. Run the six-contract montage samples quickly to prove breadth.
7. Explain photo upload/OCR as a prototype attempt, not a guaranteed main feature.

## Main Employment Mini Contract

```text
1. The employee agrees that all intellectual property created outside work hours, including personal projects and open-source work, belongs to the employer.

2. The employee agrees to a non-compete for 24 months after employment and shall not work with any company in the same or similar industry.

3. The employer may revise or reduce compensation at its sole discretion by giving notice.

4. Either party may terminate employment by giving 30 days written notice.

5. Confidentiality applies to non-public company information and excludes public information and independently developed knowledge.
```

What to show:

- red findings for broad IP ownership, post-employment non-compete, and salary reduction
- negotiation script that a user can send before signing

Core talking point:

```text
This is not just detecting risk. It tells the user what to ask for before signing.
```

## Six-Type Montage Samples

Employment:

```text
The employee agrees to a non-compete for 24 months after employment.
```

Loan:

```text
The borrower shall provide a blank cheque as security and the lender may deposit it upon default.
```

Rent:

```text
The landlord may retain the full security deposit at sole discretion for any alleged damage.
```

Freelancer:

```text
The freelancer assigns all rights and intellectual property to the client immediately before payment.
```

NDA:

```text
All information shared by the company is confidential forever with no exceptions.
```

Vendor/service:

```text
The vendor has unlimited liability for all losses including indirect and consequential losses.
```

## API Proof Command

Use this if a technical evaluator asks whether the LLM actually ran:

```powershell
$body = @{
  contract_type = "employment"
  text = "The employee agrees to a non-compete for 24 months after employment."
} | ConvertTo-Json -Compress

$data = Invoke-RestMethod `
  -Uri http://127.0.0.1:8765/analyze `
  -Method Post `
  -ContentType "application/json" `
  -Body $body `
  -TimeoutSec 120

$data.llm_status
$data.llm_provider
$data.llm_model
$data.findings | ConvertTo-Json -Depth 8
```

Expected proof:

- `llm_status` is `completed`
- `llm_provider` is `ollama`
- `llm_model` is `qwen3:1.7b`
- at least one finding has `analysis_method` as `rule+llm`

## Optional Technical Proof

Show the hybrid design:

```text
Rules catch known legal-risk patterns. Playbooks explain why they matter and suggest negotiation language. The LLM is a second-pass reviewer for wording variation and ambiguity, not the source of truth.
```

Use this indirect IP ownership sample if you want to show why LLM support matters:

```text
Any work product, inventions, tools, scripts, or reusable components created during the relationship, whether created at home, outside office hours, or without company equipment, will be assigned to the company.
```

Verified local Ollama behavior:

- deterministic rule findings: none
- `llm_status`: `completed`
- `analysis_status`: `review`
- `llm_assessments`: red IP ownership concern with `0.8` confidence

Position it as:

```text
This is the type of wording variation the LLM review layer is designed to improve.
```

Do not claim the LLM catches every missed legal issue. Also do not present this as a normal rule card in the UI unless the UI has been updated to render LLM-only assessments; use API output for this technical proof.

## Photo Upload / OCR Prototype Attempt

Current honest status:

- text paste works
- TXT, Markdown, and readable PDF upload work in the base install
- Docling-backed DOCX/image/OCR paths exist as optional code paths
- mobile camera/photo upload is not the main guaranteed demo path yet

Demo rule:

- Try one clean screenshot/image of typed contract text before the pitch.
- Show it only if the local OCR path works reliably.
- If it fails, say photo/scanned-contract upload is the next intake layer already planned in the architecture.

## Fallback Plan

If local LLM is slow or fails:

1. Stop claiming live LLM is active.
2. Run the rule-based local demo.
3. Show the saved API output proving `llm_status: completed` from prior verification.
4. Use the Hugging Face Space as the public backup.

If the local server fails:

1. Use the Hugging Face Space.
2. Show screenshots or recorded video of the local `rule+llm` result.
3. Keep the pitch focused on the product workflow and roadmap.

## One-Minute Architecture Explanation

```text
Pocket Lawyer is not a generic legal chatbot. It starts with deterministic rules, so known risky clauses are explainable and testable. Then it retrieves structured playbook guidance for plain-language explanation and negotiation wording. The optional LLM layer reviews selected clauses in a strict JSON schema and can add reasoning or escalate ambiguous clauses to lawyer review. This keeps the system evidence-first instead of letting an LLM freely invent legal advice.
```

## What Is Built

- six agreement types
- rule-backed risk detection
- red/yellow/green report
- negotiation script
- local API and CLI
- web scanner UI
- local persistence and scan history
- clause segmentation and evidence spans
- playbook retrieval
- optional Ollama/OpenAI LLM review
- SQLite/object-artifact persistence foundation

## What Is Roadmap

- user accounts
- private encrypted contract vault
- production hosted LLM strategy
- background OCR/document-processing queue
- lawyer escalation workflow
- billing and entitlements
- lawyer-reviewed legal playbook quality checks
- mobile-first photo upload polish
- evaluation pipeline and release gates

## Closing Line

```text
Pocket Lawyer gives users a first-pass safety layer before signing. It does not replace lawyers; it helps users know when they need one and what to ask for.
```

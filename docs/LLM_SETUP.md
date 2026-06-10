# LLM Setup

Pocket Lawyer now supports an optional LLM-assisted clause review pass.

Important behavior:

- It is disabled by default.
- The deterministic rule engine still owns the main risk score.
- The LLM runs only on selected clause candidates, not the full contract at once.
- The LLM output is expected to follow a strict JSON schema.
- High-confidence LLM-only concerns can elevate `analysis_status` to `review`, but they do not silently replace the existing scoring formula.

## Recommended Use

Use the LLM layer for:

- clause wording that differs from the regex patterns
- clearer plain-English reasoning
- ambiguity handling
- conservative lawyer-review escalation

Do not treat it as a replacement for:

- OCR and document extraction quality
- legal playbook maintenance
- deterministic regression tests
- human legal advice

## Recommended Profiles

Use different model targets for different hardware tiers.

### Profile A: Low-End Developer Laptop

Example:

- Ryzen 5 5600H
- Radeon RX 5500M 4GB

Recommendation:

- Do not plan on `qwen3:8b` as the main local model.
- Keep Pocket Lawyer in `rules + retrieval` mode locally.
- If an Ollama provider is added later, target `qwen3:1.7b` first.
- Treat local LLM use on this class of machine as a development convenience only, not as the production backend.

Reason:

- Ollama's current Windows AMD ROCm support list does not include RX 5500-class mobile GPUs, while Vulkan support is an additional compatibility path rather than the main supported route.
- 4GB VRAM is too tight for the stronger local models that make sense for clause-level contract review.

References:

- [Ollama hardware support](https://docs.ollama.com/gpu)

### Profile B: Recommended Prototype Machine

Example:

- 8GB+ effective GPU memory or strong unified memory

Recommendation:

- `qwen3:8b`

Reason:

- This is the best practical free open-weight target for Pocket Lawyer's clause-level analysis.
- Qwen3 is designed for reasoning, agentic workflows, and 128K-context variants in the official Qwen release materials.

References:

- [Qwen3 release blog](https://qwenlm.github.io/blog/qwen3/)
- [Qwen3 8B model card](https://huggingface.co/Qwen/Qwen3-8B)
- [Ollama Qwen3 library page](https://ollama.com/library/qwen3)

### Profile C: Stronger Local or Server Hardware

Example:

- 24GB+ GPU-class deployment or equivalent stronger server resources

Recommendation:

- `mistral-small` / Mistral Small 3.1 24B for stronger open-model quality

Reason:

- The official Mistral model card reports stronger benchmark numbers than smaller open models on several reasoning and coding evaluations.
- It is better suited to longer-context and more demanding second-pass review, but is much heavier to run.

References:

- [Mistral Small 3.1 model card](https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503)

## Website vs Local Development

The LLM profile choice has to be separated into two questions:

1. What can you run on your own machine while building?
2. What should the website use for real users?

For Pocket Lawyer:

- local laptop recommendations are only for development and demos
- the real website should call an LLM from the backend/server
- public users should never be expected to run models on their own devices

So:

- your current laptop profile does not decide the final product architecture
- it only decides what is realistic for your own local testing

## Environment Variables

### OpenAI

```powershell
$env:POCKET_LAWYER_ENABLE_LLM="1"
$env:POCKET_LAWYER_LLM_PROVIDER="openai"
$env:POCKET_LAWYER_LLM_MODEL="gpt-4o-mini"
$env:POCKET_LAWYER_OPENAI_API_KEY="YOUR_KEY"
```

### Ollama

```powershell
$env:POCKET_LAWYER_ENABLE_LLM="1"
$env:POCKET_LAWYER_LLM_PROVIDER="ollama"
$env:POCKET_LAWYER_LLM_MODEL="qwen3:1.7b"
$env:POCKET_LAWYER_LLM_API_BASE="http://127.0.0.1:11434/api"
```

For stronger hardware, change the model to `qwen3:8b`.

Before using the Ollama provider, install Ollama and pull the model:

```powershell
ollama pull qwen3:1.7b
```

Optional tuning:

```powershell
$env:POCKET_LAWYER_LLM_API_BASE="https://api.openai.com/v1"
$env:POCKET_LAWYER_LLM_TIMEOUT_SECONDS="20"
$env:POCKET_LAWYER_LLM_MAX_CANDIDATES="6"
$env:POCKET_LAWYER_LLM_MIN_CONFIDENCE="0.7"
```

Notes:

- OpenAI keeps the shorter `20s` default timeout.
- Ollama now uses a longer `60s` default timeout because local model load and first response are slower on weaker hardware.
- If your local machine is still slow, set `POCKET_LAWYER_LLM_TIMEOUT_SECONDS` to `90`.

## What The Analyzer Returns

When enabled, reports can include:

- `llm_status`
- `llm_provider`
- `llm_model`
- `llm_error`
- `llm_assessments`

Rule findings may also include:

- `analysis_method`
- `llm_confidence`
- `llm_reasoning_summary`
- `playbook_titles_used`

## Local Test Flow

1. Enable the environment variables above.
2. Run the API:

```powershell
$env:PYTHONPATH="src"
python -m pocket_lawyer.api
```

3. Send a clause likely to trigger both rules and semantic review:

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8765/analyze `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"contract_type":"employment","text":"The employee agrees to a non-compete for 24 months after employment."}'
```

4. Check:

- `llm_status`
- `llm_assessments`
- any finding with `analysis_method: "rule+llm"`

## Current Limitations

- The LLM path currently supports `openai` and `ollama`.
- The OpenAI path uses strict schema-constrained outputs.
- The Ollama path uses Ollama's structured output `format` field and local parsing/validation.
- OCR quality still matters more than LLM quality for scanned documents.
- The scoring engine is still policy-based, not ML-calibrated.

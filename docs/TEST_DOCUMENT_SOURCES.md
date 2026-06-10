# Test Document Sources

Use a mix of official templates and real-world filings. The point is to test both clause variety and document messiness.

## Best Sources

### 1. Startup India templates

Good for India-oriented sample agreements in predictable formats.

- Template index: <https://www.startupindia.gov.in/content/sih/en/reources/templates.html>
- Employment Agreement template: <https://www.startupindia.gov.in/content/dam/invest-india/Templates/public/Tools_templates/internal_templates/Lets_Venture/EMPLOYMENT_AGREEMENT%20%283%29.pdf>
- Consultancy Agreement template: <https://www.startupindia.gov.in/content/dam/invest-india/Templates/public/Tools_templates/internal_templates/Lets_Venture/CONSULTANCY_AGREEMENT.pdf>
- Confidentiality and IP Assignment Agreement template: <https://www.startupindia.gov.in/content/dam/invest-india/Templates/public/Tools_templates/internal_templates/Lets_Venture/CONFIDENTIALITY_IP_ASSIGNMENT_AGREEMENT.pdf>

Use these first for:
- employment
- freelancer / consultancy
- NDA / IP assignment

### 2. SEC EDGAR exhibits

Best source for real commercial agreements with natural clause variation.

- EDGAR full-text search: <https://www.sec.gov/edgar/search/>
- EDGAR search and access hub: <https://www.sec.gov/edgar/search-and-access>

Search terms that work well:
- `"employment agreement" exhibit`
- `"consulting agreement" exhibit`
- `"non disclosure agreement" exhibit`
- `"credit agreement" exhibit`
- `"lease agreement" exhibit`

Use these for:
- real-world wording variation
- long contracts
- nested clause numbering
- noisy formatting

### 3. CUAD / Atticus Project

Best source for benchmark-style contract review experiments.

- Atticus datasets page: <https://www.atticusprojectai.org/datasets/>
- Hugging Face CUAD dataset: <https://huggingface.co/datasets/theatticusproject/cuad>

Use CUAD for:
- labeled evaluation ideas
- clause-family coverage
- regression testing once retrieval/LLM stages are added

### 4. India government deed and lease templates

Good for rent / lease / property-style language.

- Department of Land Resources model property documents: <https://dolr.gov.in/document-category/model-property-registration-documents/>
- Lease deed page: <https://dolr.gov.in/document/lease-deed/>
- Delhi model deed page: <https://dmeast.delhi.gov.in/model-deed-page/>
- NHAI rent deed / lease agreement PDF: <https://nhai.gov.in/nhai/sites/default/files/2020/Rent%20deed%20Lease%20Agreement.pdf>

Use these for:
- lease / rent patterns
- deed-style drafting
- Indian legal formatting

## What To Test

For each source, keep examples in at least three buckets:

- clean digital PDF
- messy digital PDF with headers/footers
- scanned image or photographed page

For each contract type, keep:

- 5 clearly risky examples
- 5 standard/acceptable examples
- 5 borderline or ambiguous examples

## What To Avoid

- random blog templates with unclear legal provenance
- scraped PDFs with missing pages
- image-only screenshots without knowing whether OCR is configured

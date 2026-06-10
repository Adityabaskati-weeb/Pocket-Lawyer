# OCR Setup

Pocket Lawyer now treats OCR as an explicit intake capability instead of a hidden side effect.

## What the Code Does

- Text files use the `utf8_text` backend.
- Digital PDFs use `pypdf` first.
- DOCX uses `docling`.
- Scanned PDFs and images use `docling` only when OCR is configured.

The current code reads these environment variables:

```powershell
$env:POCKET_LAWYER_OCR_ENGINE = "tesseract_cli"
$env:POCKET_LAWYER_OCR_LANGS = "eng"
$env:POCKET_LAWYER_TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
$env:POCKET_LAWYER_FORCE_FULL_PAGE_OCR = "1"
$env:POCKET_LAWYER_DOCLING_ARTIFACTS = "C:\Users\<you>\.cache\docling-models"
```

If `POCKET_LAWYER_OCR_ENGINE` is not set, the app defaults to:

- `tesseract_cli` when `tesseract.exe` is on `PATH`
- otherwise `off`

## Local Setup

1. Install Python dependencies:

```powershell
python -m pip install -e ".[dev,docling]"
```

2. Install Tesseract for Windows.

Recommended binary source:
- UB Mannheim Windows builds: <https://ub-mannheim.github.io/Tesseract_Dokumentation/Tesseract_Doku_Windows.html>

3. Ensure `tesseract.exe` is either:
- on `PATH`, or
- referenced with `POCKET_LAWYER_TESSERACT_CMD`

4. Warm the Docling model cache for PDF/image parsing.

Docling's PDF pipeline needs model artifacts. If they are not already cached, point the app at a local artifact directory with:

```powershell
$env:POCKET_LAWYER_DOCLING_ARTIFACTS = "C:\path\to\docling-models"
```

## Verification

Check Tesseract:

```powershell
tesseract --version
```

Check Python packages:

```powershell
python -c "import docling, pypdf; print('docling ok'); print('pypdf ok')"
```

Test a scanned file:

```powershell
@'
from pathlib import Path
from pocket_lawyer.intake import extract_contract_document

path = Path(r".\sample_scan.png")
result = extract_contract_document(path.name, path.read_bytes())
print("backend:", result.backend)
print("ocr:", result.used_ocr, result.ocr_engine)
print("pages:", len(result.pages))
print("blocks:", len(result.blocks))
print(result.text[:500])
'@ | python -
```

## Expected Failure Modes

- `OCRSupportMissing`
  Means Tesseract is not configured.

- `DoclingArtifactsMissing`
  Means the Docling PDF/image pipeline cannot access its model weights.

- `IntakeError`
  Means the file could be parsed, but no readable text was extracted.

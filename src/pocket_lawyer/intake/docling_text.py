from __future__ import annotations

import importlib.util
import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from pocket_lawyer.intake.docling_export import document_from_docling_export
from pocket_lawyer.intake.errors import (
    DoclingArtifactsMissing,
    DoclingSupportMissing,
    IntakeError,
    OCRSupportMissing,
    UnsupportedFileType,
)
from pocket_lawyer.intake.models import ExtractedDocument
from pocket_lawyer.settings import get_settings


DOCLING_SUPPORTED_SUFFIXES = {
    ".pdf",
    ".docx",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def docling_is_available() -> bool:
    return importlib.util.find_spec("docling") is not None


def extract_docling_text(
    filename: str, content: bytes, require_ocr: bool = False
) -> str:
    return extract_docling_document(filename, content, require_ocr=require_ocr).text


def extract_docling_document(
    filename: str,
    content: bytes,
    require_ocr: bool = False,
) -> ExtractedDocument:
    suffix = Path(filename).suffix.lower()
    if suffix not in DOCLING_SUPPORTED_SUFFIXES:
        raise UnsupportedFileType(f"Docling intake does not support '{suffix}' files.")

    try:
        from huggingface_hub.errors import LocalEntryNotFoundError
    except ImportError:
        LocalEntryNotFoundError = RuntimeError  # type: ignore[assignment]

    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions,
            TesseractCliOcrOptions,
        )
        from docling.document_converter import (
            DocumentConverter,
            ImageFormatOption,
            PdfFormatOption,
        )
    except ImportError as exc:
        raise DoclingSupportMissing(_docling_install_message()) from exc

    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(content)
            temp_path = Path(handle.name)

        converter: DocumentConverter
        used_ocr = require_ocr or suffix in IMAGE_SUFFIXES
        ocr_engine = None

        if suffix == ".pdf":
            pipeline_options = PdfPipelineOptions()
            if get_settings().docling_artifacts_path is not None:
                pipeline_options.artifacts_path = str(
                    get_settings().docling_artifacts_path
                )
            if used_ocr:
                pipeline_options.do_ocr = True
                pipeline_options.ocr_options = _build_tesseract_cli_options(
                    TesseractCliOcrOptions
                )
                ocr_engine = "tesseract_cli"
            else:
                pipeline_options.do_ocr = False

            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
        elif suffix in IMAGE_SUFFIXES:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options = _build_tesseract_cli_options(
                TesseractCliOcrOptions
            )
            ocr_engine = "tesseract_cli"
            converter = DocumentConverter(
                format_options={
                    InputFormat.IMAGE: ImageFormatOption(
                        pipeline_options=pipeline_options
                    )
                }
            )
        else:
            converter = DocumentConverter()

        result = converter.convert(temp_path)
        document = document_from_docling_export(
            filename=filename,
            backend="docling",
            payload=result.document.export_to_dict(),
            used_ocr=used_ocr,
            ocr_engine=ocr_engine,
        )
    except OCRSupportMissing:
        raise
    except LocalEntryNotFoundError as exc:  # pragma: no cover - depends on runtime env
        raise DoclingArtifactsMissing(_docling_artifacts_message()) from exc
    except Exception as exc:
        raise IntakeError(
            "The uploaded file could not be parsed by the Docling intake backend."
        ) from exc
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except OSError:
                pass

    if not document.text:
        raise IntakeError("The uploaded file does not contain readable text.")

    return document


def _build_tesseract_cli_options(option_type: type) -> object:
    settings = get_settings()
    if settings.ocr_engine not in {"tesseract_cli", "tesseract"}:
        raise OCRSupportMissing(_ocr_setup_message())

    tesseract_cmd = settings.tesseract_cmd or shutil.which("tesseract")
    if tesseract_cmd is None:
        tesseract_cmd = shutil.which("tesseract.exe")
    if tesseract_cmd is None:
        raise OCRSupportMissing(_ocr_setup_message())

    kwargs: dict[str, object] = {
        "lang": list(settings.ocr_languages),
        "force_full_page_ocr": settings.force_full_page_ocr,
        "tesseract_cmd": tesseract_cmd,
    }

    tessdata_prefix = os.environ.get("TESSDATA_PREFIX")
    if tessdata_prefix:
        kwargs["path"] = tessdata_prefix

    return option_type(**kwargs)


def _docling_install_message() -> str:
    return (
        "Advanced intake for DOCX, images, and scanned PDFs requires the optional "
        "Docling backend. Install it with `python -m pip install -e .[docling]`."
    )


def _docling_artifacts_message() -> str:
    return (
        "Docling's PDF pipeline could not access its model artifacts. Download the "
        "required weights from `ds4sd/docling-models` or point "
        "`POCKET_LAWYER_DOCLING_ARTIFACTS` at a local artifact cache."
    )


def _ocr_setup_message() -> str:
    return (
        "OCR is not configured. Install Tesseract on this machine, ensure "
        "`tesseract.exe` is on PATH or set `POCKET_LAWYER_TESSERACT_CMD`, and keep "
        "`POCKET_LAWYER_OCR_ENGINE=tesseract_cli`."
    )


def get_docling_install_message() -> str:
    return _docling_install_message()

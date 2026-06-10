from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
DEFAULT_WEB_ROOT = PROJECT_ROOT / "web"


@dataclass(frozen=True)
class AppSettings:
    default_host: str
    default_port: int
    store_backend: str
    store_path: Path
    uploads_path: Path
    web_root: Path
    ocr_engine: str
    ocr_languages: tuple[str, ...]
    force_full_page_ocr: bool
    tesseract_cmd: str | None
    docling_artifacts_path: Path | None
    enable_llm: bool
    llm_provider: str
    llm_model: str
    llm_api_base: str
    llm_api_key: str | None
    llm_timeout_seconds: float
    llm_max_candidates: int
    llm_min_confidence: float


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _default_ocr_engine() -> str:
    explicit = os.environ.get("POCKET_LAWYER_OCR_ENGINE")
    if explicit:
        return explicit.strip().lower()

    tesseract_cmd = os.environ.get("POCKET_LAWYER_TESSERACT_CMD")
    if tesseract_cmd or shutil.which("tesseract") or shutil.which("tesseract.exe"):
        return "tesseract_cli"

    return "off"


def _default_llm_api_key() -> str | None:
    return os.environ.get("POCKET_LAWYER_LLM_API_KEY")


def _default_llm_provider() -> str:
    return os.environ.get("POCKET_LAWYER_LLM_PROVIDER", "openai").strip().lower()


def _default_llm_model(provider: str) -> str:
    explicit = os.environ.get("POCKET_LAWYER_LLM_MODEL")
    if explicit:
        return explicit.strip()
    if provider == "ollama":
        return "qwen3:1.7b"
    return "gpt-4o-mini"


def _default_llm_api_base(provider: str) -> str:
    explicit = os.environ.get("POCKET_LAWYER_LLM_API_BASE")
    if explicit:
        return explicit.rstrip("/")
    if provider == "ollama":
        return "http://127.0.0.1:11434/api"
    return "https://api.openai.com/v1"


def _provider_llm_api_key(provider: str) -> str | None:
    generic = _default_llm_api_key()
    if generic:
        return generic
    if provider == "openai":
        return os.environ.get("POCKET_LAWYER_OPENAI_API_KEY") or os.environ.get(
            "OPENAI_API_KEY"
        )
    return None


def _default_llm_timeout_seconds(provider: str) -> float:
    explicit = os.environ.get("POCKET_LAWYER_LLM_TIMEOUT_SECONDS")
    if explicit:
        return float(explicit)
    if provider == "ollama":
        return 60.0
    return 20.0


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    llm_provider = _default_llm_provider()
    port = int(os.environ.get("POCKET_LAWYER_PORT", "8765"))
    ocr_languages = tuple(
        language.strip()
        for language in os.environ.get("POCKET_LAWYER_OCR_LANGS", "eng").split(",")
        if language.strip()
    )
    artifacts_path = os.environ.get("POCKET_LAWYER_DOCLING_ARTIFACTS")
    return AppSettings(
        default_host=os.environ.get("POCKET_LAWYER_HOST", "127.0.0.1"),
        default_port=port,
        store_backend=os.environ.get("POCKET_LAWYER_STORE_BACKEND", "auto")
        .strip()
        .lower(),
        store_path=Path(os.environ.get("POCKET_LAWYER_STORE", "data/reports.json")),
        uploads_path=Path(
            os.environ.get("POCKET_LAWYER_UPLOAD_STORE", "data/uploads")
        ),
        web_root=Path(os.environ.get("POCKET_LAWYER_WEB_ROOT", DEFAULT_WEB_ROOT)),
        ocr_engine=_default_ocr_engine(),
        ocr_languages=ocr_languages or ("eng",),
        force_full_page_ocr=_env_flag("POCKET_LAWYER_FORCE_FULL_PAGE_OCR"),
        tesseract_cmd=os.environ.get("POCKET_LAWYER_TESSERACT_CMD"),
        docling_artifacts_path=Path(artifacts_path) if artifacts_path else None,
        enable_llm=_env_flag("POCKET_LAWYER_ENABLE_LLM"),
        llm_provider=llm_provider,
        llm_model=_default_llm_model(llm_provider),
        llm_api_base=_default_llm_api_base(llm_provider),
        llm_api_key=_provider_llm_api_key(llm_provider),
        llm_timeout_seconds=_default_llm_timeout_seconds(llm_provider),
        llm_max_candidates=int(
            os.environ.get("POCKET_LAWYER_LLM_MAX_CANDIDATES", "6")
        ),
        llm_min_confidence=float(
            os.environ.get("POCKET_LAWYER_LLM_MIN_CONFIDENCE", "0.7")
        ),
    )

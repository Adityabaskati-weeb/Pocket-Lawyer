class IntakeError(ValueError):
    """Raised when uploaded contract content cannot be read."""


class UnsupportedFileType(IntakeError):
    """Raised when a file type is not supported by the MVP intake layer."""


class PDFSupportMissing(IntakeError):
    """Raised when PDF parsing is requested without a local parser installed."""


class DoclingSupportMissing(IntakeError):
    """Raised when optional Docling-backed intake support is not installed."""


class OCRSupportMissing(IntakeError):
    """Raised when OCR-backed parsing is requested without a configured OCR engine."""


class DoclingArtifactsMissing(IntakeError):
    """Raised when the Docling PDF pipeline cannot access its model artifacts."""

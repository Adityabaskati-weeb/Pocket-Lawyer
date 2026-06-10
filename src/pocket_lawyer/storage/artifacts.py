from __future__ import annotations

import mimetypes
from pathlib import Path
import time
from typing import Any
from uuid import uuid4


class LocalArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def save_artifact(
        self, filename: str | None, content: bytes
    ) -> dict[str, Any]:
        original_filename = filename or "contract.bin"
        suffix = Path(original_filename).suffix
        storage_key = f"{uuid4().hex}{suffix}"
        artifact_path = self.root / storage_key

        self.root.mkdir(parents=True, exist_ok=True)
        temp_path = artifact_path.with_suffix(f"{artifact_path.suffix}.tmp")
        temp_path.write_bytes(content)
        _replace_or_fallback(temp_path, artifact_path, content)

        return {
            "storage_backend": "local_fs",
            "storage_key": storage_key,
            "original_filename": original_filename,
            "byte_size": len(content),
            "content_type": mimetypes.guess_type(original_filename)[0],
        }

    def delete_artifact(self, artifact: object) -> None:
        if not isinstance(artifact, dict):
            return
        if artifact.get("storage_backend") != "local_fs":
            return

        storage_key = artifact.get("storage_key")
        if not isinstance(storage_key, str) or not storage_key.strip():
            return

        artifact_path = self.root / storage_key
        artifact_path.unlink(missing_ok=True)


def _replace_or_fallback(
    temp_path: Path,
    target_path: Path,
    content: bytes,
    *,
    attempts: int = 5,
    delay_seconds: float = 0.1,
) -> None:
    last_error: PermissionError | None = None
    for _ in range(attempts):
        try:
            temp_path.replace(target_path)
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(delay_seconds)

    # OneDrive and Windows security tools can deny os.replace while still allowing
    # normal writes. Keep upload analysis usable rather than failing the scan.
    target_path.write_bytes(content)
    try:
        temp_path.unlink(missing_ok=True)
    except PermissionError:
        if last_error is not None:
            return

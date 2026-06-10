from __future__ import annotations

import mimetypes
from pathlib import Path
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
        temp_path.replace(artifact_path)

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

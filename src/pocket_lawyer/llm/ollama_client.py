from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaClauseAnalysisError(RuntimeError):
    """Raised when the Ollama clause-analysis request fails."""


class OllamaClauseAnalysisClient:
    def __init__(
        self,
        *,
        api_base: str,
        api_key: str | None,
        timeout_seconds: float,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def analyze(
        self,
        *,
        model: str,
        system_prompt: str,
        user_message: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        grounded_schema = json.dumps(schema, ensure_ascii=True)
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"{system_prompt}\n\n"
                        "Return only a JSON object that matches this schema exactly:\n"
                        f"{grounded_schema}"
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "format": schema,
            "keep_alive": "10m",
            "options": {"temperature": 0},
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = Request(
            url=f"{self.api_base}/chat",
            headers=headers,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw_payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OllamaClauseAnalysisError(
                f"Ollama request failed with HTTP {exc.code}: {detail}"
            ) from exc
        except URLError as exc:
            raise OllamaClauseAnalysisError(
                f"Ollama request failed: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise OllamaClauseAnalysisError("Ollama request timed out.") from exc
        except json.JSONDecodeError as exc:
            raise OllamaClauseAnalysisError(
                "Ollama response was not valid JSON."
            ) from exc

        return self._extract_structured_payload(raw_payload)

    def _extract_structured_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if isinstance(payload.get("error"), str) and payload["error"].strip():
            raise OllamaClauseAnalysisError(payload["error"].strip())

        message = payload.get("message")
        if not isinstance(message, dict):
            raise OllamaClauseAnalysisError("Ollama response did not include a message.")

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise OllamaClauseAnalysisError("Ollama response content was empty.")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OllamaClauseAnalysisError(
                "Ollama structured response was not valid JSON."
            ) from exc

        if not isinstance(parsed, dict):
            raise OllamaClauseAnalysisError(
                "Ollama structured response must be a JSON object."
            )
        return parsed

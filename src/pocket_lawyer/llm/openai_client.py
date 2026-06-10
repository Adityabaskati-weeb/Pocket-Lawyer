from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OpenAIClauseAnalysisError(RuntimeError):
    """Raised when the OpenAI clause-analysis request fails."""


class OpenAIClauseAnalysisClient:
    def __init__(
        self,
        *,
        api_base: str,
        api_key: str,
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
        payload = {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "pocket_lawyer_clause_assessments",
                    "strict": True,
                    "schema": schema,
                },
            },
        }

        request = Request(
            url=f"{self.api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw_payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OpenAIClauseAnalysisError(
                f"OpenAI request failed with HTTP {exc.code}: {detail}"
            ) from exc
        except URLError as exc:
            raise OpenAIClauseAnalysisError(
                f"OpenAI request failed: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise OpenAIClauseAnalysisError("OpenAI request timed out.") from exc
        except json.JSONDecodeError as exc:
            raise OpenAIClauseAnalysisError(
                "OpenAI response was not valid JSON."
            ) from exc

        return self._extract_structured_payload(raw_payload)

    def _extract_structured_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise OpenAIClauseAnalysisError("OpenAI response did not include choices.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise OpenAIClauseAnalysisError("OpenAI response choice was malformed.")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise OpenAIClauseAnalysisError("OpenAI response did not include a message.")

        refusal = message.get("refusal")
        if isinstance(refusal, str) and refusal.strip():
            raise OpenAIClauseAnalysisError(f"Model refused request: {refusal.strip()}")

        content_text = self._message_content_to_text(message.get("content"))
        if not content_text:
            raise OpenAIClauseAnalysisError("OpenAI response content was empty.")

        try:
            parsed = json.loads(content_text)
        except json.JSONDecodeError as exc:
            raise OpenAIClauseAnalysisError(
                "OpenAI structured response was not valid JSON."
            ) from exc

        if not isinstance(parsed, dict):
            raise OpenAIClauseAnalysisError(
                "OpenAI structured response must be a JSON object."
            )
        return parsed

    def _message_content_to_text(self, content: object) -> str:
        if isinstance(content, str):
            return content.strip()

        if not isinstance(content, list):
            return ""

        text_parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text" and isinstance(item.get("text"), str):
                text_parts.append(item["text"])

        return "".join(text_parts).strip()

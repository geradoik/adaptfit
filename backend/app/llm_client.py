from __future__ import annotations

import os

API_URL = "https://api.groq.com/openai/v1/chat/completions"   # Groq speaks the same format as OpenAI
DEFAULT_MODEL = "openai/gpt-oss-120b"   # change with the ADAPTFIT_LLM_MODEL environment variable
TIMEOUT_SECONDS = 30.0
MAX_TOKENS = 1000   # gpt-oss "thinks" first and the thinking counts too, so leave room beyond the 150-word answer


class LLMUnavailable(Exception):
    """The AI could not give an answer right now. The reason is in the message."""


class GroqClient:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, timeout: float = TIMEOUT_SECONDS, transport=None):
        self.api_key, self.model, self.timeout, self.transport = api_key, model, timeout, transport

    def complete(self, system: str, user: str) -> str:
        """Send one question, return the text of the answer. Raises LLMUnavailable on any failure."""
        import httpx

        body = {"model": self.model, "max_completion_tokens": MAX_TOKENS,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if self.model.startswith("openai/gpt-oss"):
            body["reasoning_effort"] = "low"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                response = client.post(API_URL, json=body, headers=headers)
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"] or ""
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as error:
            raise LLMUnavailable(f"{type(error).__name__}") from error
        if not text.strip():
            raise LLMUnavailable("empty answer")
        return text
 
 
class FakeClient:
    """For tests and for demos with no key. Returns a canned reply, or raises if told to."""
 
    def __init__(self, reply: str = "", error: Exception | None = None):
        self.reply, self.error, self.calls = reply, error, []
 
    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if self.error:
            raise self.error
        return self.reply
 
 
def get_client():
    """The real client if GROQ_API_KEY is set in the server's environment, otherwise None."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        return None
    return GroqClient(key, os.getenv("ADAPTFIT_LLM_MODEL", DEFAULT_MODEL))
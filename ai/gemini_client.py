"""
AI Client — Multi-Provider
Supports Google Gemini and Groq (free) as AI backends.
Uses the requests library — no SDK dependency required.
"""

import time
import requests


# ── Provider configurations ───────────────────────────────────────────

PROVIDERS = {
    "Groq (Llama 3 — recommended)": {
        "id": "groq",
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
        "key_url": "https://console.groq.com/keys",
        "note": "Free: 30 req/min, 14,400 req/day. Works globally.",
    },
    "Gemini 2.0 Flash-Lite": {
        "id": "gemini",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent",
        "model": "gemini-2.0-flash-lite",
        "key_url": "https://aistudio.google.com/app/apikey",
        "note": "Free tier. May not work in all regions.",
    },
    "Gemini 2.0 Flash": {
        "id": "gemini",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        "model": "gemini-2.0-flash",
        "key_url": "https://aistudio.google.com/app/apikey",
        "note": "Free tier. May not work in all regions.",
    },
    "Gemini 2.5 Flash": {
        "id": "gemini",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        "model": "gemini-2.5-flash",
        "key_url": "https://aistudio.google.com/app/apikey",
        "note": "Free tier. May not work in all regions.",
    },
}

PROVIDER_NAMES = list(PROVIDERS.keys())


class AIClient:
    """Unified client supporting both Gemini and Groq APIs."""

    def __init__(self, api_key: str, provider_name: str = PROVIDER_NAMES[0]) -> None:
        """
        Initialise with an API key and provider name.

        Args:
            api_key:       A valid API key for the chosen provider.
            provider_name: One of the keys in PROVIDERS dict.
        """
        if not api_key or not api_key.strip():
            raise ValueError("A valid API key is required.")
        self._api_key = api_key.strip()

        config = PROVIDERS.get(provider_name)
        if not config:
            raise ValueError(f"Unknown provider: {provider_name}")

        self._provider_id = config["id"]
        self._endpoint = config["endpoint"]
        self._model = config["model"]

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        """
        Send a prompt to the configured AI provider and return text.

        Args:
            prompt:     The text prompt to send.
            max_tokens: Maximum output tokens.

        Returns:
            The model's response as a plain string.

        Raises:
            RuntimeError: On any API error after one retry on 429.
        """
        if self._provider_id == "groq":
            return self._call_groq(prompt, max_tokens)
        else:
            return self._call_gemini(prompt, max_tokens)

    # ── Groq (OpenAI-compatible) ──────────────────────────────────────

    def _call_groq(self, prompt: str, max_tokens: int) -> str:
        """Call Groq's OpenAI-compatible chat completions API."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        response = requests.post(
            self._endpoint, headers=headers, json=payload, timeout=60
        )

        # Retry on rate limit
        if response.status_code == 429:
            time.sleep(10)
            response = requests.post(
                self._endpoint, headers=headers, json=payload, timeout=60
            )

        if response.status_code != 200:
            self._raise_error(response)

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"Unexpected Groq response: {response.text[:500]}"
            ) from exc

    # ── Gemini ────────────────────────────────────────────────────────

    def _call_gemini(self, prompt: str, max_tokens: int) -> str:
        """Call Google Gemini's generateContent API."""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7,
            },
        }

        response = requests.post(
            self._endpoint,
            params={"key": self._api_key},
            json=payload,
            timeout=60,
        )

        # Retry on rate limit
        if response.status_code == 429:
            time.sleep(10)
            response = requests.post(
                self._endpoint,
                params={"key": self._api_key},
                json=payload,
                timeout=60,
            )

        if response.status_code != 200:
            self._raise_error(response)

        try:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"Unexpected Gemini response: {response.text[:500]}"
            ) from exc

    # ── Shared helpers ────────────────────────────────────────────────

    @staticmethod
    def _raise_error(response: requests.Response) -> None:
        """Raise a RuntimeError with the API error message."""
        try:
            detail = response.json().get("error", {})
            if isinstance(detail, dict):
                detail = detail.get("message", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(
            f"API error (HTTP {response.status_code}): {detail}"
        )

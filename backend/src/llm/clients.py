"""LLM call layer using litellm.

litellm unifies multiple providers (OpenAI, Gemini, and many more) behind a
single OpenAI-style message interface, with native image (vision) support
and automatic fallback between models. The model is specified as
"provider/model" (e.g. "gemini/gemini-3.5-flash", "openai/gpt-4o") — litellm
internally decides which API to call and which API key env var to use based
on the prefix (GEMINI_API_KEY, OPENAI_API_KEY, etc.).
"""

import os

import litellm


class LLMError(Exception):
    """Controlled error when talking to the LLM."""


def _fallback_models() -> list[str] | None:
    """Fallback model list for litellm, or None if none is configured.

    Returns None (not an empty list) when there's no fallback: litellm's
    fallback path activates just by checking `fallbacks is not None`, so an
    empty list would still trigger it unnecessarily.
    """
    fallback = os.getenv("LLM_FALLBACK", "").strip()
    return [fallback] if fallback else None


def call_llm(b64_image: str, mime_type: str, system_prompt: str, user_prompt: str) -> str:
    """Send the image (base64) + prompts to the primary LLM (LLM_PRIMARY).

    If LLM_FALLBACK is set and the primary model fails, litellm automatically
    retries with that model before the error is raised. Returns the raw
    response text (expected to be JSON); content validation happens in
    extractor.py, not here.
    """
    primary_model = os.getenv("LLM_PRIMARY", "gemini/gemini-3.5-flash").strip()

    try:
        response = litellm.completion(
            model=primary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64_image}"},
                        },
                    ],
                },
            ],
            response_format={"type": "json_object"},
            fallbacks=_fallback_models(),
            max_tokens=1024,
            temperature=0,
        )
    except Exception as exc:  # noqa: BLE001 - translated into a controlled domain error
        raise LLMError(f"Error al llamar al LLM ({primary_model}): {exc}") from exc

    content = response.choices[0].message.content
    if not content:
        raise LLMError("El LLM devolvió una respuesta vacía.")
    return content

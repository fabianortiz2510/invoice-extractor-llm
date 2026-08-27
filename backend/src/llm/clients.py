import os
import litellm
class LLMError(Exception):
    """Controlled error when talking to the LLM."""


def fallback_models() -> list[str] | None:
    fallback = os.getenv("LLM_FALLBACK", "").strip()
    return [fallback] if fallback else None


def call_llm(b64_image: str, mime_type: str, system_prompt: str, user_prompt: str) -> str:
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
            fallbacks=fallback_models(),
            max_tokens=1024,
            temperature=0,
        )
    except Exception as exc:  # noqa: BLE001 - translated into a controlled domain error
        raise LLMError(f"Error al llamar al LLM ({primary_model}): {exc}") from exc

    content = response.choices[0].message.content
    if not content:
        raise LLMError("El LLM devolvió una respuesta vacía.")
    return content

"""Capa de llamada al LLM usando litellm.

litellm unifica múltiples proveedores (OpenAI, Gemini, y muchos más) bajo una
sola interfaz de mensajes estilo OpenAI, con soporte nativo de imágenes
(vision) y fallback automático entre modelos. El modelo se especifica como
"proveedor/modelo" (ej. "gemini/gemini-3.5-flash", "openai/gpt-4o") — litellm
decide internamente qué API llamar y qué variable de entorno de API key usar
según el prefijo (GEMINI_API_KEY, OPENAI_API_KEY, etc.).
"""

import os

import litellm


class LLMError(Exception):
    """Error controlado al comunicarse con el LLM."""


def _fallback_models() -> list[str] | None:
    """Lista de modelos de fallback para litellm, o None si no hay ninguno configurado.

    Se devuelve None (no una lista vacía) cuando no hay fallback: litellm
    activa su mecanismo interno de fallback con solo comprobar
    `fallbacks is not None`, así que una lista vacía igual lo activaría
    innecesariamente.
    """
    fallback = os.getenv("LLM_FALLBACK", "").strip()
    return [fallback] if fallback else None


def call_llm(b64_image: str, mime_type: str, system_prompt: str, user_prompt: str) -> str:
    """Envía la imagen (base64) + prompts al LLM primario (LLM_PRIMARY).

    Si LLM_FALLBACK está configurado y el primario falla, litellm reintenta
    automáticamente con ese modelo antes de propagar el error. Devuelve el
    texto crudo de la respuesta (se espera JSON como texto); la validación
    del contenido se hace en extractor.py, no aquí.
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
    except Exception as exc:  # noqa: BLE001 - se traduce a un error de dominio controlado
        raise LLMError(f"Error al llamar al LLM ({primary_model}): {exc}") from exc

    content = response.choices[0].message.content
    if not content:
        raise LLMError("El LLM devolvió una respuesta vacía.")
    return content

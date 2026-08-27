import os
from abc import ABC, abstractmethod

class LLMError(Exception):
    """Error controlado al comunicarse con el proveedor de LLM."""


class BaseLLMClient(ABC):
    """Interfaz común que deben implementar todos los proveedores de LLM."""

    @abstractmethod
    def extract(self, b64_image: str, mime_type: str, system_prompt: str, user_prompt: str) -> str:
        """Envía la imagen (base64) + prompts al LLM y devuelve el texto crudo de la respuesta.

        Se espera que la respuesta sea un JSON (como texto); la validación
        del contenido se hace en extractor.py, no aquí.
        """
        raise NotImplementedError


class OpenAIVisionClient(BaseLLMClient):
    """Cliente para modelos de OpenAI con capacidad de visión (ej. gpt-4o)."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMError(
                "Falta la variable de entorno OPENAI_API_KEY. "
                "Configúrala en tu archivo .env."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMError(
                "El paquete 'openai' no está instalado. Ejecuta: pip install -r requirements.txt"
            ) from exc

        self._client = OpenAI(api_key=api_key)
        self._model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")

    def extract(self, b64_image: str, mime_type: str, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=1024,
                temperature=0,
                response_format={"type": "json_object"},
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
            )
        except Exception as exc:  # noqa: BLE001 - se traduce a un error de dominio controlado
            raise LLMError(f"Error al llamar a la API de OpenAI: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMError("OpenAI devolvió una respuesta vacía.")
        return content


class AnthropicVisionClient(BaseLLMClient):
    """Cliente para modelos de Anthropic con capacidad de visión (ej. claude-sonnet-5)."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMError(
                "Falta la variable de entorno ANTHROPIC_API_KEY. "
                "Configúrala en tu archivo .env."
            )
        try:
            import anthropic
        except ImportError as exc:
            raise LLMError(
                "El paquete 'anthropic' no está instalado. Ejecuta: pip install -r requirements.txt"
            ) from exc

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = os.getenv("ANTHROPIC_VISION_MODEL", "claude-sonnet-5")

    def extract(self, b64_image: str, mime_type: str, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": b64_image,
                                },
                            },
                            {"type": "text", "text": user_prompt},
                        ],
                    }
                ],
            )
        except Exception as exc:  # noqa: BLE001 - se traduce a un error de dominio controlado
            raise LLMError(f"Error al llamar a la API de Anthropic: {exc}") from exc

        text_blocks = [block.text for block in response.content if block.type == "text"]
        if not text_blocks:
            raise LLMError("Anthropic devolvió una respuesta sin contenido de texto.")
        return "".join(text_blocks)


class GeminiVisionClient(BaseLLMClient):
    """Cliente para modelos de Google Gemini con capacidad de visión."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise LLMError(
                "Falta la variable de entorno GEMINI_API_KEY. "
                "Configúrala en tu archivo .env."
            )
        try:
            from google import genai
        except ImportError as exc:
            raise LLMError(
                "El paquete 'google-genai' no está instalado. Ejecuta: pip install -r requirements.txt"
            ) from exc

        self._client = genai.Client(api_key=api_key)
        self._model = os.getenv("GEMINI_VISION_MODEL", "gemini-3.5-flash")

    def extract(self, b64_image: str, mime_type: str, system_prompt: str, user_prompt: str) -> str:
        from google.genai import types
        import base64

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=[
                    types.Part.from_bytes(data=base64.b64decode(b64_image), mime_type=mime_type),
                    user_prompt,
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0,
                ),
            )
        except Exception as exc:  # noqa: BLE001 - se traduce a un error de dominio controlado
            raise LLMError(f"Error al llamar a la API de Gemini: {exc}") from exc

        text = response.text
        if not text:
            raise LLMError("Gemini devolvió una respuesta vacía.")
        return text


def _build_client(provider: str) -> BaseLLMClient:
    if provider == "openai":
        return OpenAIVisionClient()
    if provider == "anthropic":
        return AnthropicVisionClient()
    if provider == "gemini":
        return GeminiVisionClient()

    raise LLMError(
        f"'{provider}' no es un proveedor válido. Usa 'openai', 'anthropic' o 'gemini'."
    )


def get_llm_client() -> BaseLLMClient:
    """Factory: instancia el cliente LLM primario según LLM_PROVIDER (openai | anthropic | gemini)."""
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    try:
        return _build_client(provider)
    except LLMError as exc:
        raise LLMError(f"LLM_PROVIDER={exc}") from exc


def get_fallback_llm_client() -> BaseLLMClient | None:
    """Factory: instancia el cliente LLM de fallback según LLM_FALLBACK_PROVIDER.

    Devuelve None si la variable no está configurada (el fallback es opcional).
    """
    provider = os.getenv("LLM_FALLBACK_PROVIDER", "").strip().lower()
    if not provider:
        return None
    try:
        return _build_client(provider)
    except LLMError as exc:
        raise LLMError(f"LLM_FALLBACK_PROVIDER={exc}") from exc

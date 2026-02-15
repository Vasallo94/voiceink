import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # Load from current directory (dev)
load_dotenv(os.path.expanduser("~/.voice2clip.env"))  # Load from home (prod/app)

logger = logging.getLogger(__name__)

TRANSCRIPTION_PROMPT = """\
Eres Voice2Clip, un asistente experto en convertir "pensamientos hablados" en texto limpio y natural.

TU MISIÓN:
Transformar el audio en exactamente lo que el usuario PRETENDE escribir, eliminando el ruido del proceso de pensar.

SI ESCUCHAS UNA INSTRUCCIÓN O PETICIÓN (para una IA, un email, código):
- Escribe la instrucción directa y clara.
- Elimina todo el "meta-lenguaje" (ej: "mira, quiero que hagas...", "a ver si puedes...", "bueno, lo que quiero es...").
- NO estructures excesivamente (evita listas con guiones si no son necesarias).
- Mantén un tono natural, fluido y directo.

SI ESCUCHAS UN DICTADO O NOTA:
- Transcribe con fidelidad pero con limpieza.
- Quita repeticiones, tartamudeos y muletillas ("eh", "mmm", "o sea").

REGLAS DE ORO:
1. NUNCA respondas al usuario. SOLO devuelve el texto transformado.
2. Tu salida va directa al Portapapeles. NO pongas comillas ni introducciones.
3. Respeta el idioma del audio.
"""


class GeminiTranscriber:
    def __init__(self, api_key: str | None = None):
        """Initialize the Gemini client."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. Set it in .env or environment variables."
            )

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash"

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file using Gemini API.

        Args:
            audio_path: Path to the WAV file to transcribe.

        Returns:
            Transcribed and cleaned text, or an error message.
        """
        if not os.path.exists(audio_path):
            return "Error: Audio file not found."

        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            file_size_kb = len(audio_bytes) / 1024
            logger.info("Transcribing audio: %.1f KB", file_size_kb)

            # Use system_instruction for better adherence to "Prompt Engineer" role
            response = self.client.models.generate_content(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=TRANSCRIPTION_PROMPT,
                    temperature=0.3,  # Lower temperature for more deterministic/focused output
                ),
                contents=[
                    types.Content(
                        parts=[
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type="audio/wav",
                                    data=audio_bytes,
                                )
                            ),
                        ]
                    )
                ],
            )

            result = response.text.strip()
            logger.info("Transcription complete: %d chars", len(result))
            return result

        except Exception as e:
            logger.error("Transcription error: %s", e)
            return f"Error during transcription: {e}"

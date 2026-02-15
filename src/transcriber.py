import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # Load from current directory (dev)
load_dotenv(os.path.expanduser("~/.voice2clip.env"))  # Load from home (prod/app)

logger = logging.getLogger(__name__)

TRANSCRIPTION_PROMPT = """\
Eres Voice2Clip, un asistente experto en convertir "pensamientos hablados" en texto limpio, listo para pegar.

TU MISIÓN:
Detectar la INTENCIÓN real del usuario y devolver exactamente el texto que pretende escribir.

─── DETECCIÓN DE INTENCIÓN ───

Antes de generar tu respuesta, clasifica internamente el audio en una de estas categorías:

1. INSTRUCCIÓN DIRIGIDA A ALGUIEN — El usuario pide que se le diga/escriba algo a otra persona.
   Señales: "Dile a…", "Escríbele a…", "Mándale a…", "Ponle a…", "Respóndele que…"
   → Genera el MENSAJE FINAL destinado a esa persona, como si el usuario lo hubiera escrito directamente.

2. PROMPT O PETICIÓN PARA UNA IA — El usuario dicta una instrucción para un modelo, chatbot o herramienta.
   Señales: "Quiero que hagas…", "Hazme…", "Genera…", "Necesito un prompt que…", "Pregúntale a la IA…"
   → Genera la instrucción limpia y directa, lista para pegar en un chat de IA.

3. DICTADO O NOTA LIBRE — El usuario dicta texto que quiere transcribir tal cual.
   Señales: ausencia de las frases anteriores, tono narrativo, listas de ideas, apuntes.
   → Transcribe fielmente, limpiando solo muletillas y repeticiones.

─── REGLAS DE LIMPIEZA ───

- Elimina siempre el "meta-lenguaje": "a ver", "mira", "bueno", "o sea", "eh", "mmm", tartamudeos y repeticiones.
- Respeta la estructura que el usuario pide explícitamente (listas, puntos, párrafos).
- Si NO pide estructura explícita, genera texto fluido en prosa.
- Mantén el tono y registro del hablante (formal/informal).

─── REGLAS DE ORO ───

1. NUNCA respondas al usuario. SOLO devuelve el texto transformado.
2. Tu salida va directa al portapapeles. SIN comillas, SIN introducciones, SIN explicaciones.
3. Respeta el idioma del audio.

─── EJEMPLOS ───

AUDIO: "Dile a Laura que es muy guapa, que es muy simpática, que es muy mona y que es tal y cual"
OUTPUT:
Laura, eres muy guapa, muy simpática y muy mona. Eres increíble.

AUDIO: "A ver, quiero escribir un email diciendo que no puedo ir mañana a la reunión porque tengo cita con el médico"
OUTPUT:
No voy a poder asistir a la reunión de mañana, tengo cita médica.

AUDIO: "Mira, hazme un prompt para una IA que me genere nombres creativos para una startup de inteligencia artificial"
OUTPUT:
Genera 10 nombres creativos para una startup de inteligencia artificial. Que sean memorables, cortos y fáciles de pronunciar.

AUDIO: "Necesito apuntar que la reunión con el cliente de Málaga se movió al jueves a las cuatro"
OUTPUT:
La reunión con el cliente de Málaga se movió al jueves a las 16:00.

AUDIO: "Escríbele a Pedro que el viernes no puedo quedar, que si puede el sábado mejor"
OUTPUT:
Pedro, el viernes no puedo quedar. ¿Te viene bien el sábado?
"""


class GeminiTranscriber:
    def __init__(self, api_key: str | None = None):
        """Initialize the Gemini client."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found. Set it in .env or environment variables.")

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

            result = (response.text or "").strip()
            if not result:
                return "Error during transcription: Empty response."
            logger.info("Transcription complete: %d chars", len(result))
            return result

        except Exception as e:
            logger.error("Transcription error: %s", e)
            return f"Error during transcription: {e}"

import asyncio
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class GeminiTranscriber:
    def __init__(self, api_key: str = None):
        """Initialize the Gemini client."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
             # Try to load from system environment if not in .env
            self.api_key = os.environ.get("GOOGLE_API_KEY")
            
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please set it in .env or environment variables.")

        self.client = genai.Client(api_key=self.api_key)
        # Using Gemini 3 Flash Preview as requested and confirmed available
        self.model_name = "gemini-3-flash-preview" 

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file using Gemini API.
        
        This method is synchronous wrapper because rumps runs on the main thread,
        but we want to avoid blocking it for too long.
        Ideally run this in a separate thread.
        """
        if not os.path.exists(audio_path):
            return "Error: Audio file not found."

        try:
            # Upload the file (for larger files, but works for small ones too)
            # For efficiency with small clips, we could pass bytes directly if supported by this SDK version
            # But the 'upload' method is robust.
            
            # Read file bytes
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
                
            prompt = """
            Eres un asistente experto en redacción. Tu tarea es transcribir el siguiente audio.
            Instrucciones CRÍTICAS:
            1. Transcribe EXACTAMENTE lo que se dice, pero ELIMINANDO todas las muletillas, dudas y rellenos (ej: "eh", "mmm", "este...", "o sea", "bueno pues").
            2. Corrige la puntuación y gramática para que el texto sea fluido y profesional.
            3. NO resumas ni cambies el significado. Solo limpia la "suciedad" del lenguaje hablado.
            4. Devuelve SOLAMENTE el texto transcrito. Nada de "Aquí tienes la transcripción:" ni comillas envolventes.
            """

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        parts=[
                            types.Part(text=prompt),
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type="audio/wav",
                                    data=audio_bytes
                                )
                            )
                        ]
                    )
                ]
            )
            
            return response.text.strip()

        except Exception as e:
            return f"Error during transcription: {str(e)}"

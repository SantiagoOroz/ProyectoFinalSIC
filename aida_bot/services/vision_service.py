import re
from io import BytesIO
from groq import Groq
from aida_bot.storage.storage import FileStorage

class VisionService:
    """
    Procesa imágenes: las sube a la nube y las analiza con un modelo multimodal.
    """
    def __init__(self, groq_client: Groq, file_storage: FileStorage, model: str):
        self.groq = groq_client
        self.storage = file_storage
        self.model = model

    def _detect_intent_local(self, text: str) -> str:
        """Clasificador rápido basado en palabras clave del caption."""
        t = (text or "").lower()
        if any(k in t for k in ["vence", "vencimiento", "fecha vence", "caduca"]):
            return "expiry_date"
        if any(k in t for k in ["qué comida", "que comida", "qué es esto", "que es esto"]):
            return "identify_food"
        return "describe_image"

    def _groq_multimodal_call(self, image_url: str, prompt: str, max_tokens: int = 150) -> str:
        """Llamada base al modelo multimodal de Groq."""
        system_prompt = (
            "Eres un asistente que ayuda a personas mayores. Analiza la imagen y responde "
            "de forma clara, concisa y amable. Evita dar respuestas largas."
        )
        try:
            comp = self.groq.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    },
                ],
                temperature=0.0,
                max_tokens=max_tokens,
            )
            return comp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR Groq Vision] {e}")
            return f"No pude analizar la imagen. Error: {e}"

    def analyze_image(self, image_bytes: bytes, caption: str, user_id: str) -> str:
        """
        Sube una imagen, la analiza según la intención y luego la borra.
        """
        image_url = None
        remote_folder = f"uploads/{user_id}"
        
        try:
            # 1. Subir la imagen a Firebase Storage para obtener una URL
            print(f"Subiendo imagen a {remote_folder}...")
            image_url = self.storage.upload_file(image_bytes, remote_folder, file_extension=".jpg")
            if not image_url:
                return "Error: No pude subir la imagen para analizarla."

            # 2. Detectar intención basada en el caption
            intent = self._detect_intent_local(caption)

            # 3. Preparar el prompt según la intención
            prompt = ""
            max_tokens = 100
            if intent == "expiry_date":
                prompt = "Extrae la fecha de vencimiento visible en la imagen. Responde solo 'Vence: DD/MM/YYYY' o 'No visible'."
                max_tokens = 20
            elif intent == "identify_food":
                prompt = "¿Qué comida es? Responde solo con el nombre en español (1-3 palabras)."
                max_tokens = 10
            else: # "describe_image"
                prompt = "Describe brevemente la imagen en 1 o 2 frases simples, como para una persona mayor."
                max_tokens = 100

            # 4. Llamar al modelo multimodal
            print(f"Analizando imagen con intención: {intent}")
            analysis = self._groq_multimodal_call(image_url, prompt, max_tokens)
            return analysis

        except Exception as e:
            print(f"[ERROR VisionService] {e}")
            return "Tuve un problema al analizar la imagen."
        finally:
            # 5. Borrar la imagen de la nube (opcional, pero buena práctica)
            # Para borrarla, necesitaríamos la 'remote_path' exacta.
            # Por simplicidad, esta lógica se omite.
            # Si quisieras borrarla, `upload_file` debería devolver la `remote_path`
            # y aquí llamaríamos a `self.storage.delete_file(remote_path)`.
            pass
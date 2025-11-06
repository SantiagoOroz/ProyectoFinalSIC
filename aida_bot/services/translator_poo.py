import requests
from langdetect import detect, LangDetectException


class DatasetTranslator:

    def __init__(self, api_key: str, api_url="https://api.groq.com/openai/v1/chat/completions", model="llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.system_prompt = (
              """1. Eres un traductor profesional.
                2. Estás especializado en educación digital y comunicación inclusiva.
                3. Tu tarea es traducir contenido educativo y de asistencia tecnológica destinado a personas mayores.
                4. Mantén siempre un tono amable, claro y fácil de entender.
                5. Evita los tecnicismos innecesarios o palabras difíciles.
                6. Conserva el significado educativo y respeta el contexto original del texto.
                7. Cuando se te indique un cambio de idioma, realiza la traducción al nuevo idioma.
                8. Si una persona te habla en un idioma determinado, responde en ese mismo idioma.
                9. No cambies de idioma hasta que se te dé una nueva indicación explícita.
                10.Tu objetivo es facilitar la comprensión y hacer accesible la información a los adultos mayores."""
        )

    def detect_language(self, text: str) -> str:
        """Detecta el idioma del texto de forma local."""
        try:
            lang = detect(text)
            return lang  # ej: 'es', 'en', 'fr'
        except LangDetectException:
            return "es"

    def translate_text(self, text: str, target_lang: str) -> str:
        #Traduce el texto al idioma indicado.
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Traduce este texto al idioma '{target_lang}': {text}"}
            ]
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=20)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"[ERROR TRADUCCIÓN] No se pudo traducir el texto: {e}")
            return text

    def auto_translate(self, text: str, user_message) -> str:
        """
        Detecta el idioma del mensaje del usuario (texto)
        y traduce el texto de respuesta a ese idioma automáticamente.
        """
        try:
            lang = self.detect_language(user_message.text)
            if lang == "es":
                return text  # ya está en español
            translated = self.translate_text(text, lang)
            return translated
        except Exception as e:
            print(f"[ERROR AUTO TRADUCCIÓN] {e}")
            return text
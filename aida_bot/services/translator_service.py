<<<<<<< HEAD
import requests
from langdetect import detect

class Translator:

    def __init__(self, api_key: str, api_url="https://api.groq.com/openai/v1/chat/completions", model="llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.system_prompt = (
             "Eres un traductor profesional especializado en educación digital y comunicación inclusiva. "
            "Tu tarea es traducir contenido educativo y de asistencia tecnológica para personas mayores, "
            "manteniendo un tono amable, claro y fácil de entender. Evita tecnicismos innecesarios y conserva "
            "el significado educativo y el contexto original del texto."
        )

    def detect_language(self, text: str) -> str:
        """Detecta el idioma del texto de forma local."""
        try:
            lang = detect(text)
            return lang  
        except:
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
=======
import requests
from langdetect import detect

class Translator:

    def __init__(self, api_key: str, api_url="https://api.groq.com/openai/v1/chat/completions", model="llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.system_prompt = (
             "Eres un traductor profesional especializado en educación digital y comunicación inclusiva. "
            "Tu tarea es traducir contenido educativo y de asistencia tecnológica para personas mayores, "
            "manteniendo un tono amable, claro y fácil de entender. Evita tecnicismos innecesarios y conserva "
            "el significado educativo y el contexto original del texto."
        )

    def detect_language(self, text: str) -> str:
        """Detecta el idioma del texto de forma local."""
        try:
            lang = detect(text)
            return lang  
        except:
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
>>>>>>> 00a1fa9 (Agrego Idioma)
            return text
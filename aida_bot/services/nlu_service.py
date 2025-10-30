import json
import requests
from groq import Groq
from langdetect import detect
from aida_bot import config
from aida_bot.services.speech_service import SpeechService # Para la lista de voces

class NLUService:
    """
    Procesamiento del lenguaje natural (chat, clasificación, traducción) usando Groq.
    """
    def __init__(self, api_key: str, api_url: str, chat_model: str, classifier_model: str):
        self.api_key = api_key
        self.api_url = api_url
        self.chat_model = chat_model
        self.classifier_model = classifier_model
        self.client = Groq(api_key=api_key) # Cliente para llamadas multimodales (visión)
        
        self.intent_system_prompt = f"""
Eres un clasificador de intenciones. Analiza la petición del usuario y determina la intención.
Las intenciones posibles son:
- 'SET_AUDIO_OFF': El usuario quiere dejar de recibir respuestas en audio. (Ej: "deja de mandarme audios", "solo texto")
- 'SET_AUDIO_ON': El usuario quiere empezar a recibir respuestas en audio. (Ej: "activa la voz", "prefiero escucharte")
- 'SET_VOICE': El usuario quiere cambiar la voz del asistente. (Ej: "cambia la voz a méxico", "pon la voz de tomás")
- 'GET_SENTIMENT': El usuario quiere analizar el sentimiento de una frase. (Ej: "/sentimiento estoy muy feliz", "analiza esto: ...")
- 'TRANSLATE_TEXT': El usuario quiere traducir un texto. (Ej: "traduce 'hola' al inglés", "cómo se dice 'adiós' en francés")
- 'CHAT': Es una conversación normal, una pregunta, o cualquier otra cosa.

Si la intención es 'SET_VOICE', identifica la voz de la lista y pon su ID en 'payload'.
LISTA DE VOCES:
{json.dumps(SpeechService.VOICES, indent=2, ensure_ascii=False)}

Si la intención es 'GET_SENTIMENT', extrae el texto a analizar en 'payload'.
Ej: "analiza el sentimiento de 'qué mal día'" -> {{"intent": "GET_SENTIMENT", "payload": "qué mal día"}}

Si la intención es 'TRANSLATE_TEXT', extrae el texto y el idioma destino en 'payload'.
Ej: "traduce 'me gusta' al inglés" -> {{"intent": "TRANSLATE_TEXT", "payload": {{"text": "me gusta", "lang": "inglés"}}}}

Responde ÚNICAMENTE con un objeto JSON válido: {{"intent": "INTENCION", "payload": ...}}
"""

    def _call_api(self, model: str, messages: list, is_json: bool = False, timeout: int = 20) -> str:
        """Función helper para llamar a la API de Groq."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            "model": model,
            "messages": messages,
            "temperature": 0.1 if is_json else 0.7,
        }
        if is_json:
            data["response_format"] = {"type": "json_object"}

        try:
            resp = requests.post(self.api_url, headers=headers, json=data, timeout=timeout)
            resp.raise_for_status() # Lanza error si el status no es 2xx
            
            response_data = resp.json()
            content = response_data['choices'][0]['message']['content']
            return content.strip()
            
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR NLU HTTP {e.response.status_code}] {e.response.text}")
            return f"Error IA {e.response.status_code}"
        except requests.exceptions.RequestException as e:
            print(f"[ERROR NLU Conexión] {e}")
            return "Error de conexión con la IA."
        except Exception as e:
            print(f"[ERROR NLU Desconocido] {e}")
            return "Error desconocido en NLU."

    def detect_intent(self, user_text: str) -> dict:
        """Usa un modelo para clasificar la intención del usuario."""
        messages = [
            {"role": "system", "content": self.intent_system_prompt},
            {"role": "user", "content": user_text}
        ]
        try:
            response_json_str = self._call_api(self.classifier_model, messages, is_json=True, timeout=10)
            intent_data = json.loads(response_json_str)
            
            if "intent" not in intent_data:
                return {"intent": "CHAT", "payload": None}
            return intent_data
            
        except Exception as e:
            print(f"[ERROR Intención JSON] {e}. Respuesta: {response_json_str}")
            return {"intent": "CHAT", "payload": None} # Fallback

    def get_chat_response(self, user_text: str) -> str:
        """Obtiene una respuesta de chat normal."""
        messages = [
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
        return self._call_api(self.chat_model, messages)

    def translate(self, text: str, target_lang: str) -> str:
        """Traduce texto usando la IA."""
        prompt = f"Traduce el siguiente texto al idioma '{target_lang}', responde solo con el texto traducido:\n\n{text}"
        messages = [
            {"role": "system", "content": "Eres un traductor profesional."},
            {"role": "user", "content": prompt}
        ]
        return self._call_api(self.chat_model, messages)
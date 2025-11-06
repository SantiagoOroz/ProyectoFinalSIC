# aida_bot/services/nlu_service.py
import requests
import json
from .. import config
from .speech_service import SpeechService
from pathlib import Path


class NLUService:
    """Procesamiento del lenguaje natural (respuestas inteligentes)."""
    
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model = config.NLU_MODEL
        self.classifier_model = config.INTENT_MODEL
      
        # --- PROMPT DE CONVERSACIÓN ---
      
        # Ruta del dataset
        ruta_dataset = Path(r"C:\AIDA\ProyectoFinalSIC\aida_bot\dataset.json")

        # Cargar el dataset en memoria al iniciar el bot
        with open(ruta_dataset, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
            
        self.system_prompt = f"""
            1. Eres AIDA, un asistente digital paciente, empático y claro, diseñado para enseñar a personas mayores a usar tecnología.
            2. Tu objetivo principal es facilitar la vida cotidiana de los usuarios, ayudándolos a entender y usar herramientas tecnológicas con confianza.
            3. Cuando tengas que responder, busca la respuesta en este data set '{dataset}'; si no está, busca la respuesta en la API de Groq.
            4. Explica siempre paso a paso, de manera simple y ordenada.
            5. Utiliza ejemplos cotidianos y fáciles de relacionar con la vida diaria.
            6. Evita tecnicismos o términos complicados; si debes usarlos, explícalos de forma sencilla.
            7. Mantén un tono amable, alentador y empático en todo momento.
            8. Si detectas que el usuario está frustrado, confundido o triste (por análisis de sentimiento),
            9. Sé aún más paciente.
            10. Simplifica tu explicación.
            11. Ofrece apoyo y palabras de ánimo.
            12. Nunca te rindas con el usuario: siempre busca una manera diferente o más simple de ayudar.
            13. Respeta las reglas de idioma:
            14. Si el usuario te habla en un idioma, responde en ese mismo idioma.
            15. Si se te indica explícitamente un cambio de idioma, traduce y continúa en el nuevo idioma.
            16. No cambies de idioma hasta recibir una nueva instrucción.
            17. Tu prioridad es que la persona comprenda, se sienta acompañada y gane confianza con la tecnología.
            """

        
        # --- PROMPT DE CLASIFICADOR MULTI-INTENCIÓN (MEJORADO) ---
        self.intent_system_prompt = f"""
Eres un clasificador de intenciones experto. Tu trabajo es analizar el mensaje del usuario y descomponerlo en un plan de acción JSON.
Debes identificar tres cosas:
1.  **Conversación**: ¿El usuario quiere chatear, hacer una pregunta o dar una orden?
2.  **Configuración**: ¿El usuario está intentando cambiar una preferencia del bot (audio o voz)?
3.  **Análisis Emocional**: ¿El usuario está expresando una emoción fuerte (positiva o negativa) que deberíamos analizar?

Tu respuesta DEBE ser un objeto JSON con esta estructura:
{{
  "has_chat_intent": true/false,
  "chat_content": "...", 
  "configuration": {{
    "set_audio": "ON" / "OFF" / null,
    "set_voice": "ID_DE_VOZ" / null
  }},
  "analysis_required": {{
    "sentiment": true/false
  }}
}}

--- GUÍA DE ANÁLISIS ---

* **has_chat_intent / chat_content**:
    * Si el usuario saluda, pregunta algo ("¿qué día es hoy?"), o da una orden ("explícame esto"), `has_chat_intent` es `true`.
    * `chat_content` debe ser el texto completo de esa conversación.
    * Si el usuario *solo* cambia una configuración (ej: "solo texto"), `has_chat_intent` es `false` y `chat_content` es `null`.

* **configuration**:
    * Busca peticiones de audio: "solo texto", "no me mandes audios" -> `set_audio: "OFF"`. "activa la voz" -> `set_audio: "ON"`.
    * Busca peticiones de voz. Usa la lista de abajo. "voz de hombre" -> "es-AR-TomasNeural". "la mexicana" -> "es-MX-DaliaNeural".
    * Si un mensaje tiene chat Y configuración (ej: "hola, pon la voz de tomás"), ambas partes del JSON deben estar llenas.

* **analysis_required**:
    * `sentiment` es `true` si el usuario expresa cómo se siente.
    * Ejemplos Positivos: "qué alegría", "me encanta", "muchas gracias, me salvaste".
    * Ejemplos Negativos: "estoy harto", "no entiendo nada", "qué frustrante", "me rindo".
    * No lo actives para saludos simples como "hola" o preguntas neutrales.

--- LISTA DE VOCES DISPONIBLES (Nombre amigable: ID) ---
{json.dumps(SpeechService.VOICES, indent=2, ensure_ascii=False)}

--- EJEMPLOS DE ANÁLISIS ---

Usuario: "deja de mandarme audios"
{{
  "has_chat_intent": false,
  "chat_content": null,
  "configuration": {{
    "set_audio": "OFF",
    "set_voice": null
  }},
  "analysis_required": {{
    "sentiment": false
  }}
}}

Usuario: "hola, pon la voz de tomás por favor, estoy medio frustrado con la otra"
{{
  "has_chat_intent": true,
  "chat_content": "hola, pon la voz de tomás por favor, estoy medio frustrado con la otra",
  "configuration": {{
    "set_audio": null,
    "set_voice": "es-AR-TomasNeural"
  }},
  "analysis_required": {{
    "sentiment": true
  }}
}}

Usuario: "qué día es hoy?"
{{
  "has_chat_intent": true,
  "chat_content": "qué día es hoy?",
  "configuration": {{
    "set_audio": null,
    "set_voice": null
  }},
  "analysis_required": {{
    "sentiment": false
  }}
}}

Usuario: "usa la voz de méxico"
{{
  "has_chat_intent": false,
  "chat_content": null,
  "configuration": {{
    "set_audio": null,
    "set_voice": "es-MX-DaliaNeural"
  }},
  "analysis_required": {{
    "sentiment": false
  }}
}}

Usuario: "¡¡No puedo hacer esto!! ¡¡Qué bronca!!"
{{
  "has_chat_intent": true,
  "chat_content": "¡¡No puedo hacer esto!! ¡¡Qué bronca!!",
  "configuration": {{
    "set_audio": null,
    "set_voice": null
  }},
  "analysis_required": {{
    "sentiment": true
  }}
}}
"""

    def detect_intent(self, user_text: str) -> dict:
        """
        Usa un modelo para clasificar las intenciones del usuario.
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            "model": self.classifier_model,
            "messages": [
                {"role": "system", "content": self.intent_system_prompt},
                {"role": "user", "content": user_text}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        
        # Estructura de fallback en caso de error
        default_response = {
            "has_chat_intent": True,
            "chat_content": user_text,
            "configuration": {"set_audio": None, "set_voice": None},
            "analysis_required": {"sentiment": False}
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=data, timeout=15)
            if resp.status_code == 200:
                intent_data = json.loads(resp.json()['choices'][0]['message']['content'])
                # Validamos que la estructura básica exista
                if "has_chat_intent" not in intent_data or "configuration" not in intent_data:
                    return default_response
                return intent_data
            else:
                print(f"[ERROR Intención] Código {resp.status_code}: {resp.text}")
                return default_response
        except Exception as e:
            print(f"[ERROR Intención] {e}")
            return default_response


    def get_response(self, user_text: str) -> str:
        """Genera una respuesta de chat normal."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            "model": self.model, 
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_text}
            ]
        }
        try:
            resp = requests.post(self.api_url, headers=headers, json=data, timeout=20)
            if resp.status_code == 200:
                respuesta = resp.json()['choices'][0]['message']['content']
                return respuesta.strip()
            else:
                return f" [Error IA {resp.status_code}] No pude generar una respuesta."
        except requests.exceptions.RequestException as e:
            return f" [Error Conexión Groq] No pude contactar al servicio de IA. ¿Estás conectado a internet? ({e})"
import requests
import whisper
import torch
import os
from tempfile import NamedTemporaryFile
import json

# texto-a-voz
import asyncio
import edge_tts
from pydub import AudioSegment

class SpeechService:
    """Maneja audio (voz a texto, texto a voz) usando Whisper y Edge-TTS."""
    
    # --- Diccionario centralizado de voces ---
    VOICES = {
        "Elena (Argentina)": "es-AR-ElenaNeural",
        "Tomás (Argentina)": "es-AR-TomasNeural",
        "Dalia (México)": "es-MX-DaliaNeural",
        "Elvira (España)": "es-ES-ElviraNeural",
        "Salome (Colombia)": "es-CO-SalomeNeural",
        "Andrew (EEUU)": "en-US-AndrewNeural",
        "Denise (Francia)": "fr-FR-DeniseNeural",
        "Killian (Alemania)": "de-DE-KillianNeural",
        "Francisca (Brasil)": "pt-BR-FranciscaNeural",
        "Elsa (Italia)": "it-IT-ElsaNeural",
        "Nanami (Japón)": "ja-JP-NanamiNeural",
        "Xiaoxiao (China)": "zh-CN-XiaoxiaoNeural",
    }
    
    # Voz por defecto para nuevos usuarios
    DEFAULT_VOICE = VOICES["Elena (Argentina)"] # "es-AR-ElenaNeural"

    def __init__(self, model_size="base"):
        """
        Carga el modelo Whisper al iniciar.
        """
        print(f"Cargando el modelo Whisper '{model_size}'...")
        self.model = whisper.load_model(model_size)
        self.language = "es" # Idioma para transcripción
    
    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribe los bytes de un archivo de audio a texto, forzando el idioma español.
        """
        temp_file_path = None
        try:
            with NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name

            audio = whisper.load_audio(temp_file_path)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

            options = whisper.DecodingOptions(language=self.language, fp16=torch.cuda.is_available())
            result = whisper.decode(self.model, mel, options)
            
            return result.text.strip()
        except Exception as e:
            print(f"[ERROR Whisper] No se pudo transcribir el audio: {e}")
            return ""
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    
    def synthesize(self, text: str, voice_id: str, output_filename: str = "response_audio") -> str | None:
        """
        Sintetiza texto a un archivo de audio .ogg usando edge-tts.
        Usa el 'voice_id' proporcionado.
        Retorna el audio que fue almacenado de manera temporal.
        """
        async def _async_synthesize():
            """Función interna asíncrona para manejar la generación de audio."""
            mp3_path = f"{output_filename}.mp3"
            ogg_path = f"{output_filename}.ogg"
            
            try:
                # --- CAMBIO CLAVE ---
                # Ya no usa 'self.default_tts_voice', usa el argumento 'voice_id'
                communicate = edge_tts.Communicate(text, voice_id) 
                await communicate.save(mp3_path)

                audio = AudioSegment.from_mp3(mp3_path)
                audio.export(ogg_path, format="ogg", codec="libopus")
                
                return ogg_path
            except Exception as e:
                print(f"[ERROR TTS] No se pudo sintetizar el audio ({voice_id}): {e}")
                return None
            finally:
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)

        try:
            audio_path = asyncio.run(_async_synthesize())
            return audio_path
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_path = loop.run_until_complete(_async_synthesize())
            return audio_path

class VisionService:
    """Procesamiento de imágenes (OCR, reconocimiento, detección, etc.)."""
    def analyze_image(self, image_bytes: bytes):
        return "Una descripción de la imagen generada por un modelo de visión"


class NLUService:
    """Procesamiento del lenguaje natural (respuestas inteligentes)."""
    def __init__(self, api_key: str, api_url: str, system_prompt="Eres un asistente general amable y claro."):
        self.system_prompt = system_prompt
        self.api_key = api_key
        self.api_url = api_url
        self.model = "llama-3.3-70b-versatile" 
        self.classifier_model = "llama-3.3-70b-versatile"
        
        self.intent_system_prompt = f"""
Eres un clasificador de intenciones. Analiza la petición del usuario y determina si es una conversación normal o un comando para cambiar una configuración del bot.
Las intenciones posibles son:
- 'SET_AUDIO_OFF': El usuario quiere dejar de recibir respuestas en audio. (Ej: "deja de mandarme audios", "solo texto por favor", "no quiero escuchar", "desactiva la voz")
- 'SET_AUDIO_ON': El usuario quiere empezar a recibir respuestas en audio. (Ej: "quiero que me mandes audios", "activa la voz", "prefiero escucharte")
- 'SET_VOICE': El usuario quiere cambiar la voz del asistente. (Ej: "cambia la voz a la de méxico", "prefiero la voz de tomás", "pon una voz masculina", "quiero la voz en inglés")
- 'CHAT': Es una conversación normal, una pregunta, o cualquier otra cosa.

Si la intención es 'SET_VOICE', debes identificar a qué voz se refiere el usuario de la siguiente lista y poner su ID exacto en el campo 'payload'.
Si no puedes identificar una voz específica, usa la más cercana (ej: "voz de hombre" -> "es-AR-TomasNeural").
Si la intención no es 'SET_VOICE' o 'CHAT', el payload es null.

LISTA DE VOCES DISPONIBLES (Nombre amigable: ID):
{json.dumps(SpeechService.VOICES, indent=2, ensure_ascii=False)}

Responde ÚNICAMENTE con un objeto JSON válido con "intent" y "payload".
Ejemplos de respuesta:

Usuario: "deja de mandarme audios"
{{"intent": "SET_AUDIO_OFF", "payload": null}}

Usuario: "usa la voz de tomás"
{{"intent": "SET_VOICE", "payload": "es-AR-TomasNeural"}}

Usuario: "me gusta más la voz mexicana"
{{"intent": "SET_VOICE", "payload": "es-MX-DaliaNeural"}}

Usuario: "hola cómo estás"
{{"intent": "CHAT", "payload": null}}

Usuario: "pon la voz en inglés"
{{"intent": "SET_VOICE", "payload": "en-US-AndrewNeural"}}
"""

    # Método para detectar la intención
    def detect_intent(self, user_text: str) -> dict:
        """
        Usa un modelo para clasificar la intención del usuario.
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            "model": self.classifier_model,
            "messages": [
                {"role": "system", "content": self.intent_system_prompt}, # Pasa tanto el prompt de intención
                {"role": "user", "content": user_text} # como lo que pide el usuario
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        
        try:
            resp = requests.post(self.api_url, headers=headers, json=data, timeout=10)
            if resp.status_code == 200:
                # Aseguramos que devuelva un dict con 'intent' y 'payload'
                intent_data = json.loads(resp.json()['choices'][0]['message']['content'])
                if "intent" not in intent_data:
                    return {"intent": "CHAT", "payload": None}
                return intent_data
            else:
                print(f"[ERROR Intención] Código {resp.status_code}")
                return {"intent": "CHAT", "payload": None} 
        except Exception as e:
            print(f"[ERROR Intención] {e}")
            return {"intent": "CHAT", "payload": None}


    def get_response(self, user_text: str) -> str:
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

class SessionManager:
    """Manejo de sesiones de usuario (estado, configuración, contexto)."""
    def __init__(self):
        self.sessions = {}

    def ensure(self, chat_id: int):
        if chat_id not in self.sessions:
            # Configuración por usuario
            self.sessions[chat_id] = {
                "greeted": False, 
                "context": [],
                "responder_con_audio": True,
                "tts_voice": SpeechService.DEFAULT_VOICE
            }
        return self.sessions[chat_id]


class ModularBot:
    """Plantilla general del bot orientado a objetos."""
    def __init__(self, bot_instance, nlu, speech, vision, sessions):
        self.bot = bot_instance
        self.nlu = nlu
        self.speech = speech
        self.vision = vision
        self.sessions = sessions
        self._setup_handlers()

    def _send_response(self, msg, response_text: str):
        """
        Método centralizado para enviar respuestas.
        Primero envía el texto y luego, si está activado, el audio
        CON LA VOZ SELECCIONADA POR EL USUARIO.
        """
        # Enviar siempre la respuesta como texto
        self.bot.reply_to(msg, response_text)
        
        # Leemos la configuración de la sesión
        session = self.sessions.ensure(msg.chat.id)
        
        # Si la opción de sintetizar en está sesión está activada...
        if session.get("responder_con_audio", True):
            
            # Obtenemos la voz guardada en la sesión del usuario
            current_voice = session.get("tts_voice", SpeechService.DEFAULT_VOICE)
            
            self.bot.send_chat_action(msg.chat.id, "record_voice")
            
            # Pasamos la voz específica al sintetizador
            audio_path = self.speech.synthesize(response_text, current_voice)
            
            if audio_path:
                try:
                    with open(audio_path, 'rb') as audio_file:
                        self.bot.send_voice(msg.chat.id, audio_file)
                finally:
                    os.remove(audio_path)

    # Método central para procesar texto y ejecutar la intención
    def _process_user_message(self, msg, user_text: str):
        """
        Procesa el texto del usuario, detectando primero la intención 
        y luego generando una respuesta.
        """
        session = self.sessions.ensure(msg.chat.id)
        
        # 1. Detectar intención
        intent_data = self.nlu.detect_intent(user_text)
        intent = intent_data.get("intent", "CHAT")
        payload = intent_data.get("payload") # <-- Obtenemos el payload

        # 2. Actuar según la intención
        if intent == "SET_AUDIO_OFF":
            session["responder_con_audio"] = False
            response_text = "Entendido. A partir de ahora, solo te responderé con texto. 👍"
            self._send_response(msg, response_text)
        
        elif intent == "SET_AUDIO_ON":
            session["responder_con_audio"] = True
            response_text = "¡Hecho! Volveré a enviarte las respuestas en audio además del texto. 🔊"
            self._send_response(msg, response_text)
        
        # Cambiar voz
        elif intent == "SET_VOICE":
            # Verificamos que el payload sea una voz válida del diccionario
            if payload and payload in self.speech.VOICES.values():
                session["tts_voice"] = payload # Guardamos la nueva voz
                
                # Buscamos el nombre amigable para la respuesta
                friendly_name = "desconocida"
                for name, id_ in self.speech.VOICES.items():
                    if id_ == payload:
                        friendly_name = name
                        break
                        
                response_text = f"¡Perfecto! He cambiado mi voz a {friendly_name}. 🎤"
                self._send_response(msg, response_text) # Respondemos (ya con la nueva voz)
            else:
                response_text = f"Hmm, no pude reconocer la voz '{payload}'. Intenta de nuevo (ej: 'usa la voz de México')."
                self._send_response(msg, response_text) # Respondemos con la voz anterior
        
        elif intent == "CHAT":
            # 3. Si es un chat normal, obtener respuesta de la IA
            self.bot.send_chat_action(msg.chat.id, "typing")
            response_text = self.nlu.get_response(user_text)
            self._send_response(msg, response_text)


    def _setup_handlers(self):
        # ... (el resto de los handlers: handle_start, handle_text, handle_voice, handle_photo) ...
        # --- NO SE REQUIEREN CAMBIOS EN LOS HANDLERS ---
        @self.bot.message_handler(commands=["start"])
        def handle_start(msg):
            session = self.sessions.ensure(msg.chat.id)
            if not session["greeted"]:
                welcome = "👋 ¡Hola! Soy tu asistente digital. Enviame texto, audio o fotos para empezar 🚀"
                self._send_response(msg, welcome)
                session["greeted"] = True
            else:
                self.bot.reply_to(msg, "Ya estamos en marcha 😊")

        @self.bot.message_handler(content_types=["text"])
        def handle_text(msg):
            self._process_user_message(msg, msg.text)

        @self.bot.message_handler(content_types=["voice"])
        def handle_voice(msg):
            self.bot.send_chat_action(msg.chat.id, "typing")
            try:
                file_info = self.bot.get_file(msg.voice.file_id)
                audio_bytes = self.bot.download_file(file_info.file_path)
                
                transcribed_text = self.speech.transcribe(audio_bytes)
                
                if transcribed_text:
                    self.bot.reply_to(msg, f"🎤 Entendido: *\"{transcribed_text}\"*", parse_mode="Markdown")
                    
                    self._process_user_message(msg, transcribed_text)
                    
                else:
                    response_text = "⚠️ No pude entender lo que dijiste en el audio."
                    self._send_response(msg, response_text)

            except Exception as e:
                print(f"[ERROR VOZ] {e}")
                self.bot.reply_to(msg, "⚠️ No pude procesar tu audio.")

        @self.bot.message_handler(content_types=["photo"])
        def handle_photo(msg):
            
            self.bot.send_chat_action(msg.chat.id, "typing")
            try:
                file_id = msg.photo[-1].file_id
                file_info = self.bot.get_file(file_id)
                image_bytes = self.bot.download_file(file_info.file_path)
                
                description = self.vision.analyze_image(image_bytes)
                prompt = f"El usuario me envió una imagen. Mi análisis dice que contiene: '{description}'. Responde a esto."
                
                self.bot.send_chat_action(msg.chat.id, "typing")
                response_text = self.nlu.get_response(prompt)
                self._send_response(msg, response_text)
                
            except Exception as e:
                print(f"[ERROR IMAGEN] {e}")
                self.bot.reply_to(msg, "⚠️ No pude analizar la imagen.")

    def run(self):
        print("✅ Bot iniciado correctamente.")
        import time
        while True:
            try:
                self.bot.polling(none_stop=True)
            except Exception as e:
                print(f"[ERROR GENERAL] {e}")
                print("Reiniciando en 5 segundos...")

                time.sleep(5)

import os
import time
import telebot
from aida_bot.services.speech_service import SpeechService

class PersistentSessionManager:
    """
    Maneja sesiones de usuario (estado, configuración) usando Firestore
    para persistencia.
    """
    def __init__(self, db_client):
        self.db = db_client
        self.sessions_collection = self.db.collection("user_sessions")
        self.DEFAULT_SESSION = {
            "greeted": False,
            "context": [],
            "responder_con_audio": True,
            "tts_voice": SpeechService.DEFAULT_VOICE,
            "form_step": None, # Para el formulario de perfiles
            "form_data": {}    # Para el formulario de perfiles
        }

    def get(self, chat_id: int) -> dict:
        """Obtiene la sesión de un usuario. Si no existe, la crea."""
        session_doc = self.sessions_collection.document(str(chat_id)).get()
        if session_doc.exists:
            # Combina los valores por defecto con los guardados
            session_data = self.DEFAULT_SESSION.copy()
            session_data.update(session_doc.to_dict())
            return session_data
        else:
            # Crea y guarda la sesión por defecto
            self.sessions_collection.document(str(chat_id)).set(self.DEFAULT_SESSION)
            return self.DEFAULT_SESSION.copy()

    def update(self, chat_id: int, session_data: dict):
        """Actualiza la sesión de un usuario en la base de datos."""
        try:
            self.sessions_collection.document(str(chat_id)).set(session_data, merge=True)
        except Exception as e:
            print(f"[ERROR SessionManager] No se pudo guardar la sesión {chat_id}: {e}")

class ModularBot:
    """
    El orquestador principal del bot. Conecta los handlers de Telegram
    con los diferentes servicios (NLU, Speech, Vision, etc.).
    """
    def __init__(self, bot_instance, nlu, speech, vision, sentiment, sessions, profile_form):
        self.bot = bot_instance
        self.nlu = nlu
        self.speech = speech
        self.vision = vision
        self.sentiment = sentiment
        self.sessions = sessions
        self.profile_form = profile_form # El gestor del formulario /start
        self._setup_handlers()

    def _send_response(self, msg, response_text: str):
        """
        Método centralizado para enviar respuestas.
        Envía texto y, si el usuario lo tiene activado, también el audio.
        """
        # 1. Enviar siempre la respuesta como texto
        try:
            self.bot.reply_to(msg, response_text, parse_mode="Markdown")
        except Exception:
             self.bot.reply_to(msg, response_text) # Fallback sin Markdown

        # 2. Leer la configuración de la sesión (ya debe existir por el 'ensure')
        session = self.sessions.get(msg.chat.id)

        # 3. Si la síntesis de voz está activada, enviar audio
        if session.get("responder_con_audio", True):
            current_voice = session.get("tts_voice", SpeechService.DEFAULT_VOICE)
            self.bot.send_chat_action(msg.chat.id, "record_voice")
            
            audio_path = self.speech.synthesize(response_text, current_voice)
            
            if audio_path:
                try:
                    with open(audio_path, 'rb') as audio_file:
                        self.bot.send_voice(msg.chat.id, audio_file)
                except Exception as e:
                    print(f"[ERROR TTS Send] {e}")
                finally:
                    os.remove(audio_path) # Borrar archivo temporal

    def _process_user_message(self, msg, user_text: str):
        """
        Procesa el texto del usuario, detecta la intención y actúa.
        """
        session = self.sessions.get(msg.chat.id)
        
        # 1. Detectar intención (¿es un comando o un chat?)
        intent_data = self.nlu.detect_intent(user_text)
        intent = intent_data.get("intent", "CHAT")
        payload = intent_data.get("payload")

        response_text = ""
        update_session = False

        # 2. Actuar según la intención
        if intent == "SET_AUDIO_OFF":
            session["responder_con_audio"] = False
            response_text = "Entendido. A partir de ahora, solo te responderé con texto. 👍"
            update_session = True
        
        elif intent == "SET_AUDIO_ON":
            session["responder_con_audio"] = True
            response_text = "¡Hecho! Volveré a enviarte las respuestas en audio además del texto. 🔊"
            update_session = True

        elif intent == "SET_VOICE":
            if payload and payload in self.speech.VOICES.values():
                session["tts_voice"] = payload
                friendly_name = next((name for name, id_ in self.speech.VOICES.items() if id_ == payload), "desconocida")
                response_text = f"¡Perfecto! He cambiado mi voz a {friendly_name}. 🎤"
                update_session = True
            else:
                response_text = f"Hmm, no pude reconocer esa voz. Intenta de nuevo (ej: 'usa la voz de México')."

        elif intent == "GET_SENTIMENT":
            if not payload: # Si no escribió texto junto al comando
                payload = "..."
            sentiment_result = self.sentiment.analyze(payload)
            response_text = f"Análisis de: *\"{payload}\"*\n\n{sentiment_result}"

        elif intent == "TRANSLATE_TEXT":
            if payload and payload.get("text") and payload.get("lang"):
                text_to_translate = payload['text']
                target_lang = payload['lang']
                translated_text = self.nlu.translate(text_to_translate, target_lang)
                response_text = f"Traducción a *{target_lang}*:\n\n{translated_text}"
            else:
                response_text = "No entendí qué texto traducir o a qué idioma."

        elif intent == "CHAT":
            self.bot.send_chat_action(msg.chat.id, "typing")
            response_text = self.nlu.get_chat_response(user_text)

        else:
            response_text = "No entendí esa intención."

        # 3. Guardar la sesión si hubo cambios
        if update_session:
            self.sessions.update(msg.chat.id, session)

        # 4. Enviar la respuesta
        if response_text:
            self._send_response(msg, response_text)

    def _setup_handlers(self):
        """
        Configura los handlers para mensajes de texto, voz y foto.
        /start y los comandos de perfil son manejados por PerfilFormulario.
        """

        @self.bot.message_handler(content_types=["text"], func=lambda msg: not msg.text.startswith('/'))
        def handle_text(msg):
            """Maneja mensajes de texto que NO son comandos."""
            session = self.sessions.get(msg.chat.id)
            
            # Comprueba si el usuario está en medio de un formulario
            if self.profile_form.is_user_in_form(session):
                # Si está en un formulario, delega el mensaje al gestor de formularios
                self.profile_form.handle_form_message(msg, session)
            else:
                # Si no está en un formulario, procesa como chat normal
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
                    self.bot.send_chat_action(msg.chat.id, "typing")
                    # Procesa el texto transcrito
                    self._process_user_message(msg, transcribed_text)
                else:
                    self._send_response(msg, "⚠️ No pude entender lo que dijiste en el audio.")
            except Exception as e:
                print(f"[ERROR VOZ] {e}")
                self._send_response(msg, "⚠️ Hubo un error al procesar tu audio.")

        @self.bot.message_handler(content_types=["photo"])
        def handle_photo(msg):
            self.bot.send_chat_action(msg.chat.id, "typing")
            try:
                file_id = msg.photo[-1].file_id
                file_info = self.bot.get_file(file_id)
                image_bytes = self.bot.download_file(file_info.file_path)
                caption = msg.caption or ""
                
                # Usar el servicio de visión para analizar la imagen
                analysis_text = self.vision.analyze_image(image_bytes, caption, str(msg.chat.id))
                
                # Crear un prompt para la NLU basado en el análisis
                prompt = f"""
El usuario me envió una imagen. Mi análisis de la imagen dice:
'{analysis_text}'

El texto que el usuario escribió junto a la imagen (caption) es:
'{caption}'

Por favor, genera una respuesta amable y útil basada en AMBAS cosas.
"""
                response_text = self.nlu.get_chat_response(prompt)
                self._send_response(msg, response_text)
                
            except Exception as e:
                print(f"[ERROR IMAGEN] {e}")
                self._send_response(msg, "⚠️ Hubo un error al analizar la imagen.")

    def run(self):
        """Inicia el bot y lo mantiene corriendo."""
        print("✅ Bot (ModularBot) configurado. Iniciando polling...")
        while True:
            try:
                self.bot.polling(none_stop=True)
            except Exception as e:
                print(f"[ERROR GENERAL POLLING] {e}")
                print("Reiniciando en 5 segundos...")
                time.sleep(5)
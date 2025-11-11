# aida_bot/bot.py
import os
import time
from telebot import types 
from .services.speech_service import SpeechService
from .features.user_profiles import ProfileOnboarding
import json
from aida_bot import config
import re
import difflib
from aida_bot.features.user_profiles import ProfileOnboarding
from aida_bot.memory import ensure_profile, save_turn, build_llm_context


class SessionManager:
    """
    Manejo de sesiones de usuario (estado, configuración, contexto).
    Usa un cliente de almacenamiento para persistir los datos.
    """
    def __init__(self, storage_client):
        self.storage = storage_client
        self.local_cache = {} 

    def ensure(self, chat_id: int) -> dict:
        """
        Asegura que una sesión exista, cargándola desde el almacenamiento
        o creando una nueva con valores por defecto.
        """
        if chat_id in self.local_cache:
            return self.local_cache[chat_id]
        
        session_data = self.storage.get_session(chat_id)
        
        if not session_data:
            session_data = {
                "greeted": False, 
                "context": [],
                "responder_con_audio": True,
                "tts_voice": SpeechService.DEFAULT_VOICE
            }
            self.storage.save_session(chat_id, session_data)
        
        self.local_cache[chat_id] = session_data
        return session_data

    def save(self, chat_id: int, session_data: dict):
        """Guarda la sesión en el almacenamiento y actualiza la caché."""
        self.storage.save_session(chat_id, session_data)
        self.local_cache[chat_id] = session_data


class ModularBot:
    """Plantilla general del bot orientado a objetos."""
    
    # <--- MODIFICACIÓN 1: Añadir email_service al init ---
    def __init__(self, bot_instance, nlu, speech, vision, sentiment, sessions, storage_client, translator, email_service):
        self.bot = bot_instance
        self.nlu = nlu
        self.speech = speech
        self.vision = vision
        self.sentiment = sentiment
        self.email_service = email_service # <--- AÑADIDO
        self.sessions = sessions
        self.storage = storage_client
        self.translator = translator

        self._load_dataset()
        # Inicializa el manejador del formulario de bienvenida
        self.onboarding = ProfileOnboarding(bot_instance=self.bot, storage_client=self.storage)
        
        self._setup_handlers()
        print("✅ Bot modular listo y handlers configurados.")
    
    def _load_dataset(self):
        """Carga el conjunto de datos de respuestas predefinidas desde un archivo JSON."""
        self.dataset = {}
        try:
            # Construye una ruta absoluta al archivo dataset.json
            # __file__ es la ubicación de este archivo (bot.py)
            # os.path.dirname() obtiene el directorio (aida_bot)
            # os.path.join() une el directorio con el nombre del archivo
            current_dir = os.path.dirname(__file__)
            dataset_path = os.path.join(current_dir, 'storage', 'dataset.json')

            with open(dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convertimos la lista de JSON a un diccionario para búsqueda rápida
                for item in data:
                    normalized_question = re.sub(r'[^\w\s]', '', item['question']).lower().strip()
                    self.dataset[normalized_question] = item['answer']
            print(f"✅ Dataset cargado correctamente desde '{dataset_path}'.")
        except FileNotFoundError:
            print(f"⚠️ Advertencia: No se encontró el archivo de dataset en '{dataset_path}'. El bot funcionará sin respuestas predefinidas.")
        except json.JSONDecodeError:
            print(f"❌ Error: El archivo de dataset en '{dataset_path}' no es un JSON válido.")

    def _find_similar_question(self, user_question: str, threshold: float = 0.65) -> str | None:
        """
        Busca una pregunta similar en el dataset usando el coeficiente de similitud.
        Retorna la respuesta correspondiente si encuentra una pregunta con una similitud
        superior al umbral definido.
        """
        if not self.dataset:
            return None

        best_match_score = 0.0
        best_match_answer = None

        for question, answer in self.dataset.items():
            similarity = difflib.SequenceMatcher(None, user_question, question).ratio()
            if similarity > best_match_score:
                best_match_score = similarity
                best_match_answer = answer

        return best_match_answer if best_match_score >= threshold else None

    def _send_response(self, msg, response_text: str):
        """
        Método centralizado para enviar respuestas.
        Primero envía el texto y luego, si está activado, el audio
        CON LA VOZ SELECCIONADA POR EL USUARIO.
        """
        self.bot.reply_to(msg, response_text, parse_mode="Markdown")
        
        session = self.sessions.ensure(msg.chat.id)
        
        if session.get("responder_con_audio", True):
            # Lógica de voz corregida:
            # 1. Intentar detectar la voz automáticamente según el idioma de la RESPUESTA.
            current_voice = self.speech.get_voice_for_text(response_text)
            
            # 2. Si no se pudo determinar una voz (porque el idioma no es soportado),
            #    usar la voz guardada por el usuario como fallback.
            if not current_voice:
                current_voice = session.get("tts_voice", SpeechService.DEFAULT_VOICE)

            self.bot.send_chat_action(msg.chat.id, "record_voice")
            audio_path = self.speech.synthesize(response_text, current_voice)
            
            if audio_path:
                try:
                    with open(audio_path, 'rb') as audio_file:
                        self.bot.send_voice(msg.chat.id, audio_file)
                finally:
                    if os.path.exists(audio_path):
                        os.remove(audio_path)

    def _process_user_message(self, msg, user_text: str):
        """
        Procesa el texto del usuario, detectando *múltiples* intenciones 
        y ejecutando un plan de acción.
        """
        session = self.sessions.ensure(msg.chat.id)
        
        # 1. Detectar todas las intenciones
        intent_data = self.nlu.detect_intent(user_text)
        
        config_actions = intent_data.get("configuration", {})
        analysis_actions = intent_data.get("analysis_required", {})
        has_chat = intent_data.get("has_chat_intent", True)
        chat_content = intent_data.get("chat_content", user_text if has_chat else "")

        # 2. Ejecutar acciones de configuración (siempre primero)
        config_responses = [] 

        if config_actions.get("set_audio") == "OFF":
            if session["responder_con_audio"]: 
                session["responder_con_audio"] = False
                self.sessions.save(msg.chat.id, session)
                config_responses.append("Entendido. A partir de ahora, solo te responderé con texto. 👍")

        elif config_actions.get("set_audio") == "ON":
            if not session["responder_con_audio"]: 
                session["responder_con_audio"] = True
                self.sessions.save(msg.chat.id, session)
                config_responses.append("¡Hecho! Volveré a enviarte las respuestas en audio además del texto. 🔊")

        if config_actions.get("set_voice"):
            voice_id = config_actions["set_voice"]
            if voice_id in self.speech.VOICES.values():
                if session["tts_voice"] != voice_id: 
                    session["tts_voice"] = voice_id
                    self.sessions.save(msg.chat.id, session)
                    friendly_name = next((name for name, id_ in self.speech.VOICES.items() if id_ == voice_id), "desconocida")
                    config_responses.append(f"¡Perfecto! He cambiado mi voz a {friendly_name}. 🎤")
            else:
                config_responses.append(f"Hmm, no pude reconocer la voz '{voice_id}'.")

        # 3. Enviar respuestas de configuración (si las hubo)
        for response in config_responses:
            self._send_response(msg, response)

        # 4. Ejecutar análisis y chat (si aplica)
        prompt_adicional = ""
        
        # Si el NLU pide análisis de sentimiento
        if analysis_actions.get("sentiment") and chat_content:
            self.bot.send_chat_action(msg.chat.id, "typing")
            
            # 4.1. Analizar el sentimiento
            sentimiento = self.sentiment.analyze(chat_content)
            
            # 4.2. Formatear y ENVIAR el mensaje de feedback 
            sentiment_feedback = self.sentiment.format_analysis(sentimiento)
            if sentiment_feedback:
                self.bot.send_message(msg.chat.id, sentiment_feedback)
            
            # 4.3. Preparar el prompt adicional para el LLM
            if sentimiento['label'] == 'NEG' and sentimiento['score'] > 0.6:
                prompt_adicional = " (El usuario parece frustrado o enojado. Responde con extra paciencia y empatía)."
            elif sentimiento['label'] == 'POS' and sentimiento['score'] > 0.8:
                prompt_adicional = " (El usuario parece feliz o agradecido. Responde con calidez)."

        # 5. Ejecutar el chat (si aplica)
        if has_chat and chat_content:
            self.bot.send_chat_action(msg.chat.id, "typing")
            
            # Normalizar el texto del usuario para la búsqueda en el dataset
            normalized_text = re.sub(r'[^\w\s]', '', chat_content).lower().strip()

            # 5.1. Buscar respuesta exacta o similar en el dataset local primero
            response_text = self._find_similar_question(normalized_text, threshold=0.75)

            # 5.2. Si no se encuentra, usar el NLU
            if response_text is None:
                final_prompt = f"{chat_content}{prompt_adicional}"
                response_text = self.nlu.get_response(
                    final_prompt,
                    user_id=msg.chat.id,
                    user_name=getattr(msg.from_user, "first_name", "") or getattr(msg.chat, "first_name", "")
                    )
            
            self._send_response(msg, response_text)


    def _setup_handlers(self):
        
        # <--- MODIFICACIÓN 2: Usar el handle_start de "botfinal" ---
        @self.bot.message_handler(commands=["start"])
        def handle_start(msg):
            user_id = msg.from_user.id
            profile = self.storage.get_profile(user_id)
            
            if profile is not None: 
                uid = msg.chat.id
                profile = self.storage.get_profile(uid) or {}
                required = ("autonomia", "foco", "entorno")
                missing = any(k not in profile or not profile[k] for k in required)

            if missing:
                # Lanzar formulario de onboarding
                self.onboarding.start_onboarding(msg, force_retry=True)
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Actualizar mis preferencias", callback_data="start_onboarding_retry"))
                self.bot.reply_to(
                    msg,
                    "¡Hola de nuevo! Ya te conozco. 😊 ¿En qué te puedo ayudar hoy?",
                    reply_markup=markup
                )

        @self.bot.callback_query_handler(func=lambda query: True)
        def handle_callback_query(query):
            """Maneja todos los clics de botones en el bot."""
            
            # Si es un botón del formulario
            if query.data.startswith("onboarding_"):
                self.onboarding.handle_callback(query)
                return
            
            # Si es el botón de repetir el formulario
            if query.data == "start_onboarding_retry":
                self.bot.answer_callback_query(query.id, "Entendido, empecemos de nuevo.")
                try:
                    self.bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=None)
                except Exception:
                    pass 
                
                self.onboarding.start_onboarding(query.message, force_retry=True)
                return

            self.bot.answer_callback_query(query.id, "Callback desconocido")

        # <--- MODIFICACIÓN 3: Lógica de texto fusionada ---
        @self.bot.message_handler(content_types=["text"])
        def handle_text(msg):
            if msg.text.startswith('/'):
                return  # ignorar comandos

            uid = msg.chat.id
            profile = self.storage.get_profile(uid) or {}

            # --- Lógica de Onboarding (de botfinal) ---
            # 1. Si el usuario está respondiendo al formulario (ej. dando su nombre o email)
            if profile.get("esperando_nombre") or profile.get("esperando_contacto"):
                self.onboarding.handle_text_response(msg)
                return # Detener aquí, no es un chat normal

            # --- Lógica de "perfil incompleto" (de rama_memoria) ---
            # 2. Si el usuario no ha completado el formulario inicial
            required = ("autonomia", "foco", "entorno")
            missing = any(k not in profile or not profile[k] for k in required)
            if missing:
                self.onboarding.start_onboarding(msg, force_retry=False)
                return

            # --- Flujo normal (de rama_memoria) ---
            # 3. Perfil OK → sigue el flujo normal
            self._process_user_message(msg, msg.text)

            # --- Lógica de Alertas (de botfinal) ---
            # 4. Verificar si el mensaje contiene palabras de alerta
            if self.sentiment.check_for_alert(msg.text):
                email_destino = profile.get("contacto_emergencia")
                if email_destino and self.email_service:
                    motivo_alerta = "Palabras potencialmente peligrosas detectadas en el chat."
                    profile_data = self.storage.get_profile(uid) # Re-obtener datos
                    self.email_service.send_alert(email_destino, uid, motivo_alerta, profile_data)

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
                self.bot.reply_to(msg, "⚠️ Ocurrió un error al procesar tu audio.")

        @self.bot.message_handler(content_types=["photo"])
        def handle_photo(msg):
            self.bot.send_chat_action(msg.chat.id, "upload_photo")
            try:
                file_id = msg.photo[-1].file_id
                file_info = self.bot.get_file(file_id)
                image_bytes = self.bot.download_file(file_info.file_path)
                
                self.bot.send_chat_action(msg.chat.id, "typing")
                
                description = self.vision.analyze_image(image_bytes, msg.caption)
                
                self._send_response(msg, description)
                
            except Exception as e:
                print(f"[ERROR IMAGEN] {e}")
                self.bot.reply_to(msg, "⚠️ Ocurrió un error al analizar la imagen.")

    def run(self):
        print("✅ Bot iniciado. Escuchando mensajes...")
        while True:
            try:
                self.bot.polling(none_stop=True)
            except Exception as e:
                print(f"[ERROR GENERAL POLLING] {e}")
                print("Reiniciando en 10 segundos...")
                time.sleep(10)
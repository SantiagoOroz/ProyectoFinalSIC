# bot_poo.py
import requests
import whisper
import torch
import os
from tempfile import NamedTemporaryFile

# texto-a-voz
import asyncio
import edge_tts
from pydub import AudioSegment
# ---------------------------------------------
responder_con_audio = True
# ----------------------------
# --- ID de las voces en español que podés usar ---
# Encontrarás muchas más si buscás en la lista completa.
VOICE_ES_AR = "es-AR-ElenaNeural"        # Argentina (Femenina)
VOICE_ES_MX = "es-MX-DaliaNeural"        # México (Femenina)
VOICE_ES_ES = "es-ES-ElviraNeural"       # España (Femenina)
VOICE_ES_CO = "es-CO-SalomeNeural"       # Colombia (Femenina)
VOICE_ES_AR_M = "es-AR-TomasNeural"      # Argentina (Masculina)
# ----------------------------

class SpeechService:
    """Maneja audio (voz a texto, texto a voz) usando Whisper y Edge-TTS."""
    def __init__(self, model_size="base"):
        """
        Carga el modelo Whisper al iniciar.
        """
        print(f"Cargando el modelo Whisper '{model_size}'...")
        self.model = whisper.load_model(model_size)
        self.language = "es" # Idioma
        self.default_tts_voice = VOICE_ES_AR # Voz por defecto
    
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

    
    def synthesize(self, text: str, output_filename: str = "response_audio") -> str | None:
        """
        Sintetiza texto a un archivo de audio .ogg usando edge-tts.
        Retorna el audio que fue almacenado de manera temporal.
        """
        async def _async_synthesize():
            """Función interna asíncrona para manejar la generación de audio."""
            mp3_path = f"{output_filename}.mp3"
            ogg_path = f"{output_filename}.ogg"
            
            try:
                communicate = edge_tts.Communicate(text, self.default_tts_voice)
                await communicate.save(mp3_path)

                audio = AudioSegment.from_mp3(mp3_path)
                audio.export(ogg_path, format="ogg", codec="libopus")
                
                return ogg_path
            except Exception as e:
                print(f"[ERROR TTS] No se pudo sintetizar el audio: {e}")
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
            self.sessions[chat_id] = {"greeted": False, "context": []}
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
        Primero envía el texto y luego, si está activado, el audio.
        """
        # 1. Enviar siempre la respuesta como texto
        self.bot.reply_to(msg, response_text)
        
        # 2. Si la opción global está activada, sintetizar y enviar el audio
        if responder_con_audio:
            self.bot.send_chat_action(msg.chat.id, "record_voice")
            audio_path = self.speech.synthesize(response_text)
            if audio_path:
                try:
                    with open(audio_path, 'rb') as audio_file:
                        self.bot.send_voice(msg.chat.id, audio_file)
                finally:
                    # Nos aseguramos de borrar el archivo temporal
                    os.remove(audio_path)

    def _setup_handlers(self):
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
            self.bot.send_chat_action(msg.chat.id, "typing")
            response_text = self.nlu.get_response(msg.text)
            self._send_response(msg, response_text)

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
                    
                    response_text = self.nlu.get_response(transcribed_text)
                    self._send_response(msg, response_text)
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
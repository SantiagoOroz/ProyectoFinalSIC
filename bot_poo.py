import requests

class SpeechService:
    """Maneja audio (voz a texto, texto a voz)."""
    def transcribe(self, audio_bytes: bytes):
        return "Transcripción simulada del audio"

    def synthesize(self, text: str):
        return None


class VisionService:
    """Procesamiento de imágenes (OCR, reconocimiento, detección, etc.)."""
    def analyze_image(self, image_bytes: bytes):
        return "Texto o descripción detectada en la imagen"


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
                # Extrae el contenido generado por la IA
                respuesta = resp.json()['choices'][0]['message']['content']
                return respuesta.strip()
            else:
                # Manejo de errores de la API
                error_info = resp.json().get('error', {}).get('message', 'Error desconocido.')
                return f" [Error IA {resp.status_code}] No pude generar una respuesta."
        
        except requests.exceptions.RequestException as e:
            # Manejo de errores de conexión o timeout
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

    def _setup_handlers(self):
        @self.bot.message_handler(commands=["start"])
        def handle_start(msg):
            session = self.sessions.ensure(msg.chat.id)
            if not session["greeted"]:
                welcome = "👋 ¡Hola! Soy tu asistente digital. Enviame texto, audio o fotos para empezar 🚀"
                self.bot.reply_to(msg, welcome)
                session["greeted"] = True
            else:
                self.bot.reply_to(msg, "Ya estamos en marcha 😊")

        @self.bot.message_handler(content_types=["text"])
        def handle_text(msg):
            self.bot.send_chat_action(msg.chat.id, "typing")
            response = self.nlu.get_response(msg.text)
            self.bot.reply_to(msg, response)

        @self.bot.message_handler(content_types=["voice"])
        def handle_voice(msg):
            self.bot.send_chat_action(msg.chat.id, "typing")
            try:
                file_info = self.bot.get_file(msg.voice.file_id)
                audio_bytes = self.bot.download_file(file_info.file_path)
                text = self.speech.transcribe(audio_bytes)
                response = self.nlu.get_response(text)
                self.bot.reply_to(msg, response)
            except Exception as e:
                print(f"[ERROR VOZ] {e}")
                self.bot.reply_to(msg, "⚠️ No pude procesar tu audio.")

        @self.bot.message_handler(content_types=["photo"])
        def handle_photo(msg):
            self.bot.send_chat_action(msg.chat.id, "upload_photo")
            try:
                file_id = msg.photo[-1].file_id
                file_info = self.bot.get_file(file_id)
                image_bytes = self.bot.download_file(file_info.file_path)
                description = self.vision.analyze_image(image_bytes)
                response = self.nlu.get_response(f"Imagen detectada: {description}")
                self.bot.reply_to(msg, response)
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

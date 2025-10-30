import requests
from transformers import pipeline
import json
import time
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

class SentimentAnalyzer:
    """Analiza el sentimiento de un texto usando transformers."""
    def __init__(self, model_name="pysentimiento/robertuito-sentiment-analysis"):
        print("🔄 Cargando modelo de análisis de sentimiento...")
        self.analyzer = pipeline("sentiment-analysis", model=model_name)
        print("✅ Modelo de sentimiento cargado.")

    def analyze(self, text: str) -> str:
        result = self.analyzer(text)[0]
        sentimiento = result['label']
        confianza = result['score']

        emoji = "❓"
        if sentimiento == "POS":
            emoji = "😊"
        elif sentimiento == "NEG":
            emoji = "😟"
        elif sentimiento == "NEU":
            emoji = "😐"

        return f"Sentimiento: {sentimiento} {emoji} (Confianza: {confianza:.2%})"
    
class NLUService:
    """Procesamiento del lenguaje natural (respuestas inteligentes)."""
    def __init__(self, api_key, api_url, system_prompt="Eres un asistente digital paciente y claro que enseña a personas mayores a usar tecnología. Explica las cosas paso a paso, con ejemplos sencillos, sin tecnicismos y usando un tono amable y alentador."):
        self.system_prompt = system_prompt
        self.api_key = api_key
        self.api_url = api_url
        self.model = "llama3-70b-8192"

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
                error_info = resp.json().get('error', {}).get('message', resp.text)
                return f"[Error IA {resp.status_code}] No pude generar una respuesta. Detalle: {error_info}"
        
        except requests.exceptions.RequestException as e:
            # Manejo de errores de conexión o timeout
            return f" [Error Conexión Groq] No pude contactar al servicio de IA. ¿Estás conectado a internet? ({e})"

class SessionManager:
    """Manejo de sesiones de usuario (estado, configuración, contexto)."""
    def __init__(self):
        self.sessions = {}

    def ensure(self, chat_id: int):
        if chat_id not in self.sessions:
            self.sessions[chat_id] = {"greeted": False, "context": [], "message_history": []}
        return self.sessions[chat_id]


class ModularBot:
    """Plantilla general del bot orientado a objetos."""
    def __init__(self, bot_instance, nlu, speech, vision, sentiment, sessions):
        self.bot = bot_instance
        self.nlu = nlu
        self.speech = speech
        self.vision = vision
        self.sessions = sessions
        self.sentiment = sentiment
        self.alert_words = self._load_alert_words()
        self._setup_handlers()

    def _load_alert_words(self):
        """Carga las palabras de alerta desde el archivo JSON."""
        try:
            # Asegúrate de que la ruta al archivo JSON sea la correcta
            with open('c:\\AIDA\\ProyectoFinalSIC\\app\\sentimientos\\feel_list.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convertimos todas las palabras a minúsculas para una comparación insensible
                return [word.lower() for word in data.get("sentimientos_alerta", [])]
        except FileNotFoundError:
            print("⚠️  Error: El archivo 'feel_list.json' no se encontró.")
            return []
        except json.JSONDecodeError:
            print("⚠️  Error: El archivo 'feel_list.json' no es un JSON válido.")
            return []

    def _setup_handlers(self):
        @self.bot.message_handler(commands=["start"])
        def handle_start(msg):
            session = self.sessions.ensure(msg.chat.id)
        #     if not session["greeted"]:
        #         welcome = "👋 ¡Hola! Soy tu asistente digital. Podemos practicar juntos cosas como enviar correos, usar el celular, hacer videollamadas o aprender qué es una app. Escribime o mandame un audio para empezar 😊"
        #         self.bot.reply_to(msg, welcome)
        #         session["greeted"] = True
        #     else:
        #         self.bot.reply_to(msg, "¡Qué alegría volver a verte! ¿Seguimos aprendiendo algo nuevo hoy?")

        @self.bot.message_handler(commands=["sentimiento"])
        def handle_sentiment(msg):
             self.bot.send_chat_action(msg.chat.id, "typing")
             texto_para_analizar = msg.text.replace("/sentimiento", "").strip()
             if not texto_para_analizar:
                 self.bot.reply_to(msg, "Por favor, escribe una frase después del comando /sentimiento para que pueda analizarla. 😊")
                 return
             resultado = self.sentiment.analyze(texto_para_analizar)
             self.bot.reply_to(msg, resultado)

        @self.bot.message_handler(content_types=["text"])
        def handle_text(msg):
            # Ignorar comandos para que no sean procesados por esta función
            if msg.text.startswith('/'):
                return

            self.bot.send_chat_action(msg.chat.id, "typing")
            
            session = self.sessions.ensure(msg.chat.id)
            now = time.time()

            # 1. Añadir el mensaje actual al historial de la sesión
            session["message_history"].append({"text": msg.text, "timestamp": now})

            # 2. Filtrar mensajes que tengan más de 12 horas (12 * 3600 segundos)
            twelve_hours_ago = now - (12 * 60 * 60)
            recent_messages = [m for m in session["message_history"] if m["timestamp"] > twelve_hours_ago]
            session["message_history"] = recent_messages  # Actualizar el historial

            # 3. Contar palabras de alerta en todo el historial reciente
            full_text_lower = " ".join([m["text"] for m in recent_messages]).lower()
            alert_count = sum(1 for word in self.alert_words if word in full_text_lower)

            # 4. Si el conteo de alertas en el chat reciente es 5 o más, activar el análisis
            if alert_count >= 5:
                resultado_sentimiento = self.sentiment.analyze(msg.text)
                self.bot.reply_to(msg, resultado_sentimiento)
                session["message_history"] = [] # Limpiar historial después de la alerta para no repetir
            else:
                response = self.nlu.get_response(msg.text)
                self.bot.reply_to(msg, response)

        # @self.bot.message_handler(content_types=["voice"])
        # def handle_voice(msg):
        #     self.bot.send_chat_action(msg.chat.id, "typing")
        #     try:
        #         file_info = self.bot.get_file(msg.voice.file_id)
        #         audio_bytes = self.bot.download_file(file_info.file_path)
        #         text = self.speech.transcribe(audio_bytes)
        #         response = self.nlu.get_response(text)
        #         self.bot.reply_to(msg, response)
        #     except Exception as e:
        #         print(f"[ERROR VOZ] {e}")
        #         self.bot.reply_to(msg, "⚠️ No pude procesar tu audio.")

        # @self.bot.message_handler(content_types=["photo"])
        # def handle_photo(msg):
        #     self.bot.send_chat_action(msg.chat.id, "upload_photo")
        #     try:
        #         file_id = msg.photo[-1].file_id
        #         file_info = self.bot.get_file(file_id)
        #         image_bytes = self.bot.download_file(file_info.file_path)
        #         description = self.vision.analyze_image(image_bytes)
        #         response = self.nlu.get_response(f"Imagen detectada: {description}")
        #         self.bot.reply_to(msg, response)
        #     except Exception as e:
        #         print(f"[ERROR IMAGEN] {e}")
        #         self.bot.reply_to(msg, "⚠️ No pude analizar la imagen.")

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

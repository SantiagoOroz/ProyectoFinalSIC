import telebot
import os
from dotenv import load_dotenv
from bot_poo import SpeechService, VisionService, NLUService, SentimentAnalyzer, SessionManager, ModularBot

# Cargar variables de entorno
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ Falta TELEGRAM_TOKEN en el archivo .env")
if not GROQ_API_KEY:
    raise ValueError("❌ Falta GROQ_API_KEY en el archivo .env")

# Instancia del bot de Telegram
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Crear los objetos 
nlu = NLUService(
    api_key=GROQ_API_KEY,
    api_url=GROQ_API_URL,
    system_prompt="Eres un asistente digital paciente y claro que enseña a personas mayores a usar tecnología. Explica las cosas paso a paso, con ejemplos sencillos, sin tecnicismos y usando un tono amable y alentador."
)
speech = SpeechService()
vision = VisionService()
sentiment = SentimentAnalyzer()
sessions = SessionManager()


# Crear la instancia principal del bot 
general_bot = ModularBot(bot, nlu, speech, vision,sentiment, sessions)

# Ejecutar el bot
general_bot.run()

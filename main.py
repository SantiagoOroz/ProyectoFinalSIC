import telebot
import os
from dotenv import load_dotenv
from bot_poo import SpeechService, VisionService, NLUService, SessionManager, ModularBot

# Cargar variables de entorno
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
GROQ_API_URL = os.getenv("GROQ_API_URL", '''URL''' )

if not TELEGRAM_TOKEN:
    raise ValueError("❌ Falta TELEGRAM_TOKEN en el archivo .env")
if not GROQ_API_KEY:
    raise ValueError("❌ Falta GROQ_API_KEY en el archivo .env")

# Instancia del bot de Telegram
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Crear los objetos 
nlu = NLUService(
    api_key=GROQ_API_KEY,          # <-- ¡Pasamos la clave!
    api_url=GROQ_API_URL,          # <-- ¡Pasamos la URL!
    system_prompt="Eres un asistente general amable y claro.")
speech = SpeechService()
vision = VisionService()
sessions = SessionManager()

# Crear la instancia principal del bot 
general_bot = ModularBot(bot, nlu, speech, vision, sessions)

# Ejecutar el bot
general_bot.run()

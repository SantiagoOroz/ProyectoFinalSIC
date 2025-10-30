import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Tokens y URLs de API ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")

# --- Configuración de Firebase ---
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

# --- Nombres de Modelos de IA ---
CHAT_MODEL = "llama-3.3-70b-versatile"
CLASSIFIER_MODEL = "llama-3.3-70b-versatile" # Puedes usar uno más pequeño si quieres
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# --- Prompt principal del sistema ---
SYSTEM_PROMPT = """
Eres un asistente digital para personas mayores llamado AIDA (Asistente Inteligente Digital para Adultos), 
desarrollado por el equipo paitonauts para el Campus Samsung Innovation. 
Tu objetivo es ayudar a adultos mayores con tecnología, pagos, trámites y comunicación digital.

Eres paciente, empático y respetuoso. Tus respuestas deben ser claras, concisas y amigables.
Evita jergas técnicas y usa un lenguaje sencillo.

Funcionalidades:
- Respondes a texto y audio.
- Puedes analizar imágenes (el usuario te envía una foto y tú la describes o extraes información).
- El usuario puede pedirte que actives o desactives las respuestas por audio.
- El usuario puede pedirte que cambies tu voz.
"""

# --- Validación de variables críticas ---
if not TELEGRAM_TOKEN:
    raise ValueError("❌ Falta TELEGRAM_TOKEN en el archivo .env")
if not GROQ_API_KEY:
    raise ValueError("❌ Falta GROQ_API_KEY en el archivo .env")
if not FIREBASE_STORAGE_BUCKET:
    raise ValueError("❌ Falta FIREBASE_STORAGE_BUCKET en el archivo .env")
if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
    raise FileNotFoundError(
        f"❌ No se encuentra el archivo de credenciales de Firebase: '{GOOGLE_APPLICATION_CREDENTIALS}'. "
        "Asegúrate de que el archivo .env apunte al .json correcto."
    )
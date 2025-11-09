# aida_bot/config.py
import os
from dotenv import load_dotenv

# Carga el archivo .env
load_dotenv()

# --- Tokens y APIs Requeridas ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")

# --- Modelos de IA ---
NLU_MODEL = "llama-3.3-70b-versatile" # Modelo rápido para chat
INTENT_MODEL = "llama-3.3-70b-versatile" # Modelo rápido para clasificación
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct" # Modelo potente para visión

# --- Configuración Opcional de Base de Datos ---
# Busca el archivo de credenciales de Google
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

# Variable booleana para saber si usamos la nube
USE_CLOUD_STORAGE = (GOOGLE_CREDENTIALS_PATH and os.path.exists(GOOGLE_CREDENTIALS_PATH))

# --- Validación de Configuración ---
if not TELEGRAM_TOKEN:
    raise ValueError("❌ Falta TELEGRAM_TOKEN en el archivo .env")
if not GROQ_API_KEY:
    raise ValueError("❌ Falta GROQ_API_KEY en el archivo .env")

print("✅ Configuración cargada.")
if USE_CLOUD_STORAGE:
    print(f"☁️ Usando Firebase Cloud Storage (encontrado: {GOOGLE_CREDENTIALS_PATH})")
else:
    print("📁 Usando almacenamiento JSON local (no se encontró GOOGLE_APPLICATION_CREDENTIALS).")
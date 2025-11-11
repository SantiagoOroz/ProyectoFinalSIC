# aida_bot/config.py
from pathlib import Path
import os
from dotenv import load_dotenv

# --- Cargar .env ---
load_dotenv()

# --- Identidad / Namespacing ---
ENV = os.getenv("ENV", "dev")
BOT_ID = os.getenv("BOT_ID", "aida_local")
NAMESPACE = f"{ENV}:{BOT_ID}"

# --- Tokens y APIs ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL") # <--- AÑADIR ESTA LÍNEA

# --- Modelos (Groq) ---
# Nota: llama3-8b-8192 fue deprecado
NLU_MODEL = os.getenv("NLU_MODEL", "llama-3.1-8b-instant")
INTENT_MODEL = os.getenv("INTENT_MODEL", NLU_MODEL)
VISION_MODEL = os.getenv("VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

# --- Storage ---
USE_CLOUD_STORAGE = os.getenv("USE_CLOUD_STORAGE", "False").lower() == "true"

# Resolver ruta ABSOLUTA para la credencial de Firebase
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # carpeta .../ProyectoFinalSIC
_raw_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "aida_bot/serviceAccountKey.json")
if os.path.isabs(_raw_path):
    GOOGLE_CREDENTIALS_PATH = _raw_path
else:
    GOOGLE_CREDENTIALS_PATH = str((PROJECT_ROOT / _raw_path).resolve())

# --- Validaciones mínimas ---
if not TELEGRAM_TOKEN:
    raise ValueError("❌ Falta TELEGRAM_TOKEN en el archivo .env")
if not GROQ_API_KEY:
    raise ValueError("❌ Falta GROQ_API_KEY en el archivo .env")

# --- Log de arranque claro ---
print("✅ Configuración cargada.")
if USE_CLOUD_STORAGE:
    cred_exists = Path(GOOGLE_CREDENTIALS_PATH).exists()
    if cred_exists:
        print(f"☁️ Storage: Firebase (credencial: {GOOGLE_CREDENTIALS_PATH})")
    else:
        print(f"⚠️ USE_CLOUD_STORAGE=True, pero NO existe la credencial en: {GOOGLE_CREDENTIALS_PATH}")
        print("    Se usará JSON local si get_storage_client() no encuentra la credencial.")
else:
    print("💾 Storage: JSON local (USE_CLOUD_STORAGE=False)")

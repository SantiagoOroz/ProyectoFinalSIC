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
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

# --- Modelos (Groq) ---
NLU_MODEL = os.getenv("NLU_MODEL", "llama-3.3-70b-versatile")
INTENT_MODEL = os.getenv("INTENT_MODEL", NLU_MODEL)
VISION_MODEL = os.getenv("VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

# Resolver ruta ABSOLUTA para la credencial de Firebase
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # carpeta .../ProyectoFinalSIC
_raw_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")
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
cred_exists = Path(GOOGLE_CREDENTIALS_PATH).exists()
if cred_exists:
    print(f"☁️ Storage: Firebase (credencial: {GOOGLE_CREDENTIALS_PATH})")
else:
    print(f"NO existe la credencial en: {GOOGLE_CREDENTIALS_PATH}")
    print("    Se usará JSON local, get_storage_client() no encuentra la credencial.")

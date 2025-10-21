import telebot
import os
import time
import uuid
from io import BytesIO
from groq import Groq
from supabase import create_client, Client
from dotenv import load_dotenv
from funciones import BotResponder

# Cargar variables de entorno
load_dotenv(r"C:\AIDA\ProyectoFinalSIC\.env")

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "images")

if not all([TELEGRAM_BOT_TOKEN, GROQ_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    raise RuntimeError("Faltan variables de entorno requeridas.")

# Inicializar clientes
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
responder = BotResponder(groq_client, supabase)
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# ---------------- UTILIDADES ----------------
def get_photo_bytes(message):
    """Descarga la foto de mayor resolución enviada por Telegram."""
    if getattr(message, "photo", None):
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        return bot.download_file(file_info.file_path)
    if getattr(message, "document", None) and getattr(message.document, "mime_type", "").startswith("image"):
        file_info = bot.get_file(message.document.file_id)
        return bot.download_file(file_info.file_path)
    raise ValueError("No se encontró una imagen en el mensaje")

import tempfile

def upload_supabase_get_signed_url(img_bytes, bucket=SUPABASE_BUCKET, expires_in=3600):
    file_name = f"{int(time.time())}_{uuid.uuid4().hex}.jpg"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        supabase.storage.from_(bucket).upload(
            file_name,
            tmp_path,  # <-- ruta del archivo temporal
            {"content-type": "image/jpeg"}
        )
    except Exception as e:
        raise RuntimeError(f"Error subiendo la imagen a Supabase: {e}")

    try:
        signed = supabase.storage.from_(bucket).create_signed_url(file_name, expires_in)
        if isinstance(signed, dict):
            return signed.get("signedURL") or signed.get("signed_url") or signed.get("signedUrl")
        return str(signed)
    except Exception:
        pub = supabase.storage.from_(bucket).get_public_url(file_name)
        if isinstance(pub, dict):
            return pub.get("publicURL") or pub.get("public_url") or pub.get("publicUrl")
        return str(pub)

# ---------------- OCR ----------------
import re
from typing import Optional

FECHA_RE = re.compile(
    r"(?:(?:vence|vencimiento|caduca)\s*[:\-]?\s*)?(\d{1,2})[\/\-\.\s](\d{1,2})[\/\-\.\s](\d{2,4})",
    re.IGNORECASE,
)

def groq_ocr(image_url: str, groq_client, model: str) -> str:
    """OCR con Groq: devuelve SOLO el texto detectado."""
    comp = groq_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Devuelve SOLO el texto reconocido de la imagen, sin comentarios."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extrae el texto visible (OCR)."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        temperature=0.0,
        max_tokens=500,
    )
    return comp.choices[0].message.content.strip()

def ocr_find_expiry_date(ocr_text: str) -> Optional[str]:
    """Busca fechas tipo DD/MM/YYYY en texto OCR."""
    for m in FECHA_RE.finditer(ocr_text):
        d, mth, y = m.groups()
        y = y if len(y) == 4 else f"20{y}"
        try:
            dd = f"{int(d):02d}"
            mm = f"{int(mth):02d}"
            yyyy = str(int(y))
            return f"{dd}/{mm}/{yyyy}"
        except Exception:
            continue
    return None

# ---------------- HANDLER ----------------
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, "typing")
    try:
        img_bytes = get_photo_bytes(message)
        url = upload_supabase_get_signed_url(img_bytes)
        caption = (message.caption or "").strip().lower()

        # si mencionan "vencimiento" → OCR
        if any(k in caption for k in ["vence", "vencimiento", "fecha vence", "caduca"]):
            ocr_text = groq_ocr(url, groq_client, GROQ_MODEL)
            fecha = ocr_find_expiry_date(ocr_text)
            answer = f"Vence: {fecha}" if fecha else "No visible"
            bot.reply_to(message, answer)
            return

        # caso general: ruteo conciso
        answer = responder.route_image(url, caption, chat_id)
        bot.reply_to(message, answer[:4000])

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("Bot corriendo (Supabase + Groq)…")
    bot.infinity_polling(skip_pending=True, timeout=60)

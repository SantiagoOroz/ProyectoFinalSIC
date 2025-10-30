from __future__ import annotations
import re
import datetime
from typing import Optional

class BotResponder:
    """
    Encapsula la lógica de respuestas concisas y el ruteo por intención.
    Se inyectan los clientes que ya creaste en modelo.py (groq_client y supabase).
    """
    def __init__(self, groq_client, supabase=None):
        self.groq = groq_client
        self.db = supabase
        self.MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

    # -------- INTENTS --------
    def detect_intent_local(self, text: str) -> str:
        t = (text or "").lower()
        if any(k in t for k in ["qué comida", "que comida", "qué es esto", "que es esto", "qué alimento"]):
            return "identify_food"
        if any(k in t for k in ["vence", "vencimiento", "fecha vence", "caduca"]):
            return "expiry_date"
        if any(k in t for k in ["pagar", "pago ahora", "quiero pagar"]):
            return "ask_pay"
        if any(k in t for k in ["recordar", "recuérdame", "recordame", "recordatorio"]):
            return "set_reminder"
        if any(k in t for k in ["qué es", "describe", "qué hay", "que hay"]):
            return "describe_image"
        return "other"

    # -------- CORE: llamada concisa a Groq --------
    def _groq_concise(self, image_url: str, user_text: str, max_tokens: int = 24) -> str:
        system = (
            "Eres un asistente extremadamente conciso. "
            "Devuelve 1–3 palabras si te piden identificar algo (p. ej., comida u objeto). "
            "En otros casos responde en 1–2 frases como máximo. "
            "No uses listas, viñetas ni markdown. Si no sabes, responde 'desconocido'."
        )
        comp = self.groq.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
            temperature=0.0,
            max_tokens=max_tokens,
            top_p=1.0,
        )
        return comp.choices[0].message.content.strip()

    # -------- Handlers por intención --------
    def identify_food(self, image_url: str) -> str:
        return self._groq_concise(
            image_url,
            "¿Qué comida es? Responde SOLO con el nombre en español (1–3 palabras).",
            max_tokens=6,
        )

    def describe_image(self, image_url: str) -> str:
        return self._groq_concise(
            image_url,
            "Describe brevemente lo más importante en 1–2 frases, sin listas ni markdown.",
            max_tokens=30,
        )

    def expiry_date(self, image_url: str) -> str:
        return self._groq_concise(
            image_url,
            "Extrae la fecha de vencimiento visible en la imagen. "
            "Responde exactamente: 'Vence: DD/MM/YYYY' o 'No visible'.",
            max_tokens=12,
        )

    def ask_pay(self, image_url: str) -> str:
        return "¿Querés pagar ahora? (Sí/No)"

    def set_reminder(self, user_text: str, chat_id: int) -> str:
        m = re.search(r"(\d{1,2})[\/\-](\d{1,2})(?:[\/\-](\d{2,4}))?", user_text)
        if not m:
            return "¿Qué fecha querés? (ej: 25/10)"
        d, mo, y = m.groups()
        y = y if y else str(datetime.datetime.now().year)
        date_str = f"{int(d):02d}/{int(mo):02d}/{y}"
        if self.db:
            try:
                self.db.table("reminders").insert(
                    {"chat_id": chat_id, "date": date_str, "note": user_text}
                ).execute()
            except Exception:
                pass
        return f"Recordatorio guardado: {date_str}"

    # -------- Router principal --------
    def route_image(self, image_url: str, caption: Optional[str], chat_id: int) -> str:
        intent = self.detect_intent_local(caption or "")
        if intent == "identify_food":
            return self.identify_food(image_url)
        if intent == "expiry_date":
            return self.expiry_date(image_url)
        if intent == "ask_pay":
            return self.ask_pay(image_url)
        if intent == "set_reminder":
            return self.set_reminder(caption or "", chat_id)
        if intent == "describe_image":
            return self.describe_image(image_url)
        return self._groq_concise(
            image_url,
            "Resume lo más importante de la imagen en 1–2 frases (sin listas).",
            max_tokens=30,
        )

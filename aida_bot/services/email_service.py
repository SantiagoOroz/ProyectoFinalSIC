# aida_bot/services/email_service.py
import requests
from datetime import datetime
from .. import config


class EmailService:
    """
    Servicio encargado de enviar alertas a través de Make.com
    usando un webhook configurado en el archivo .env.
    """

    def __init__(self, webhook_url: str | None = None):
        # Usa la URL del .env si no se pasa manualmente
        self.webhook_url = webhook_url or config.MAKE_WEBHOOK_URL
        if not self.webhook_url:
            print("⚠️ ADVERTENCIA: No se ha configurado MAKE_WEBHOOK_URL en el archivo .env.")

    def send_alert(self, email_destino: str, user_id: int, motivo: str, profile_data: dict | None = None):
        """
        Envía una alerta a través de un webhook de Make.com.
        """
        if not self.webhook_url:
            print("⚠️ No se puede enviar la alerta: falta MAKE_WEBHOOK_URL.")
            return
        

        payload = {
            "email_destino": email_destino,
            "user_id": str(user_id),
            "motivo": motivo,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sistema": "AIDA - Asistente Digital para Adultos",
            "nombre_apellido": (profile_data.get("nombre_apellido") if profile_data else "No proporcionado")
        }

    

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            print(f"✅ Alerta enviada correctamente a {email_destino}. Payload: {payload}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error enviando alerta a Make: {e}")

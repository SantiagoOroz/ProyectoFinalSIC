# aida_bot/services/vision_service.py
import requests
import base64
import json
from .. import config

class VisionService:
    """Procesamiento de imágenes (OCR, reconocimiento, detección, etc.)."""
    
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model = config.VISION_MODEL
        print("✅ Servicio de Visión inicializado.")

    def _image_to_base64(self, image_bytes: bytes) -> str:
        """Convierte bytes de imagen a base64 para enviarla a Groq"""
        try:
            return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error al convertir imagen a base64: {e}")
            return ""

    def _build_prompt(self, user_caption: str | None) -> str:
        """
        Construye el prompt del sistema para el modelo de visión, 
        incluyendo la pregunta del usuario si existe.
        """
        
        base_prompt = """
Eres AIDA, un asistente empático, claro y paciente, diseñado para acompañar a personas mayores.
Tu objetivo es ayudarlos a entender lo que ven en una imagen.

📸 TAREA:
1.  **Describe la imagen**: Con claridad y amabilidad, describe lo que ves (colores, objetos, personas, acciones).
2.  **Lee el Texto (OCR)**: Si hay texto visible (fechas, precios, nombres, vencimientos, links), léelo y explícalo de manera simple.
3.  **Detecta Alertas**: Si la imagen parece un correo, mensaje o sitio falso (con errores ortográficos, direcciones web sospechosas o pedidos de datos personales), advierte al usuario con calma:
    👉 “Este mensaje parece ser un intento de fraude o phishing. No hagas clic en los enlaces ni ingreses tus datos personales. Si tenés dudas, contactá directamente al banco o empresa desde su página oficial.”
4.  **Responde la Pregunta**: Si el usuario hizo una pregunta (ej: 'cuándo vence esto?'), enfócate en responderla.

Usa un tono cálido y paciente.
"""
        
        if user_caption:
            return f"{base_prompt}\n\nConsulta específica del usuario: '{user_caption}'\n\nResponde a esta consulta basándote en la imagen."
        else:
            return f"{base_prompt}\n\nDescribe la imagen para el usuario."

    def analyze_image(self, image_bytes: bytes, user_caption: str | None = None) -> str:
        """
        Envía la imagen a Groq y obtiene la descripción.
        """
        image_b64 = self._image_to_base64(image_bytes)
        if not image_b64:
            return "No pude procesar la imagen."

        system_prompt = self._build_prompt(user_caption)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Aquí tienes la imagen."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1024
        }
        
        try:
            resp = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'].strip()
            else:
                return f"[Error IA {resp.status_code}] No pude analizar la imagen. {resp.text}"
        except requests.exceptions.RequestException as e:
            return f" [Error Conexión Groq] No pude contactar al servicio de IA. ({e})"
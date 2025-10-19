# app/data/db.py
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Cargar variables de entorno desde .env
load_dotenv()

# Ruta al JSON del service account (NO se commitea)
SA_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "app/service-account.json")

def get_db():
    """
    Devuelve un cliente de Firestore (singleton).
    Llama a get_db() donde necesites leer/escribir.
    """
    # Evita inicializar dos veces
    if not firebase_admin._apps:
        if not os.path.exists(SA_PATH):
            raise FileNotFoundError(
                f"No encuentro el service account en: {SA_PATH}. "
                "Asegurate de que .env tenga GOOGLE_APPLICATION_CREDENTIALS apuntando al JSON local."
            )
        cred = credentials.Certificate(SA_PATH)
        firebase_admin.initialize_app(cred)  # si usás Storage sin especificar bucket, configúralo en storage.py
    return firestore.client()

# Atajo opcional si te gusta usar 'db' directo:
db = get_db()

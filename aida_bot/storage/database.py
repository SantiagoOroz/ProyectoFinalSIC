import os
import firebase_admin
from firebase_admin import credentials, firestore
from aida_bot import config

_db_client = None

def get_db():
    """
    Inicializa y devuelve un cliente de Firestore (Singleton).
    """
    global _db_client
    if _db_client is not None:
        return _db_client

    # Evita inicializar dos veces
    if not firebase_admin._apps:
        if not os.path.exists(config.GOOGLE_APPLICATION_CREDENTIALS):
            raise FileNotFoundError(
                f"No encuentro el service account en: {config.GOOGLE_APPLICATION_CREDENTIALS}. "
                "Asegúrate de que .env tenga GOOGLE_APPLICATION_CREDENTIALS apuntando al JSON local."
            )
        
        cred_options = {
            'storageBucket': config.FIREBASE_STORAGE_BUCKET
        }
        cred = credentials.Certificate(config.GOOGLE_APPLICATION_CREDENTIALS)
        firebase_admin.initialize_app(cred, cred_options)
    
    _db_client = firestore.client()
    return _db_client
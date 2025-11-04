# aida_bot/storage/database.py
import json
import os
import firebase_admin
from firebase_admin import credentials, firestore
from abc import ABC, abstractmethod
from .. import config

# --- Interfaz de Almacenamiento ---

class AbstractStorage(ABC):
    """Define los métodos que cualquier sistema de almacenamiento debe tener."""
    
    @abstractmethod
    def get_session(self, chat_id: int) -> dict:
        pass
        
    @abstractmethod
    def save_session(self, chat_id: int, session_data: dict):
        pass
        
    @abstractmethod
    def get_profile(self, user_id: int) -> dict | None:
        pass
        
    @abstractmethod
    def save_profile(self, user_id: int, profile_data: dict):
        pass

# --- Implementación 1: Almacenamiento en JSON Local ---

class JSONStorage(AbstractStorage):
    """Implementación de almacenamiento usando un archivo JSON local."""
    
    def __init__(self, db_path="aida_data.json"):
        self.db_path = db_path
        self._load_db()

    def _load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {"sessions": {}, "profiles": {}}

    def _save_db(self):
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_session(self, chat_id: int) -> dict:
        return self.data["sessions"].get(str(chat_id), {})

    def save_session(self, chat_id: int, session_data: dict):
        self.data["sessions"][str(chat_id)] = session_data
        self._save_db()

    def get_profile(self, user_id: int) -> dict | None:
        return self.data["profiles"].get(str(user_id))

    def save_profile(self, user_id: int, profile_data: dict):
        self.data["profiles"][str(user_id)] = profile_data
        self._save_db()

# --- Implementación 2: Almacenamiento en Firebase ---

class FirebaseStorage(AbstractStorage):
    """Implementación de almacenamiento usando Google Firebase Firestore."""
    
    def __init__(self):
        cred = credentials.Certificate(config.GOOGLE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.sessions_col = self.db.collection("bot_sessions")
        self.profiles_col = self.db.collection("bot_profiles")

    def get_session(self, chat_id: int) -> dict:
        doc = self.sessions_col.document(str(chat_id)).get()
        if doc.exists:
            return doc.to_dict()
        return {}

    def save_session(self, chat_id: int, session_data: dict):
        self.sessions_col.document(str(chat_id)).set(session_data)

    def get_profile(self, user_id: int) -> dict | None:
        doc = self.profiles_col.document(str(user_id)).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def save_profile(self, user_id: int, profile_data: dict):
        self.profiles_col.document(str(user_id)).set(profile_data)

# --- Factory (Fábrica) ---

def get_storage_client() -> AbstractStorage:
    """
    Devuelve una instancia del cliente de almacenamiento apropiado
    basado en la configuración del proyecto.
    """
    if config.USE_CLOUD_STORAGE:
        return FirebaseStorage()
    else:
        return JSONStorage()
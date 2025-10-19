# app/data/storage.py
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, storage

load_dotenv()

SA_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "app/service-account.json")
# Si querés fijar el bucket explícitamente (recomendado):
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")  # ej: "tu-proyecto.appspot.com"

def _ensure_app():
    if not firebase_admin._apps:
        if not os.path.exists(SA_PATH):
            raise FileNotFoundError(
                f"No encuentro el service account en: {SA_PATH}. "
                "Configurá GOOGLE_APPLICATION_CREDENTIALS en .env."
            )
        cred = credentials.Certificate(SA_PATH)
        if FIREBASE_STORAGE_BUCKET:
            firebase_admin.initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET})
        else:
            firebase_admin.initialize_app(cred)

def _bucket():
    _ensure_app()
    if FIREBASE_STORAGE_BUCKET:
        return storage.bucket(FIREBASE_STORAGE_BUCKET)
    return storage.bucket()  # usa el default del proyecto

def upload_file(local_path: str, remote_path: str, make_public: bool = True) -> str:
    """
    Sube un archivo local a Firebase Storage.
    remote_path: ruta deseada en el bucket (p.ej. 'audios/user123/voz1.wav')
    Devuelve URL (pública si make_public=True).
    """
    b = _bucket()
    blob = b.blob(remote_path)
    blob.upload_from_filename(local_path)
    if make_public:
        blob.make_public()
        return blob.public_url
    # URL firmada temporal (si no querés hacerlo público):
    # return blob.generate_signed_url(expiration=timedelta(hours=1))
    return f"gs://{b.name}/{remote_path}"

def download_file(remote_path: str, local_path: str) -> None:
    b = _bucket()
    blob = b.blob(remote_path)
    blob.download_to_filename(local_path)

def delete_file(remote_path: str) -> None:
    b = _bucket()
    blob = b.blob(remote_path)
    blob.delete()

def exists(remote_path: str) -> bool:
    b = _bucket()
    return b.blob(remote_path).exists()

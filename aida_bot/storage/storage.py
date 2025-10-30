import os
import uuid
import tempfile
from firebase_admin import storage
from aida_bot.storage.database import get_db # Asegura que Firebase esté inicializado

class FileStorage:
    """
    Gestiona la subida y bajada de archivos a Firebase Storage.
    """
    def __init__(self, bucket_name: str):
        # Asegura que la app de Firebase esté inicializada
        get_db() 
        self.bucket_name = bucket_name
        self.bucket = storage.bucket(bucket_name)

    def upload_file(self, file_bytes: bytes, remote_folder: str, file_extension: str = ".jpg") -> str:
        """
        Sube bytes a Firebase Storage y devuelve la URL firmada (temporal).
        """
        # Crear un nombre de archivo único
        file_name = f"{uuid.uuid4()}{file_extension}"
        remote_path = f"{remote_folder}/{file_name}"
        
        blob = self.bucket.blob(remote_path)
        
        # Subir desde bytes
        blob.upload_from_string(file_bytes, content_type=f'image/{file_extension.strip(".")}')
        
        # Generar una URL firmada que dure 15 minutos (para que Groq la lea)
        try:
            signed_url = blob.generate_signed_url(expiration=900) # 900 segundos = 15 minutos
            return signed_url
        except Exception as e:
            print(f"[ERROR Storage] No se pudo firmar la URL: {e}. Intentando hacer público...")
            # Plan B: Hacerla pública (si los permisos lo permiten) y devolver URL pública
            blob.make_public()
            return blob.public_url

    def delete_file(self, remote_path: str):
        """Elimina un archivo del bucket."""
        try:
            blob = self.bucket.blob(remote_path)
            if blob.exists():
                blob.delete()
        except Exception as e:
            print(f"[ERROR Storage] No se pudo eliminar el archivo {remote_path}: {e}")
# aida_bot/sync_to_firestore.py
import json
import time
import os
from aida_bot.storage.database import FirebaseStorage

JSON_PATH = "aida_data_FF.json"  # ⚠️ Ruta del JSON real desde la raíz
SYNC_INTERVAL = 5  # segundos entre chequeos

def load_local_data():
    """Lee el contenido actual del JSON local."""
    if not os.path.exists(JSON_PATH):
        print("❌ No se encontró el archivo", JSON_PATH)
        return {"sessions": {}, "profiles": {}}
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def sync_once(local_data, firebase):
    """Sube los cambios locales a Firestore."""
    sessions = local_data.get("sessions", {})
    profiles = local_data.get("profiles", {})

    # 🔹 Subir sesiones
    for chat_id, session_data in sessions.items():
        firebase.save_session(chat_id, session_data)
        print(f"☁️ Sincronizada sesión {chat_id}")

    # 🔹 Subir perfiles
    for user_id, profile_data in profiles.items():
        firebase.save_profile(user_id, profile_data)
        print(f"☁️ Sincronizado perfil {user_id}")

def run_sync_loop():
    """Sincroniza cada pocos segundos automáticamente."""
    firebase = FirebaseStorage()
    last_snapshot = None

    print("🔄 Iniciando sincronización automática JSON ↔ Firestore...")
    while True:
        try:
            current = load_local_data()
            # Detectar cambios comparando texto JSON
            current_snapshot = json.dumps(current, sort_keys=True)
            if current_snapshot != last_snapshot:
                sync_once(current, firebase)
                last_snapshot = current_snapshot
            time.sleep(SYNC_INTERVAL)
        except KeyboardInterrupt:
            print("\n🛑 Sincronización detenida manualmente.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_sync_loop()

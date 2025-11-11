import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aida_bot.storage.database import get_storage_client


db = get_storage_client()
db.save_profile("test_user", {"nombre": "AIDA", "rol": "asistente"})
print(db.get_profile("test_user"))

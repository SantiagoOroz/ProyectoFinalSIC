import json
import os

class PerfilUsuarioManager:
    def __init__(self, archivo="data/perfilesAIDA.json"):
        self.archivo = archivo
        os.makedirs(os.path.dirname(archivo), exist_ok=True)
        if not os.path.exists(self.archivo):
            with open(self.archivo, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)

def guardar_perfil(usuario_id, perfil):
    archivo = "data/perfilesAIDA.json" 

    # Si el archivo ya existe, lo abrimos
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            perfiles = json.load(f)
    else:
        perfiles = {}

    # Guardamos el perfil bajo el ID del usuario
    perfiles[usuario_id] = perfil

    # Sobrescribimos el archivo con el nuevo contenido
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(perfiles, f, indent=4, ensure_ascii=False)


def cargar_perfil(usuario_id):
    archivo = "perfilesAIDA.json"

    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            perfiles = json.load(f)
            return perfiles.get(usuario_id)
    return None
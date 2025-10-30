import json
from aida_bot.storage.database import get_db

class PerfilUsuarioManager:
    """
    Gestiona la lectura y escritura de perfiles de usuario en Firestore.
    """
    def __init__(self, db_client):
        self.db = db_client
        self.collection = self.db.collection("user_profiles")

    def guardar_perfil(self, usuario_id: int, perfil: dict):
        """Guarda un perfil de usuario en Firestore."""
        try:
            self.collection.document(str(usuario_id)).set(perfil)
            print(f"Perfil guardado para {usuario_id}")
        except Exception as e:
            print(f"[ERROR PerfilManager] No se pudo guardar el perfil {usuario_id}: {e}")

    def obtener_perfil(self, usuario_id: int) -> dict | None:
        """Obtiene un perfil de usuario de Firestore."""
        try:
            doc = self.collection.document(str(usuario_id)).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"[ERROR PerfilManager] No se pudo obtener el perfil {usuario_id}: {e}")
            return None

class PerfilFormulario:
    """
    Maneja la lógica del formulario de bienvenida (/start) para nuevos usuarios.
    """
    def __init__(self, bot_instance, perfil_manager: PerfilUsuarioManager):
        self.bot = bot_instance
        self.perfil_manager = perfil_manager
        self._setup_handlers()

    def is_user_in_form(self, session: dict) -> bool:
        """Verifica si el usuario está actualmente en el formulario."""
        return session.get("form_step") is not None

    def _setup_handlers(self):
        """Registra el handler para el comando /start."""
        
        @self.bot.message_handler(commands=["start", "perfil"])
        def handle_start(msg):
            user_id = msg.from_user.id
            perfil_existente = self.perfil_manager.obtener_perfil(user_id)
            
            if perfil_existente and msg.text == "/start":
                self.bot.send_message(
                    user_id,
                    f"👋 ¡Hola de nuevo! Ya tengo tu perfil guardado 😊\n"
                    f"Si querés actualizarlo, escribí /perfil.\n\n"
                    f"¿En qué te puedo ayudar hoy?"
                )
            else:
                # Inicia el formulario (ya sea /start por primera vez o /perfil)
                self._iniciar_formulario(msg)

    def _iniciar_formulario(self, message):
        """Envía la primera pregunta del formulario."""
        user_id = message.from_user.id
        
        # Guardamos el estado del formulario en la sesión del bot (que es persistente)
        from aida_bot.bot import ModularBot # Importación local para evitar importación circular
        session = self.bot.sessions.get(user_id) # Asumimos que el bot tiene un session manager
        session["form_step"] = 1
        session["form_data"] = {}
        self.bot.sessions.update(user_id, session)

        self.bot.send_message(
            user_id,
            "Vamos a configurar tu perfil 🧩\n\n"
            "1️⃣ *Nivel de autonomía:*\n"
            "A) Mayoritariamente autónoma\n"
            "B) Con apoyos moderados\n"
            "C) Dependencia parcial o alta\n\n"
            "Respondé con *1A*, *1B* o *1C*.",
            parse_mode="Markdown"
        )

    def handle_form_message(self, message, session: dict):
        """Maneja las respuestas del usuario mientras está en el formulario."""
        user_id = message.from_user.id
        texto = message.text.strip().upper()
        paso = session.get("form_step")

        if paso == 1:
            if texto in ["1A", "1B", "1C"]:
                session["form_data"]["autonomia"] = texto
                session["form_step"] = 2
                self.bot.sessions.update(user_id, session)
                self.bot.send_message(
                    user_id,
                    "2️⃣ *Foco principal de acompañamiento:*\n"
                    "A) Prevención y promoción\n"
                    "B) Soporte emocional / social\n"
                    "C) Organización y seguridad del entorno\n"
                    "D) Estimulación cognitiva\n\n"
                    "Podés elegir más de una (ejemplo: *2B y 2D*)",
                    parse_mode="Markdown"
                )
            else:
                self.bot.send_message(user_id, "Respuesta no válida. Por favor, respondé *1A*, *1B* o *1C*.", parse_mode="Markdown")

        elif paso == 2:
            if any(x in texto for x in ["2A", "2B", "2C", "2D"]):
                session["form_data"]["foco"] = texto
                session["form_step"] = 3
                self.bot.sessions.update(user_id, session)
                self.bot.send_message(
                    user_id,
                    "3️⃣ *Entorno habitual:*\n"
                    "A) Vive sola/o\n"
                    "B) Vive con familia\n"
                    "C) Residencia / institucionalización\n"
                    "D) Centro de día / asistido parcialmente\n\n"
                    "Respondé con *3A*, *3B*, *3C* o *3D*.",
                    parse_mode="Markdown"
                )
            else:
                self.bot.send_message(user_id, "Respuesta no válida. Por favor, incluí al menos una opción (ej: *2A*).", parse_mode="Markdown")

        elif paso == 3:
            if texto in ["3A", "3B", "3C", "3D"]:
                session["form_data"]["entorno"] = texto
                
                # Guardar el perfil completo en Firestore
                self.perfil_manager.guardar_perfil(user_id, session["form_data"])

                # Limpiar el estado del formulario de la sesión
                session["form_step"] = None
                session["form_data"] = {}
                self.bot.sessions.update(user_id, session)

                self.bot.send_message(
                    user_id,
                    f"✅ ¡Perfil registrado con éxito!\n\n"
                    f"Gracias. Ahora podré adaptar mis respuestas un poco mejor.\n\n"
                    f"¿En qué te puedo ayudar hoy?"
                )
            else:
                self.bot.send_message(user_id, "Respuesta no válida. Por favor, respondé *3A*, *3B*, *3C* o *3D*.", parse_mode="Markdown")
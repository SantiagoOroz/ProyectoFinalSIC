# aida_bot/features/user_profiles.py
from telebot import types

class ProfileOnboarding:
    
    def __init__(self, bot_instance, storage_client):
        self.bot = bot_instance
        self.storage = storage_client

    def _get_profile_data(self, user_id):
        """Función helper para obtener o crear un perfil vacío."""
        profile = self.storage.get_profile(user_id)
        if not profile:
            profile = {}
        return profile

    def start_onboarding(self, message, force_retry=False):
        """Inicia el proceso de creación de perfil para un nuevo usuario."""
        chat_id = message.chat.id
        
        # Si no es forzado, revisa si existe
        if not force_retry:
            profile = self.storage.get_profile(chat_id)
            if profile:
                # Si ya existe y no es forzado, no hace nada
                self.bot.send_message(chat_id, "¡Hola de nuevo! Ya te conozco. 😊 ¿En qué te puedo ayudar hoy?")
                return

        # Lógica de Botones
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("A) Me manejo bien", callback_data="onboarding_autonomia_A"),
            types.InlineKeyboardButton("B) Más o menos, necesito ayuda", callback_data="onboarding_autonomia_B"),
            types.InlineKeyboardButton("C) Me cuesta bastante", callback_data="onboarding_autonomia_C"),
            row_width=1
        )
        
        self.bot.send_message(
            chat_id,
            "👋 ¡Hola! Soy *AIDA*, tu asistente digital.\n\n"
            "Para ayudarte mejor, me gustaría hacerte 3 preguntas rápidas.\n\n"
            "1️⃣ ¿Cómo te sentís usando tecnología? (Apretá un botón)"
        , reply_markup=markup, parse_mode="Markdown")
        
        # Guardamos un perfil vacío para ir llenándolo
        self.storage.save_profile(chat_id, {})


    def handle_callback(self, query):
        """Maneja las respuestas del formulario de onboarding."""
        user_id = query.from_user.id
        data = query.data # ej: "onboarding_autonomia_A"
        
        # Respondemos al callback para que el botón deje de "cargar"
        self.bot.answer_callback_query(query.id)
        
        try:
            # Editamos el mensaje original para que no se pueda volver a clickear
            self.bot.edit_message_reply_markup(chat_id=user_id, message_id=query.message.message_id, reply_markup=None)
        except Exception as e:
            print(f"No se pudo editar el markup: {e}") # Puede fallar si el bot se reinició
            
        profile_data = self._get_profile_data(user_id)
        
        # Lógica de Pasos
        
        if data.startswith("onboarding_autonomia_"):
            profile_data["autonomia"] = data.split('_')[-1] # Guarda "A", "B", o "C"
            self.storage.save_profile(user_id, profile_data) # Guardamos el progreso
            
            # Pregunta 2
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("A) Aprender cosas nuevas", callback_data="onboarding_foco_A"),
                types.InlineKeyboardButton("B) Ayuda con trámites y pagos", callback_data="onboarding_foco_B"),
                types.InlineKeyboardButton("C) Recordatorios y organización", callback_data="onboarding_foco_C"),
                types.InlineKeyboardButton("D) Simplemente conversar", callback_data="onboarding_foco_D"),
                row_width=1
            )
            self.bot.send_message(user_id, "¡Genial! 2️⃣ ¿En qué te gustaría que me enfoque más?", reply_markup=markup)

        elif data.startswith("onboarding_foco_"):
            profile_data["foco"] = data.split('_')[-1]
            self.storage.save_profile(user_id, profile_data)
            
            # Pregunta 3
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("A) Vivo solo/a", callback_data="onboarding_entorno_A"),
                types.InlineKeyboardButton("B) Vivo con mi pareja o familia", callback_data="onboarding_entorno_B"),
                types.InlineKeyboardButton("C) En una residencia o con asistencia", callback_data="onboarding_entorno_C"),
                row_width=1
            )
            self.bot.send_message(user_id, "¡Perfecto! Y la última, 3️⃣ ¿Vivís solo/a o con familia?", reply_markup=markup)

        elif data.startswith("onboarding_entorno_"):
            profile_data["entorno"] = data.split('_')[-1]
            self.storage.save_profile(user_id, profile_data)
            
            # Finalizar
            self.bot.send_message(
                user_id,
                "✅ ¡Perfil guardado! Muchas gracias. Esto me ayudará a darte respuestas mejor adaptadas a vos.\n\n"
                "Ahora sí, ¿en qué te puedo ayudar?"
            )
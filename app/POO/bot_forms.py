from perfiles import PerfilUsuarioManager

class PerfilFormulario:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.perfil_manager = PerfilUsuarioManager()
        self.estado_formulario = {}
        self.estado_bienvenida = {}

        self._setup_handlers()

    def _setup_handlers(self):
        @self.bot.message_handler(commands=["start"])
        def handle_start(msg):
            user_id = msg.from_user.id
            perfil_existente = self.perfil_manager.obtener_perfil(user_id)
            if perfil_existente:
                self.bot.send_message(
                    user_id,
                    f"👋 ¡Hola de nuevo! Ya tengo tu perfil guardado 😊\n"
                    f"Si querés actualizarlo, escribí /perfil.\n\n"
                    f"¿En qué te puedo ayudar hoy?"
                )
            else:
                self.bot.send_message(
                    user_id,
                    "👋 ¡Hola! Soy *AIDA*, tu asistente digital.\n\n"
                    "¿Sos nuevo/a en AIDA? (responde *Sí* o *No*)",
                    parse_mode="Markdown"
                )
                self.estado_bienvenida[user_id] = True

        @self.bot.message_handler(func=lambda message: True)
        def handle_message(msg):
            user_id = msg.from_user.id
            texto = msg.text.strip().lower()

            if user_id in self.estado_bienvenida:
                if "sí" in texto or "si" in texto:
                    self.bot.send_message(user_id, "Perfecto 😊 Vamos a conocerte un poquito mejor.")
                    del self.estado_bienvenida[user_id]
                    self.iniciar_formulario(msg)
                    return
                elif "no" in texto:
                    self.bot.send_message(user_id, "¡Genial! Bienvenido/a nuevamente ¿En qué puedo ayudarte hoy?")
                    del self.estado_bienvenida[user_id]
                    return
                else:
                    self.bot.send_message(user_id, "Solo respondé *Sí* o *No* para continuar.")
                    return

            if user_id in self.estado_formulario:
                self.manejar_respuesta(msg)
                return

    def iniciar_formulario(self, message):
        user_id = message.from_user.id
        self.estado_formulario[user_id] = {"paso": 1, "perfil": {}}
        self.bot.send_message(
            user_id,
            "Vamos a configurar tu perfil 🧩\n\n"
            "1️⃣ Nivel de autonomía:\n"
            "A) Mayoritariamente autónoma\n"
            "B) Con apoyos moderados\n"
            "C) Dependencia parcial o alta\n\n"
            "Respondé con 1A, 1B o 1C."
        )

    def manejar_respuesta(self, message):
        user_id = message.from_user.id
        texto = message.text.strip().upper()
        estado = self.estado_formulario[user_id]
        paso = estado["paso"]

        if paso == 1 and texto in ["1A", "1B", "1C"]:
            estado["perfil"]["autonomia"] = texto
            estado["paso"] = 2
            self.bot.send_message(
                user_id,
                "2️⃣ Foco principal de acompañamiento:\n"
                "A) Prevención y promoción\n"
                "B) Soporte emocional / social\n"
                "C) Organización y seguridad del entorno\n"
                "D) Estimulación cognitiva\n\n"
                "Podés elegir más de una (ejemplo: 2B y 2D)"
            )

        elif paso == 2 and any(x in texto for x in ["2A", "2B", "2C", "2D"]):
            estado["perfil"]["foco"] = texto
            estado["paso"] = 3
            self.bot.send_message(
                user_id,
                "3️⃣ Entorno habitual:\n"
                "A) Vive sola/o\n"
                "B) Vive con familia\n"
                "C) Residencia / institucionalización\n"
                "D) Centro de día / asistido parcialmente\n\n"
                "Respondé con 3A, 3B, 3C o 3D."
            )

        elif paso == 3 and texto in ["3A", "3B", "3C", "3D"]:
            estado["perfil"]["entorno"] = texto
            self.perfil_manager.guardar_perfil(user_id, estado["perfil"])

            self.bot.send_message(
                user_id,
                f"✅ Perfil registrado:\n\n{estado['perfil']}\n\nGracias. Ahora podré adaptar mis respuestas según este perfil."
            )
            del self.estado_formulario[user_id]

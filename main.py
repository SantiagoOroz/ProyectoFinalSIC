import telebot
from aida_bot import config
from aida_bot.bot import ModularBot, PersistentSessionManager
from aida_bot.storage.database import get_db
from aida_bot.storage.storage import FileStorage
from aida_bot.services.nlu_service import NLUService
from aida_bot.services.speech_service import SpeechService
from aida_bot.services.vision_service import VisionService
from aida_bot.services.sentiment_service import SentimentAnalyzer
from aida_bot.features.user_profiles import PerfilFormulario, PerfilUsuarioManager

def main():
    print("Iniciando servicios...")

    # 1. Inicializar la Base de Datos y Almacenamiento
    try:
        db = get_db()
        file_storage = FileStorage(bucket_name=config.FIREBASE_STORAGE_BUCKET)
        print("✅ Conexión a Firebase establecida.")
    except Exception as e:
        print(f"❌ ERROR al conectar con Firebase: {e}")
        print("Asegúrate de que 'GOOGLE_APPLICATION_CREDENTIALS' apunte a un 'service-account.json' válido.")
        return

    # 2. Inicializar el bot de Telegram
    bot_instance = telebot.TeleBot(config.TELEGRAM_TOKEN)

    # 3. Inicializar los Servicios
    nlu_service = NLUService(
        api_key=config.GROQ_API_KEY,
        api_url=config.GROQ_API_URL,
        chat_model=config.CHAT_MODEL,
        classifier_model=config.CLASSIFIER_MODEL
    )
    
    speech_service = SpeechService(model_size="base")
    
    sentiment_service = SentimentAnalyzer()

    vision_service = VisionService(
        groq_client=nlu_service.client, # Reutiliza el cliente de Groq
        file_storage=file_storage,
        model=config.VISION_MODEL
    )
    print("✅ Servicios de IA (NLU, Speech, Vision, Sentiment) inicializados.")

    # 4. Inicializar Gestores de Sesión y Perfiles (Persistentes)
    session_manager = PersistentSessionManager(db)
    profile_manager = PerfilUsuarioManager(db)
    print("✅ Gestores de sesión y perfiles listos.")

    # 5. Inicializar el Formulario de Perfiles (Maneja el /start)
    # Esta clase registra sus propios handlers en el bot
    profile_form = PerfilFormulario(bot_instance, profile_manager)

    # 6. Inicializar el Bot Modular Principal
    # Pasa el bot_instance y todos los servicios que necesita
    # NO maneja /start (lo hace profile_form), pero SÍ maneja texto, voz y fotos.
    general_bot = ModularBot(
        bot_instance=bot_instance,
        nlu=nlu_service,
        speech=speech_service,
        vision=vision_service,
        sentiment=sentiment_service,
        sessions=session_manager,
        profile_form=profile_form # Lo pasa para poder delegar el manejo de mensajes
    )

    # 7. Ejecutar el bot
    print("🚀 Bot AIDA iniciado. Escuchando mensajes...")
    general_bot.run()

if __name__ == "__main__":
    main()
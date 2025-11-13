# main.py
import telebot
from aida_bot import config
from aida_bot.storage.database import get_storage_client
from aida_bot.services.nlu_service import NLUService
from aida_bot.services.speech_service import SpeechService
from aida_bot.services.vision_service import VisionService
from aida_bot.services.sentiment_service import SentimentAnalyzer
from aida_bot.services.email_service import EmailService  # <--- AÑADIR
from aida_bot.services.translator_service import Translator
from aida_bot.bot import ModularBot, SessionManager
# from aida_bot.features.user_profiles import ProfileOnboarding # <--- ELIMINAR (bot.py lo maneja)


def main():
    print("--- INICIALIZANDO AIDA BOT ---")
    
    # 1. Instancia del bot de Telegram
    bot = telebot.TeleBot(config.TELEGRAM_TOKEN)
    
    # 2. Cliente de Almacenamiento (Firebase o JSON)
    storage = get_storage_client()
    
    # 3. Manejador de Sesiones (Persistentes)
    sessions = SessionManager(storage)

    # 4. Servicios Modulares
    nlu = NLUService(api_key=config.GROQ_API_KEY, api_url=config.GROQ_API_URL, storage=storage)

    
    speech = SpeechService(model_size="base")
    
    vision = VisionService(
        api_key=config.GROQ_API_KEY,
        api_url=config.GROQ_API_URL
    )
    
    sentiment = SentimentAnalyzer()

    email_service = EmailService() # <--- AÑADIR
    # email_service = EmailService() # <--- MODIFICADO: Comentado para desactivar alertas

    translator = Translator(api_key=config.GROQ_API_KEY)

    # --- ELIMINAR LOS HANDLERS DE main.py ---
    # (ModularBot se encarga de esto internamente)
    
    # 5. Instancia principal del Bot
    aida_bot = ModularBot(
        bot_instance=bot,
        nlu=nlu,
        speech=speech,
        vision=vision,
        sentiment=sentiment,
        email_service=email_service, # <--- AÑADIR
        translator=translator,
        sessions=sessions,
        storage_client=storage
    )

    # 6. Ejecutar el bot
    aida_bot.run()


if __name__ == "__main__":
    main()
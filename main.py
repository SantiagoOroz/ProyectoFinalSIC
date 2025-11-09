# main.py
import telebot
from aida_bot import config
from aida_bot.storage.database import get_storage_client
from aida_bot.services.nlu_service import NLUService
from aida_bot.services.speech_service import SpeechService
from aida_bot.services.vision_service import VisionService
from aida_bot.services.sentiment_service import SentimentAnalyzer
from aida_bot.services.email_service import EmailService
from aida_bot.services.translator_service import Translator
from aida_bot.bot import ModularBot, SessionManager

def main():
    print("--- INICIALIZANDO AIDA BOT ---")
    
    # 1. Instancia del bot de Telegram
    bot = telebot.TeleBot(config.TELEGRAM_TOKEN)
    
    # 2. Cliente de Almacenamiento (Firebase o JSON)
    storage = get_storage_client()
    
    # 3. Manejador de Sesiones (Persistentes)
    sessions = SessionManager(storage)

    # 4. Servicios Modulares
    nlu = NLUService(
        api_key=config.GROQ_API_KEY,
        api_url=config.GROQ_API_URL
    )
    
    speech = SpeechService(model_size="base")
    
    vision = VisionService(
        api_key=config.GROQ_API_KEY,
        api_url=config.GROQ_API_URL
    )
    
    sentiment = SentimentAnalyzer()

    email_service = EmailService()

    translator = Translator(
        api_key=config.GROQ_API_KEY
    )

    # 5. Instancia principal del Bot
    # Le pasamos todas las dependencias
    aida_bot = ModularBot(
        bot_instance=bot,
        nlu=nlu,
        speech=speech,
        vision=vision,
        sentiment=sentiment,
        email_service=email_service,
        translator=translator,
        sessions=sessions,
        storage_client=storage # Le pasamos el cliente de storage
    )

    # 6. Ejecutar el bot
    aida_bot.run()

if __name__ == "__main__":
    main()
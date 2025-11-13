# AIDA Bot - Asistente Digital Unificado

Este repositorio contiene el código fuente de AIDA, un chatbot de Telegram modular y empático diseñado para ayudar a adultos mayores con la tecnología.

Esta versión unifica múltiples prototipos en una arquitectura de servicios limpia.

## Arquitectura

* **`main.py`**: Punto de entrada. Carga la configuración e inicializa todos los servicios.
* **`aida_bot/config.py`**: Carga todas las variables de entorno desde `.env`.
* **`aida_bot/bot.py`**: Contiene la lógica principal del bot (`ModularBot`) y el manejo de sesiones (`SessionManager`).
* **`aida_bot/services/`**: Contiene los "cerebros" modulares:
    * `nlu_service.py`: Procesa lenguaje (Groq) y clasifica intenciones.
    * `speech_service.py`: Transcripción (Whisper) y Texto-a-Voz (EdgeTTS).
    * `vision_service.py`: Análisis de imágenes (Groq Vision).
    * `sentiment_service.py`: Análisis de sentimiento (Transformers).
* **`aida_bot/features/`**: Contiene lógica de "características" específicas:
    * `user_profiles.py`: El formulario de bienvenida para nuevos usuarios.
    * `feel_list.json`: Palabras clave para el análisis de sentimiento.
* **`aida_bot/storage/`**: Gestiona la persistencia de datos (perfiles, preferencias).
    * `database.py`: Abstracción que usa Firebase si está configurado, o un archivo JSON local (`aida_data.json`) como fallback.

## ⚙️ Configuración

1.  Clona el repositorio.
2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3.  Crea un archivo `.env` (puedes copiar `.env.example`).
4.  Rellena las variables de entorno:

    ```bash
    # (Requerido) Token de tu bot de Telegram
    TELEGRAM_TOKEN="TU_TOKEN_DE_TELEGRAM"

    # (Requerido) API Key de Groq
    GROQ_API_KEY="TU_API_KEY_DE_GROQ"
    GROQ_API_URL="[https://api.groq.com/openai/v1/chat/completions](https://api.groq.com/openai/v1/chat/completions)"

    # --- Opcional: Persistencia en la Nube ---
    # Si quieres usar Firebase Firestore para guardar perfiles y sesiones,
    # descarga tu 'service-account.json' y colócalo en la raíz del proyecto.
    # Si no, el bot usará un archivo 'aida_data.json' local.
    GOOGLE_APPLICATION_CREDENTIALS="service-account.json"
    ```

## ▶️ Ejecución

```bash
python main.py

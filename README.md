# ProyectoFinalSIC - AIDA Bot
Equipo: The Pythonauts
Comisión 1  

Integrantes:
Santiago Oroz - Milagros Argañin - Renata Berho

## Descripción
Bot de Telegram (AIDA - Asistente Inteligente Digital para Adultos) que integra todas las siguientes funcionalidades:
-   Chat con IA (Groq)
-   Transcripción de Audio (Whisper)
-   Síntesis de Voz (Edge-TTS) con selección de voz
-   Configuración de audio por usuario (On/Off)
-   Análisis de Imágenes (Groq Multimodal)
-   Perfiles de Usuario persistentes (Formulario en /start)
-   Base de datos y almacenamiento en Firebase (Firestore + Storage)
-   Análisis de Sentimiento

## Ejecución
1.  Crea un archivo `.env` (puedes usar `.env.example` como plantilla).
2.  Asegúrate de tener tu archivo `service-account.json` de Firebase en la raíz.
3.  Instala las dependencias: `pip install -r requirements.txt`
4.  Ejecuta el bot: `python main.py`
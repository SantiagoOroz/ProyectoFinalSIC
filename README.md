# AIDA Bot - Asistente Digital Unificado

**AIDA (Asistente Digital Unificado)** es un chatbot de Telegram modular y empático, diseñado para acompañar, enseñar y ayudar a adultos mayores a navegar el mundo de la tecnología con paciencia y claridad.

Este proyecto fue desarrollado como el **Trabajo Final del Samsung Innovation Campus**.
* [**Video de presentación AIDA**](https://youtu.be/Sl-CFzgz-u0)

---

## 👨‍💻 Integrantes del Equipo

* [**Santiago Oroz**](https://www.linkedin.com/in/santiago-oroz/)
* [**Renata Berho**](https://www.linkedin.com/in/renata-ana-emilia-berho-02264230a/)
* [**Milagros Argañin**](https://www.linkedin.com/in/milagros-arga%C3%B1in-13641a376/)
* Contacto: aidaassistantbot@gmail.com
---

## 📜 Índice

* [Características Principales](#-características-principales)
* [Stack Tecnológico](#-stack-tecnológico)
* [Arquitectura del Proyecto](#-arquitectura-del-proyecto)
* [Configuración e Instalación](#%EF%B8%8F-configuración-e-instalación)
    * [1. Prerrequisitos](#1-prerrequisitos)
    * [2. Instalación](#2-instalación)
    * [3. Variables de Entorno (`.env`)](#3-variables-de-entorno-env)
* [Ejecución](#-ejecución)
* [Agradecimientos](#-agradecimientos)

---

## ✨ Características Principales

Este bot no es solo un chat, sino un sistema de asistencia integral que incluye:

* **🧠 Inteligencia Conversacional (NLU):** Utiliza modelos de lenguaje de alta velocidad (vía Groq) para entender intenciones complejas, mantener conversaciones fluidas y responder preguntas más allá de su base de datos.
* **🗣️ Soporte de Voz (V2T y T2S):**
    * **Transcripción:** Convierte los mensajes de voz del usuario a texto usando `openai-whisper`.
    * **Síntesis de Voz:** Responde con mensajes de audio claros y naturales usando `edge-tts`, permitiendo al usuario elegir entre varias voces.
* **👁️ Análisis de Visión:** Permite a los usuarios enviar fotos. El bot utiliza un modelo de visión (`llama-4-scout`) para describir la imagen, leer texto (OCR) y **detectar posibles fraudes o phishing** en capturas de pantalla de mensajes.
* **❤️ Análisis de Sentimiento:** Monitorea los mensajes del usuario en busca de frustración, enojo o tristeza (`pysentimiento/robertuito`). Si detecta una emoción negativa fuerte, ajusta su tono para ser más empático.
* **🚨 Sistema de Alertas:** Si un usuario escribe palabras clave de alto riesgo (listadas en `feel_list.json`), el bot puede enviar automáticamente un correo de alerta (vía Make.com) a un contacto de emergencia.
* **👥 Perfiles de Usuario (Onboarding):** Al iniciar el bot por primera vez (`/start`), un cuestionario guía al usuario para entender su nivel de autonomía, sus intereses y su entorno, personalizando la interacción.
* **📚 Base de Conocimiento Local:** Incluye un `dataset.json` con más de 35 preguntas y respuestas comunes sobre tecnología, permitiendo respuestas instantáneas y precisas a las dudas más frecuentes.
* **🌐 Soporte Multi-idioma:** Detecta el idioma del usuario y puede traducir automáticamente sus respuestas si el usuario habla en un idioma diferente al español.
* **☁️ Base de Datos Híbrida:** El sistema puede guardar perfiles y sesiones en **Firebase Firestore** (para producción) o en un archivo **JSON local** (`aida_data.json`) como fallback para desarrollo.

---

## 🛠️ Stack Tecnológico

| Categoría | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Bot Framework** | `pyTelegramBotAPI` | Interacción principal con la API de Telegram. |
| **NLU y Visión** | `groq` | Inferencia de alta velocidad para Llama 3 (NLU) y Llama 4 (Visión). |
| **Voz a Texto** | `openai-whisper` | Transcripción de mensajes de voz. |
| **Texto a Voz** | `edge_tts` | Síntesis de voz natural y multi-idioma. |
| **Sentimiento** | `pysentimiento` | Análisis de sentimiento |
| **Base de Datos** | `firebase-admin` | Almacenamiento en la nube (perfiles y sesiones). |
| **Configuración** | `python-dotenv` | Carga de variables de entorno (API keys). |
| **Audio** | `pydub` | Procesamiento y conversión de archivos de audio. |
| **Utilidades** | `langdetect` | Detección de idioma para traducción. |

* [**Flujos del proceso, hechos con mermaid**](https://drive.google.com/drive/folders/1fdrQno89sITk2tT1_y0nFCjlRVw-2BVC?usp=sharing)
---

## 📁 Arquitectura del Proyecto

El proyecto sigue una arquitectura modular y orientada a servicios para separar responsabilidades:

```

santiagooroz-proyectofinalsic/
├── README.md
├── main.py                 \# 1. Punto de entrada: Inicializa y ejecuta el bot.
├── requirements.txt        \# Lista de dependencias.
├── .env.example            \# Plantilla para las variables de entorno.
├── aida\_data.json          \# Fallback de base de datos local (si Firebase no está).
├── service-account.json    \# (Opcional) Clave de Firebase.
└── aida\_bot/
├── config.py           \# 2. Carga todas las variables de entorno.
├── bot.py              \# 3. Lógica principal (ModularBot) y handlers de Telegram.
├── dataset.json        \# Base de conocimiento de preguntas y respuestas.
├── features/
│   ├── user\_profiles.py  \# Lógica del formulario de bienvenida (onboarding).
│   └── feel\_list.json    \# Palabras clave para el sistema de alertas.
├── services/
│   ├── nlu\_service.py      \# Cerebro: Conexión con Groq para chat y clasificación.
│   ├── speech\_service.py   \# Cerebro: Maneja Whisper (V2T) y EdgeTTS (T2S).
│   ├── vision\_service.py   \# Cerebro: Conexión con Groq para análisis de imágenes.
│   ├── sentiment\_service.py\# Cerebro: Analiza el sentimiento del texto.
│   ├── email\_service.py    \# Servicio de envío de alertas por correo.
│   └── translator\_service.py \# Servicio de traducción de texto.
└── storage/
└── database.py       \# 4. Abstracción de BD (elige Firebase o JSON).

````

---

## ⚙️ Configuración e Instalación

### 1. Prerrequisitos

* Python 3.10 o superior.
* Una cuenta de Telegram y un [Token de Bot](https://t.me/BotFather).
* Una [API Key de Groq](https://console.groq.com/keys).

### 2. Instalación

1.  Clona el repositorio:
    ```bash
    git clone [https://github.com/tu-usuario/santiagooroz-proyectofinalsic.git](https://github.com/tu-usuario/santiagooroz-proyectofinalsic.git)
    cd santiagooroz-proyectofinalsic
    ```

2.  Crea un entorno virtual (recomendado):
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Variables de Entorno (`.env`)

1.  Copia el archivo `.env.example` y renómbralo a `.env`:
    ```bash
    cp .env.example .env
    ```

2.  Abre el archivo `.env` y rellena tus claves API:

    ```ini
    # === REQUERIDO ===
    # Token de Telegram obtenido de @BotFather
    TELEGRAM_TOKEN="TU_TOKEN_DE_TELEGRAM_AQUI"

    # API Key de Groq ([https://console.groq.com/keys](https://console.groq.com/keys))
    GROQ_API_KEY="TU_API_KEY_DE_GROQ_AQUI"

    # URL de la API de Groq (generalmente no cambia)
    GROQ_API_URL="[https://api.groq.com/openai/v1/chat/completions](https://api.groq.com/openai/v1/chat/completions)"


    # === OPCIONAL: PERSISTENCIA EN LA NUBE ===
    # Si quieres usar Google Firebase para guardar datos:
    # 1. Crea un proyecto en Firebase y activa Firestore.
    # 2. Descarga tu 'service-account.json'.
    # 3. Coloca ese archivo JSON en la raíz del proyecto.
    # 4. Escribe el nombre de ese archivo aquí:
    # GOOGLE_APPLICATION_CREDENTIALS="service-account.json"

    # Si dejas GOOGLE_APPLICATION_CREDENTIALS vacío, el bot
    # guardará todos los perfiles en el archivo local 'aida_data.json'.
    ```

---

## ▶️ Ejecución

Una vez configurado el archivo `.env`, puedes iniciar el bot:

```bash
python main.py
````

El bot comenzará a escuchar mensajes.

-----

## 🙏 Agradecimientos

Queremos extender nuestro más sincero agradecimiento a las siguientes personas e instituciones por su apoyo y guía invaluable durante el desarrollo de este proyecto:

A todas las personas que hicieron posible la experiencia del curso **Samsung Campus Innovation:** Por su dedicación y por brindarnos esta valiosa oportunidad educativa.
  * **Profesor Alejandro Sosa**: Por su mentoría, paciencia y por brindarnos las herramientas fundamentales para llevar este proyecto a la realidad.
  * **Asociación Conciencia**: Por su dedicación, por facilitarnos el espacio de aprendizaje y por su compromiso con la inclusión digital.

<!-- end list -->


import os
import base64
import telebot
from dotenv import load_dotenv
import io
import requests
from groq import Groq

load_dotenv()

# --- Claves y Tokens ---
TOKEN_BOT_TELEGRAM = os.getenv('TELEGRAM_BOT_TOKEN')
CLAVE_API_GROQ = os.getenv('GROQ_API_KEY')

if not TOKEN_BOT_TELEGRAM:
    raise ValueError("TELEGRAM_BOT_TOKEN no está configurado en las variables de entorno")

if not CLAVE_API_GROQ:
    raise ValueError("GROQ_API_KEY no está configurado en las variables de entorno")

# --- Inicialización de Clientes ---
bot = telebot.TeleBot(TOKEN_BOT_TELEGRAM)
cliente_groq = Groq(api_key=CLAVE_API_GROQ)


def imagen_a_base64(ruta_o_bytes_imagen):
    """Convierte una imagen a base64 para enviarla a Groq"""
    try:
        if isinstance(ruta_o_bytes_imagen, bytes):
            return base64.b64encode(ruta_o_bytes_imagen).decode('utf-8')
        else:
            with open(ruta_o_bytes_imagen, "rb") as archivo_imagen:
                return base64.b64encode(archivo_imagen.read()).decode('utf-8')
    except Exception as e:
        print(f"Error al convertir imagen a base64: {e}")
        return None


def describir_imagen_con_groq(imagen_base64, mensaje):
    """Envía la imagen a Groq y obtiene la descripción"""
    try:
        completado_chat = cliente_groq.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""
                            Sos AIDA, un asistente empático, claro y paciente, diseñado para acompañar a personas mayores o con poca familiaridad con la tecnología.
                            Tu objetivo es facilitar su vida cotidiana, ayudándolos a entender y usar la tecnología, pero también a mantenerlos seguros ante posibles fraudes o engaños.

                            📸 Si el usuario te envía una imagen:
                            — Describila con claridad y amabilidad, incluyendo colores, objetos, personas, texto visible, logotipos, acciones y cualquier detalle útil.
                            — Si aparece texto (fechas, precios, nombres, vencimientos, links, etc.), leelo y explicalo de manera simple.
                            — Si la imagen parece un correo, mensaje o sitio falso (por ejemplo, con errores ortográficos, direcciones web sospechosas o pedidos de datos personales), advertí al usuario con calma:
                            👉 “Este mensaje parece ser un intento de fraude o phishing. No hagas clic en los enlaces ni ingreses tus datos personales. Si tenés dudas, contactá directamente al banco o empresa desde su página oficial.”
                            — Nunca confirmes que algo es auténtico si no podés verificarlo. En ese caso, decí: “No puedo confirmar si esto es verdadero, pero te recomiendo no ingresar datos personales ni abrir enlaces hasta comprobarlo.”

                            🎨 Si el usuario pregunta por algo visual:
                            — Decí los colores, formas, expresiones o elementos visibles de forma descriptiva y fácil de entender (“es un azul claro”, “parece una tarjeta bancaria”, “es una hoja con texto impreso”, etc.).

                            🗣️ En las conversaciones:
                            — Usá un tono cálido, paciente y empático, como si hablaras con un familiar mayor.
                            — Podés responder preguntas cotidianas sobre tecnología, trámites, objetos, colores, clima, recetas, o cualquier tema de interés general.
                            — Si algo no lo sabés, decí con amabilidad: “Entiendo tu pregunta, pero no tengo la información suficiente para responderte por ahora.”

                            Consulta del usuario: {mensaje}
                            """


                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                # Se envía la imagen como una data URL en formato base64
                                "url": f"data:image/jpeg;base64,{imagen_base64}"
                            }
                        }
                    ]
                }
            ],
            # Modelo de Groq con capacidad de visión
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.7,
            max_tokens=150
        )
        return completado_chat.choices[0].message.content
    except Exception as e:
        print(f"Error al describir imagen con Groq: {e}")
        return None


# --- Manejadores de Comandos ---
@bot.message_handler(commands=['start'])
def enviar_bienvenida(mensaje):
    """Mensaje de bienvenida"""
    texto_bienvenida = """
¡Hola! 👋 Soy AIDA que puede describir imágenes para ti.


🖼️ **¿Cómo funciono?**
Simplemente envíame una imagen y yo te daré una descripción de lo que veo.

📸 **¡Pruébame!**
Envía una imagen y verás lo que puedo hacer.


Para obtener ayuda, usa el comando /help
    # Cierra el string multi-línea y termina la asignación a texto_bienvenida
    """
    bot.reply_to(mensaje, texto_bienvenida)


@bot.message_handler(commands=['help'])
def enviar_ayuda(mensaje):
    """Mensaje de ayuda"""
    texto_ayuda = """
🔧 **Comandos disponibles:**

/start - Iniciar el bot
/help - Mostrar esta ayuda

📸 **¿Cómo usar el bot?**

1. Envía una imagen (foto, dibujo, captura, etc.)
2. Espera unos segundos mientras proceso la imagen
3. Recibirás una descripción de lo que veo

💡 **Consejos:**
- Las imágenes más claras y nítidas generan mejores descripciones
- Puedo analizar fotos, dibujos, gráficos, capturas de pantalla, etc.
- Respondo en español por defecto, pero si quieres otro idioma puedes decirme

❓ **¿Problemas?**
Si algo no funciona, intenta enviar la imagen de nuevo.
    """
    bot.reply_to(mensaje, texto_ayuda)


# --- Manejador Principal de Contenido ---
@bot.message_handler(content_types=['photo'])
def manejar_foto(mensaje):
    """Procesa las imágenes enviadas por el usuario"""
    try:

        # Obtener la foto de mayor calidad enviada por el usuario
        foto = mensaje.photo[-1]
        info_archivo = bot.get_file(foto.file_id)
        archivo_descargado = bot.download_file(info_archivo.file_path)

        imagen_base64 = imagen_a_base64(archivo_descargado)

        if not imagen_base64:
            bot.reply_to(mensaje, "❌ Error al procesar la imagen. Intenta de nuevo.")
            return

        descripcion = describir_imagen_con_groq(imagen_base64, mensaje)

        if descripcion:
            respuesta = f"🤖 **Descripción de la imagen:**\n\n{descripcion}"
            bot.reply_to(mensaje, respuesta, parse_mode='Markdown')
        else:
            bot.reply_to(mensaje, "❌ No pude analizar la imagen. Por favor, intenta con otra imagen.")

    except Exception as e:
        print(f"Error al procesar la imagen: {e}")
        bot.reply_to(mensaje, "❌ Ocurrió un error al procesar tu imagen. Intenta de nuevo.")


# Manejador para cualquier otro tipo de mensaje que no sea una foto o comando
# @bot.message_handler(func=lambda mensaje: True)
# def manejar_otros_mensajes(mensaje):
#     """Maneja mensajes que no son comandos ni imágenes"""
#     bot.reply_to(mensaje, """
# 📝 Solo puedo procesar imágenes por ahora.

# 📸 **Envía una imagen** y te daré una descripción detallada de ella.

# 💡 Usa /help para ver todos los comandos disponibles.
#     """)

# --- Bucle Principal del Bot ---
if __name__ == '__main__':
    print("🤖 Bot de descripción de imágenes iniciado...")
    print("📸 Esperando imágenes para describir...")

    try:
        # Inicia el bot en un bucle infinito para escuchar mensajes.
        # none_stop=True permite que el bot siga funcionando incluso si ocurre un error menor.
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error al iniciar el bot: {e}")

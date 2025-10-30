import whisper
import torch
import os
from tempfile import NamedTemporaryFile
import asyncio
import edge_tts
from pydub import AudioSegment

class SpeechService:
    """Maneja audio (voz a texto, texto a voz) usando Whisper y Edge-TTS."""
    
    # --- Diccionario centralizado de voces ---
    VOICES = {
        "Elena (Argentina)": "es-AR-ElenaNeural",
        "Tomás (Argentina)": "es-AR-TomasNeural",
        "Dalia (México)": "es-MX-DaliaNeural",
        "Elvira (España)": "es-ES-ElviraNeural",
        "Salome (Colombia)": "es-CO-SalomeNeural",
        "Andrew (EEUU)": "en-US-AndrewNeural",
        "Denise (Francia)": "fr-FR-DeniseNeural",
        "Killian (Alemania)": "de-DE-KillianNeural",
        "Francisca (Brasil)": "pt-BR-FranciscaNeural",
        "Elsa (Italia)": "it-IT-ElsaNeural",
        "Nanami (Japón)": "ja-JP-NanamiNeural",
        "Xiaoxiao (China)": "zh-CN-XiaoxiaoNeural",
    }
    
    # Voz por defecto para nuevos usuarios
    DEFAULT_VOICE = VOICES["Elena (Argentina)"]

    def __init__(self, model_size="base"):
        print(f"Cargando el modelo Whisper '{model_size}'...")
        self.model = whisper.load_model(model_size)
        self.language = "es" # Idioma para transcripción
    
    def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe los bytes de un archivo de audio a texto."""
        temp_file_path = None
        try:
            with NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name

            audio = whisper.load_audio(temp_file_path)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

            options = whisper.DecodingOptions(language=self.language, fp16=torch.cuda.is_available())
            result = whisper.decode(self.model, mel, options)
            
            return result.text.strip()
        except Exception as e:
            print(f"[ERROR Whisper] No se pudo transcribir el audio: {e}")
            return ""
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    
    def synthesize(self, text: str, voice_id: str, output_filename: str = "response_audio") -> str | None:
        """Sintetiza texto a un archivo de audio .ogg usando el 'voice_id'."""
        
        async def _async_synthesize():
            mp3_path = f"{output_filename}.mp3"
            ogg_path = f"{output_filename}.ogg"
            
            try:
                communicate = edge_tts.Communicate(text, voice_id) 
                await communicate.save(mp3_path)

                audio = AudioSegment.from_mp3(mp3_path)
                audio.export(ogg_path, format="ogg", codec="libopus")
                
                return ogg_path
            except Exception as e:
                print(f"[ERROR TTS] No se pudo sintetizar el audio ({voice_id}): {e}")
                return None
            finally:
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)

        try:
            # Intenta ejecutar en el loop de eventos existente
            audio_path = asyncio.run(_async_synthesize())
            return audio_path
        except RuntimeError:
            # Si falla (ej. 'asyncio.run() cannot be called from a running event loop')
            # crea un nuevo loop.
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_path = loop.run_until_complete(_async_synthesize())
            return audio_path
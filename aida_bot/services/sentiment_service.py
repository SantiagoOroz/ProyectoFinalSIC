# aida_bot/services/sentiment_service.py
from transformers import pipeline
import json
import os
import time

class SentimentAnalyzer:
    """Analiza el sentimiento de un texto usando transformers."""
    
    def __init__(self, model_name="pysentimiento/robertuito-sentiment-analysis", alert_file_path="aida_bot/features/feel_list.json"):
        print("🔄 Cargando modelo de análisis de sentimiento...")
        self.analyzer = pipeline("sentiment-analysis", model=model_name)
        print("✅ Modelo de sentimiento cargado.")
        self.alert_words = self._load_alert_words(alert_file_path)
        
        # Mapeo de etiquetas a un español más amigable
        self.label_map = {
            "NEG": "frustración o enojo",
            "POS": "alegría o entusiasmo",
            "NEU": "neutralidad"
        }

    def _load_alert_words(self, file_path):
        """Carga las palabras de alerta desde el archivo JSON."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [word.lower() for word in data.get("sentimientos_alerta", [])]
        except FileNotFoundError:
            print(f"⚠️ Error: El archivo '{file_path}' no se encontró.")
            return []
        except json.JSONDecodeError:
            print(f"⚠️ Error: El archivo '{file_path}' no es un JSON válido.")
            return []

    def check_for_alert(self, text: str) -> bool:
        """Verifica si el texto contiene alguna palabra de alerta."""
        text_lower = text.lower()
        for word in self.alert_words:
            if word in text_lower:
                return True
        return False
        
    def analyze(self, text: str) -> dict:
        """
        Analiza el sentimiento y devuelve un dict con 'label' y 'score'.
        Labels son: 'POS', 'NEG', 'NEU'.
        """
        try:
            result = self.analyzer(text)[0]
            return {
                "label": result.get('label'),
                "score": result.get('score')
            }
        except Exception as e:
            print(f"[ERROR Sentimiento] {e}")
            return {"label": "NEU", "score": 0.0}

    def format_analysis(self, analysis_result: dict) -> str | None:
        """
        Formatea el resultado del análisis en un mensaje amigable para el usuario.
        Devuelve None si no es un sentimiento fuerte.
        """
        label = analysis_result.get("label")
        score = analysis_result.get("score", 0)
        
        # Solo reportamos sentimientos fuertes
        if score < 0.75:
            return None
            
        friendly_label = self.label_map.get(label, "una emoción")
        
        if label == "NEG":
            return f"Veo que esto puede estar generándote {friendly_label}. (Confianza: {score:.0%}) \nNo te preocupes, estoy aquí para ayudarte."
        elif label == "POS":
            return f"¡Noto {friendly_label} en tu mensaje! (Confianza: {score:.0%}) \nMe alegra que te sientas así."
        
        return None
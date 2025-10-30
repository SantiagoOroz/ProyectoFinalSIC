from transformers import pipeline

class SentimentAnalyzer:
    """Analiza el sentimiento de un texto usando un modelo local."""
    def __init__(self, model_name="pysentimiento/robertuito-sentiment-analysis"):
        try:
            print("🔄 Cargando modelo de análisis de sentimiento (Robertuito)...")
            self.analyzer = pipeline("sentiment-analysis", model=model_name)
            print("✅ Modelo de sentimiento cargado.")
        except Exception as e:
            print(f"❌ ERROR al cargar el modelo de sentimiento: {e}")
            print("Ejecuta 'pip install pysentimiento transformers' para instalarlo.")
            self.analyzer = None

    def analyze(self, text: str) -> str:
        if self.analyzer is None:
            return "El servicio de análisis de sentimiento no está disponible."
            
        try:
            result = self.analyzer(text)[0]
            sentimiento = result['label']
            confianza = result['score']

            emoji = "❓"
            traduccion = "Desconocido"
            if sentimiento == "POS":
                emoji = "😊"
                traduccion = "Positivo"
            elif sentimiento == "NEG":
                emoji = "😟"
                traduccion = "Negativo"
            elif sentimiento == "NEU":
                emoji = "😐"
                traduccion = "Neutral"

            return f"Sentimiento: *{traduccion}* {emoji} (Confianza: {confianza:.1%})"
        except Exception as e:
            print(f"[ERROR Sentiment] {e}")
            return "No pude analizar el sentimiento de ese texto."
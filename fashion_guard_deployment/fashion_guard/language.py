import importlib
import re
import unicodedata

SUPPORTED_LANGUAGES = frozenset({"en", "de", "fr", "it", "es", "tr"})
LANGUAGE_MARKERS = {
    "tr": ("ariyorum", "istiyorum", "olabilir mi", "bulabilir misin", "ne giysem", "dugun", "icin", "elbise", "ayakkabi", "ceket", "canta", "indirim", "butce", "selam", "merhaba", "nasilsin", "tesekkur", "tesekkurler"),
    "de": ("ich suche", "ich brauche", "ich mochte", "welche", "kann ich", "bitte hilf", "mantel", "jacke", "kleid", "schuhe", "tasche", "hochzeit", "lieferung", "hallo", "guten tag", "wie geht"),
    "fr": ("je cherche", "je voudrais", "quelle tenue", "peux tu", "aide moi", "manteau", "veste", "robe", "chaussures", "sac", "mariage", "livraison", "bonjour", "salut", "comment vas"),
    "it": ("cerco", "vorrei", "cosa posso", "puoi", "aiutami", "cappotto", "giacca", "abito", "scarpe", "borsa", "matrimonio", "consegna", "ciao", "buongiorno", "come stai"),
    "es": ("busco", "quiero", "que puedo", "que vestido puedo", "puedes", "ayudame", "abrigo", "chaqueta", "vestido", "zapatos", "bolso", "boda", "entrega", "hola", "como estas"),
    "pt": ("eu procuro", "posso", "vestir", "casamento", "sapatos", "vestido"),
    "nl": ("ik zoek", "welke schoenen", "jurk", "bruiloft", "bezorging"),
    "pl": ("szukam", "jakie buty", "sukienka", "wesele", "dostawa"),
    "ar": ("ارتدي", "فستان", "معطف", "حذاء", "زفاف", "ملابس"),
}


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    ascii_text = ascii_text.translate(str.maketrans({"ı": "i", "ß": "ss"}))
    return f" {re.sub(r'[^a-z0-9]+', ' ', ascii_text)} "


class LanguageDetector:
    def detect(self, text: str) -> str | None:
        strong = self._fallback(text, strong_only=True)
        if strong:
            return strong
        try:
            module = importlib.import_module("langdetect")
            module.DetectorFactory.seed = 42
            return module.detect(text)
        except Exception:
            return self._fallback(text)

    @staticmethod
    def _fallback(text: str, strong_only: bool = False) -> str | None:
        if any("\u0600" <= char <= "\u06ff" for char in text):
            return "ar"
        padded = normalize_text(text)
        scores = {
            language: sum(len(marker.split()) for marker in markers if f" {marker} " in padded)
            for language, markers in LANGUAGE_MARKERS.items()
        }
        best_score = max(scores.values())
        best_languages = [language for language, score in scores.items() if score == best_score]
        if best_score and len(best_languages) == 1:
            return best_languages[0]
        if strong_only:
            return None
        return "en" if any(char.isascii() and char.isalpha() for char in text) else None

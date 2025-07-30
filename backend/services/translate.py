from langdetect import detect
from deep_translator import GoogleTranslator

def detect_language(text: str) -> str:
    return detect(text)

def translate_text(text: str, source: str, target: str) -> str:
    return GoogleTranslator(source=source, target=target).translate(text)

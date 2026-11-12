"""Translation + text-to-speech logic (UI-independent, unit-testable)."""
from __future__ import annotations

import re
import time
from io import BytesIO
from typing import Dict, List

from deep_translator import GoogleTranslator, MyMemoryTranslator

AUTO = "auto"
MAX_CHARS = 5000  # Google Translate per-request limit
GOOGLE_RETRIES = 3          # attempts before switching to the backup service
RETRY_DELAY = 1.5           # seconds; multiplied by the attempt number
MYMEMORY_CHUNK = 450        # MyMemory accepts at most 500 characters per request


class TranslationError(Exception):
    """Raised for any user-facing translation or speech failure."""


def get_languages() -> Dict[str, str]:
    """Return {Display Name: language code}, sorted alphabetically."""
    langs = GoogleTranslator().get_supported_languages(as_dict=True)
    return {name.title(): code for name, code in sorted(langs.items())}


def _code_to_name(code: str) -> str:
    """Map a Google language code (e.g. 'ur') to the language name MyMemory understands."""
    langs = GoogleTranslator().get_supported_languages(as_dict=True)
    return next((name for name, c in langs.items() if c == code), code)


def _chunks(text: str, size: int = MYMEMORY_CHUNK) -> List[str]:
    """Split text into pieces of at most `size` characters, preferring sentence boundaries."""
    pieces: List[str] = []
    current = ""
    for sentence in re.split(r"(?<=[.!?\u06d4])\s+", text):
        while len(sentence) > size:                       # very long sentence: split by words
            cut = sentence.rfind(" ", 0, size)
            cut = cut if cut > 0 else size
            pieces.append(sentence[:cut])
            sentence = sentence[cut:].lstrip()
        if current and len(current) + 1 + len(sentence) > size:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def _translate_google(text: str, source: str, target: str) -> str:
    """Google Translate with retry/backoff (handles temporary rate limiting)."""
    last_exc: Exception = RuntimeError("no attempt made")
    for attempt in range(1, GOOGLE_RETRIES + 1):
        try:
            return GoogleTranslator(source=source, target=target).translate(text)
        except Exception as exc:
            last_exc = exc
            if attempt < GOOGLE_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
    raise last_exc


def _translate_backup(text: str, source: str, target: str) -> str:
    """Backup provider (MyMemory, free, no key) used when Google is unavailable."""
    src_name = "auto" if source == AUTO else _code_to_name(source)
    translator = MyMemoryTranslator(source=src_name, target=_code_to_name(target))
    if source == AUTO:
        translator._source = "Autodetect"                 # MyMemory's auto-detect keyword
    return " ".join(translator.translate(chunk) for chunk in _chunks(text))


def translate_text(text: str, source: str, target: str) -> str:
    """Translate `text` from `source` (or 'auto') into `target`.

    Tries Google Translate (with retries); if it is rate-limited or down,
    falls back to the MyMemory service.
    """
    text = text.strip()
    if not text:
        raise TranslationError("Please enter some text to translate.")
    if len(text) > MAX_CHARS:
        raise TranslationError(f"Text is too long ({len(text)}/{MAX_CHARS} characters).")
    if source == target:
        raise TranslationError("Source and target languages are the same.")

    try:
        result = _translate_google(text, source, target)
    except Exception as google_exc:
        try:
            result = _translate_backup(text, source, target)
        except Exception as backup_exc:
            raise TranslationError(
                "Translation services are busy right now. Please wait a minute and try again. "
                f"(Google: {google_exc}; backup: {backup_exc})"
            ) from backup_exc

    if not result:
        raise TranslationError("The service returned an empty translation. Try again.")
    return result


def text_to_speech(text: str, lang: str) -> bytes:
    """Return MP3 bytes of `text` spoken in `lang` (gTTS)."""
    try:
        from gtts import gTTS

        buffer = BytesIO()
        gTTS(text=text, lang=lang).write_to_fp(buffer)
        return buffer.getvalue()
    except Exception as exc:
        raise TranslationError(f"Text-to-speech is not available for this language: {exc}") from exc

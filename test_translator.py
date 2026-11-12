"""Unit tests (network and sleeping mocked). Run: python -m unittest -v test_translator"""
import unittest
from unittest.mock import patch

import translator
from translator import (GOOGLE_RETRIES, MAX_CHARS, MYMEMORY_CHUNK, TranslationError, _chunks,
                        get_languages, translate_text)


@patch("translator.time.sleep")
class TranslateTests(unittest.TestCase):
    @patch("translator.GoogleTranslator")
    def test_success(self, mock_cls, _sleep):
        mock_cls.return_value.translate.return_value = "Hola"
        self.assertEqual(translate_text("  Hello ", "en", "es"), "Hola")
        mock_cls.assert_called_with(source="en", target="es")
        mock_cls.return_value.translate.assert_called_with("Hello")

    def test_empty_text(self, _sleep):
        with self.assertRaises(TranslationError):
            translate_text("   ", "en", "es")

    def test_too_long(self, _sleep):
        with self.assertRaises(TranslationError):
            translate_text("a" * (MAX_CHARS + 1), "en", "es")

    def test_same_language(self, _sleep):
        with self.assertRaises(TranslationError):
            translate_text("hi", "en", "en")

    @patch("translator.GoogleTranslator")
    def test_retries_then_succeeds(self, mock_cls, sleep):
        mock_cls.return_value.translate.side_effect = [RuntimeError("429"), "Bonjour"]
        self.assertEqual(translate_text("hi", "en", "fr"), "Bonjour")
        self.assertEqual(sleep.call_count, 1)

    @patch("translator._translate_backup", return_value="backup result")
    @patch("translator.GoogleTranslator")
    def test_falls_back_when_google_rate_limited(self, mock_cls, mock_backup, sleep):
        mock_cls.return_value.translate.side_effect = RuntimeError("Too many requests")
        self.assertEqual(translate_text("hi", "auto", "ur"), "backup result")
        self.assertEqual(mock_cls.return_value.translate.call_count, GOOGLE_RETRIES)
        mock_backup.assert_called_once_with("hi", "auto", "ur")

    @patch("translator._translate_backup", side_effect=RuntimeError("backup down"))
    @patch("translator.GoogleTranslator")
    def test_both_services_fail(self, mock_cls, _backup, _sleep):
        mock_cls.return_value.translate.side_effect = RuntimeError("network down")
        with self.assertRaises(TranslationError) as ctx:
            translate_text("hi", "auto", "ur")
        self.assertIn("wait a minute", str(ctx.exception))

    @patch("translator.GoogleTranslator")
    def test_empty_result(self, mock_cls, _sleep):
        mock_cls.return_value.translate.return_value = ""
        with self.assertRaises(TranslationError):
            translate_text("hi", "en", "fr")


class HelperTests(unittest.TestCase):
    def test_language_list(self):
        langs = get_languages()
        self.assertEqual(langs.get("Urdu"), "ur")
        self.assertEqual(langs.get("English"), "en")
        self.assertGreater(len(langs), 50)

    def test_chunks_respect_limit_and_keep_content(self):
        text = " ".join(f"Sentence number {i} is here." for i in range(80))
        parts = _chunks(text)
        self.assertTrue(all(len(p) <= MYMEMORY_CHUNK for p in parts))
        self.assertEqual(" ".join(parts).split(), text.split())

    def test_chunks_long_sentence_without_punctuation(self):
        text = "word " * 400
        parts = _chunks(text.strip())
        self.assertTrue(all(len(p) <= MYMEMORY_CHUNK for p in parts))

    def test_code_to_name(self):
        self.assertEqual(translator._code_to_name("ur"), "urdu")


if __name__ == "__main__":
    unittest.main()

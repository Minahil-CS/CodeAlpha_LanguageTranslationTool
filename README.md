# 🌐 Language Translation Tool

CodeAlpha AI Internship, **Task 1**. A Streamlit web app that translates text between 100+ languages.

## Features
- Text input with source and target language selection (plus **auto-detect**)
- Translation via the Google Translate service (`deep-translator`, no API key needed)
- Clear output with right-to-left support (Urdu, Arabic)
- **Copy button** (built into the output box) and **text-to-speech** (gTTS)
- **Reliable:** automatic retry, then a backup service (MyMemory) if Google rate-limits you; repeated requests are cached
- Swap languages, recent-translation history, and friendly error handling

## Project Structure
| File | Purpose |
|---|---|
| `app.py` | Streamlit user interface |
| `translator.py` | Translation and TTS logic (UI-independent) |
| `test_translator.py` | Unit tests (12 tests, network mocked) |
| `requirements.txt` | Dependencies |

## Run Locally
```bash
git clone https://github.com/<your-username>/CodeAlpha_LanguageTranslationTool.git
cd CodeAlpha_LanguageTranslationTool
pip install -r requirements.txt
streamlit run app.py
```

## Run Tests
```bash
python -m unittest -v test_translator
```

## How It Works
1. User enters text and picks source and target languages.
2. `translate_text()` validates input (empty, length, same language).
3. The text is sent to Google Translate and the response is displayed.
4. Optionally, `text_to_speech()` converts the result to MP3 audio.

## Notes
- Limit: 5,000 characters per request.
- Uses the free Google Translate web endpoint (with automatic fallback to MyMemory, 500-character chunks). For production, switch to the official Google Cloud Translation API.

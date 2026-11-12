"""Language Translation Tool - CodeAlpha AI Internship, Task 1.

Run:  streamlit run app.py
"""
import html

import streamlit as st

from translator import AUTO, MAX_CHARS, TranslationError, get_languages, text_to_speech, translate_text

AUTO_LABEL = "Detect language"

st.set_page_config(page_title="Language Translator", page_icon="🌐", layout="centered")


@st.cache_data
def load_languages() -> dict:
    return get_languages()


@st.cache_data(ttl=3600, show_spinner=False)
def cached_translate(text: str, source: str, target: str) -> str:
    """Identical requests are served from cache, which also reduces rate-limit hits."""
    return translate_text(text, source, target)


LANGS = load_languages()
SOURCE_OPTIONS = [AUTO_LABEL] + list(LANGS)
TARGET_OPTIONS = list(LANGS)

# ---- session state ---------------------------------------------------------
st.session_state.setdefault("src_name", AUTO_LABEL)
st.session_state.setdefault("tgt_name", "Urdu" if "Urdu" in LANGS else TARGET_OPTIONS[0])
st.session_state.setdefault("result", None)
st.session_state.setdefault("history", [])


def swap_languages() -> None:
    """Swap source/target (disabled while source is auto-detect)."""
    s, t = st.session_state.src_name, st.session_state.tgt_name
    if s != AUTO_LABEL:
        st.session_state.src_name, st.session_state.tgt_name = t, s


# ---- UI --------------------------------------------------------------------
st.title("🌐 Language Translator")
st.caption("Translate text between 100+ languages. Built for CodeAlpha AI Internship, Task 1.")

col_src, col_swap, col_tgt = st.columns([5, 1, 5], vertical_alignment="bottom")
col_src.selectbox("From", SOURCE_OPTIONS, key="src_name")
col_swap.button("⇄", on_click=swap_languages, disabled=st.session_state.src_name == AUTO_LABEL,
                help="Swap languages", use_container_width=True)
col_tgt.selectbox("To", TARGET_OPTIONS, key="tgt_name")

text = st.text_area("Text to translate", height=160, max_chars=MAX_CHARS,
                    placeholder="Type or paste text here...")

if st.button("Translate", type="primary", use_container_width=True):
    src_code = AUTO if st.session_state.src_name == AUTO_LABEL else LANGS[st.session_state.src_name]
    tgt_code = LANGS[st.session_state.tgt_name]
    try:
        with st.spinner("Translating..."):
            translated = cached_translate(text, src_code, tgt_code)
        st.session_state.result = {"text": translated, "lang": tgt_code, "audio": None}
        st.session_state.history.insert(0, (text.strip(), translated, st.session_state.tgt_name))
        st.session_state.history = st.session_state.history[:5]
    except TranslationError as err:
        st.session_state.result = None
        st.error(str(err))

result = st.session_state.result
if result:
    st.subheader("Translation")
    # dir="auto" renders right-to-left languages (Urdu, Arabic) correctly
    st.markdown(
        f'<div dir="auto" style="padding:1rem;border:1px solid rgba(128,128,128,.35);'
        f'border-radius:.5rem;font-size:1.15rem;white-space:pre-wrap;">{html.escape(result["text"])}</div>',
        unsafe_allow_html=True,
    )
    st.caption("📋 Copy: use the icon on the box below")
    st.code(result["text"], language=None, wrap_lines=True)

    if st.button("🔊 Listen"):
        try:
            result["audio"] = text_to_speech(result["text"], result["lang"])
        except TranslationError as err:
            st.warning(str(err))
    if result["audio"]:
        st.audio(result["audio"], format="audio/mp3")

if st.session_state.history:
    with st.expander("Recent translations"):
        for original, translated, lang in st.session_state.history:
            st.markdown(f"**{original}**  \n→ ({lang}) {translated}")

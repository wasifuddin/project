"""
AI Image Editor (Google Gemini) — Streamlit app.

Upload an image, describe a change in plain language, and a Gemini image model
edits it. Each result becomes the new working image, so you can refine
prompt-by-prompt.

Run:
    pip install -r requirements.txt
    # put GEMINI_API_KEY (or GOOGLE_API_KEY) in a .env file, or set it in the env
    streamlit run app.py
"""

import io
import os

import streamlit as st
from PIL import Image

try:  # load a local .env if python-dotenv is installed (optional convenience)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# Gemini image-editing models, best/newest first.
# gemini-3-pro-image is the top-quality (Pro) model; the flash models are faster.
ALLOWED_MODELS = ["gemini-3.1-flash-image", "gemini-3-pro-image", "gemini-2.5-flash-image"]
DEFAULT_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")

# Resolution (Gemini 3 models). Lower is much faster: 1K ~18s vs 2K ~85s on Pro.
RESOLUTIONS = ["1K", "2K", "4K"]
ASPECT_RATIOS = ["Auto", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"]


def get_api_key():
    """Accept either GEMINI_API_KEY or GOOGLE_API_KEY."""
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def run_edit(image: Image.Image, prompt: str, model: str,
             resolution: str = "1K", aspect_ratio: str = "Auto") -> Image.Image:
    """Send the image + prompt to Gemini and return the edited image.

    resolution / aspect_ratio are honoured by the Gemini 3 image models
    (gemini-3-*); the 2.5 flash model ignores them (it outputs ~1K).
    """
    from google import genai
    from google.genai import types

    image_cfg = {}
    if model.startswith("gemini-3"):
        image_cfg["image_size"] = resolution          # 1K / 2K / 4K
        if aspect_ratio != "Auto":
            image_cfg["aspect_ratio"] = aspect_ratio

    config = types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(**image_cfg) if image_cfg else None,
    )

    # A request timeout so a stalled API call fails cleanly instead of hanging.
    client = genai.Client(
        api_key=get_api_key(),
        http_options=types.HttpOptions(timeout=180_000),  # 3 min hard cap
    )
    response = client.models.generate_content(
        model=model,
        contents=[prompt, image.convert("RGB")],
        config=config,
    )

    parts = response.candidates[0].content.parts
    for part in parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            return Image.open(io.BytesIO(inline.data)).convert("RGBA")

    # No image came back — surface any text the model returned as the reason.
    texts = [p.text for p in parts if getattr(p, "text", None)]
    raise RuntimeError(
        "Gemini returned no image. "
        + (" ".join(texts) if texts else "Try rephrasing the prompt.")
    )


def img_to_png_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Page setup
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="AI Image Editor", page_icon="🪄", layout="wide")

# Session state holds the original upload and the current working image.
ss = st.session_state
ss.setdefault("original", None)   # PIL.Image — first upload
ss.setdefault("current", None)    # PIL.Image — latest version
ss.setdefault("upload_id", None)  # to detect a fresh upload

st.title("🪄 AI Image Editor")
st.caption("Upload an image, describe a change, and Gemini edits it. "
           "Each result feeds back in so you can keep refining.")

api_key = get_api_key()
if not api_key:
    st.error(
        "No API key found. Add **GEMINI_API_KEY** (or **GOOGLE_API_KEY**) to a "
        "`.env` file in this folder or set it in your environment, then restart. "
        "Get a key at https://aistudio.google.com/apikey"
    )

# --------------------------------------------------------------------------- #
# Sidebar — controls
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("Controls")

    uploaded = st.file_uploader(
        "Image", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=False
    )
    if uploaded is not None and uploaded.file_id != ss.upload_id:
        img = Image.open(uploaded).convert("RGBA")
        ss.original = img
        ss.current = img
        ss.upload_id = uploaded.file_id

    prompt = st.text_area(
        "Prompt",
        placeholder="e.g. turn the sky into a dramatic sunset, add a small red boat…",
        height=120,
    )

    model = st.selectbox(
        "Model", ALLOWED_MODELS,
        index=ALLOWED_MODELS.index(DEFAULT_MODEL) if DEFAULT_MODEL in ALLOWED_MODELS else 0,
    )

    is_gemini3 = model.startswith("gemini-3")
    col_r, col_a = st.columns(2)
    with col_r:
        resolution = st.selectbox(
            "Resolution", RESOLUTIONS, index=0, disabled=not is_gemini3,
            help="1K is ~5× faster than 2K. Only the Gemini 3 models support this.",
        )
    with col_a:
        aspect_ratio = st.selectbox(
            "Aspect ratio", ASPECT_RATIOS, index=0, disabled=not is_gemini3,
            help="‘Auto’ keeps the source proportions.",
        )
    if not is_gemini3:
        st.caption("ℹ️ This model outputs ~1K and ignores the controls above.")
    elif resolution != "1K":
        st.caption("⏳ Higher resolution is noticeably slower (2K ≈ 85s, 4K longer).")

    generate = st.button(
        "✨ Generate edit",
        type="primary",
        use_container_width=True,
        disabled=(ss.current is None or not api_key),
    )
    if st.button("↩︎ Reset to original", use_container_width=True,
                 disabled=ss.original is None):
        ss.current = ss.original
        st.rerun()

# --------------------------------------------------------------------------- #
# Run an edit
# --------------------------------------------------------------------------- #
if generate:
    if not prompt.strip():
        st.warning("Enter a prompt first.")
    elif ss.current is None:
        st.warning("Upload an image first.")
    else:
        try:
            with st.spinner(f"Editing with {model} at {resolution}… this can take a moment"):
                ss.current = run_edit(ss.current, prompt.strip(), model,
                                      resolution, aspect_ratio)
            st.success("Done ✨ — edit again to refine.")
        except Exception as exc:  # noqa: BLE001 — show the provider's reason
            st.error(f"AI edit failed: {exc}")

# --------------------------------------------------------------------------- #
# Main view — before / after
# --------------------------------------------------------------------------- #
if ss.current is None:
    st.info("⬅️ Upload an image in the sidebar to get started.")
else:
    left, right = st.columns(2)
    with left:
        st.subheader("Original")
        if ss.original is not None:
            st.image(ss.original, use_container_width=True)
    with right:
        st.subheader("Current")
        st.image(ss.current, use_container_width=True)
        st.download_button(
            "⤓ Download PNG",
            data=img_to_png_bytes(ss.current),
            file_name="edited.png",
            mime="image/png",
            use_container_width=True,
        )

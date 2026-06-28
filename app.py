"""
AI Creative Studio — Streamlit app with two tools:

  🖼️  Image Editor  — edit an image from a text prompt or one-click style (Gemini)
  🎵  Music Studio   — turn lyrics + a style into a full song (ElevenLabs Music)

Run:
    pip install -r requirements.txt
    # in a .env file (or the environment) set:
    #   GEMINI_API_KEY=...        (image editing + AI lyric writer)
    #   ELEVENLABS_API_KEY=...    (music generation)
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


# ---- Image (Gemini) config -------------------------------------------------- #
ALLOWED_MODELS = ["gemini-3.1-flash-image", "gemini-3-pro-image", "gemini-2.5-flash-image"]
DEFAULT_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
RESOLUTIONS = ["1K", "2K", "4K"]
ASPECT_RATIOS = ["Auto", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"]
LYRICS_MODEL = os.environ.get("GEMINI_TEXT_MODEL", "gemini-2.5-flash")

# One-click image styles → the instruction sent to the model.
CUSTOM_LABEL = "✍️ Custom instruction…"
IMAGE_PRESETS = {
    "🎨 Watercolor painting": "Transform this photo into a soft, artistic watercolor painting while keeping the subject recognizable.",
    "✏️ Pencil sketch": "Turn this image into a detailed hand-drawn black-and-white pencil sketch.",
    "🧸 3D animated character": "Restyle the main subject as a charming 3D animated movie character with soft cinematic lighting.",
    "💥 Pop art": "Convert this into bold pop-art with bright flat colors, high contrast, and halftone dots.",
    "🎭 Anime / cartoon": "Restyle this image as vibrant, detailed anime artwork.",
    "🦸 Comic book": "Restyle this image as a bold comic-book illustration with inked outlines and cel shading.",
    "🌃 Cyberpunk neon": "Reimagine this scene with a neon cyberpunk aesthetic: glowing lights and a moody atmosphere.",
    "📷 Black & white": "Convert this to a striking high-contrast black-and-white photograph.",
    "🎞️ Vintage film": "Give this a vintage 1970s film look with warm, faded tones and subtle grain.",
    "🌅 Dramatic sunset sky": "Replace the sky with a dramatic golden-hour sunset, matching the scene's lighting.",
    "❄️ Add snow": "Add gentle falling snow and a cold, wintry atmosphere to the scene.",
    "✨ Enhance & sharpen": "Enhance this photo: improve lighting, color balance, and sharpness. Keep it photorealistic.",
    "🧹 Remove background (white)": "Remove the background entirely and replace it with a clean solid white background.",
    "🌫️ Blur background (portrait)": "Blur the background for a flattering shallow depth-of-field portrait effect; keep the subject sharp.",
}

# ---- Music (ElevenLabs) config ---------------------------------------------- #
MUSIC_MODEL = os.environ.get("ELEVENLABS_MUSIC_MODEL", "music_v1")
MUSIC_MIN_S, MUSIC_MAX_S = 10, 180
MUSIC_GENRES = ["Pop", "Synthwave", "Lo-fi hip hop", "Rock", "Acoustic / folk",
                "R&B / soul", "EDM / dance", "Cinematic / orchestral", "Jazz",
                "Country", "Hip hop / rap", "Reggae", "Metal", "Ambient"]
MUSIC_MOODS = ["Happy / upbeat", "Chill / relaxed", "Emotional / sad",
               "Epic / powerful", "Romantic", "Dark / moody", "Dreamy", "Energetic"]
MUSIC_VOCALS = ["Female vocals", "Male vocals", "Duet", "Choir / group", "No preference"]
MUSIC_TEMPOS = ["Slow", "Medium", "Upbeat", "Fast"]
LENGTH_PRESETS = {"Short (15s)": 15, "Standard (30s)": 30, "Long (60s)": 60, "Extended (120s)": 120}


def get_image_key():
    """Accept either GEMINI_API_KEY or GOOGLE_API_KEY."""
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def get_music_key():
    """Accept ELEVENLABS_API_KEY / ELEVEN_API_KEY / ELEVENLABS_KEY."""
    return (
        os.environ.get("ELEVENLABS_API_KEY")
        or os.environ.get("ELEVEN_API_KEY")
        or os.environ.get("ELEVENLABS_KEY")
    )


# --------------------------------------------------------------------------- #
# Image editing (Gemini)
# --------------------------------------------------------------------------- #
def run_edit(image: Image.Image, prompt: str, model: str,
             resolution: str = "1K", aspect_ratio: str = "Auto") -> Image.Image:
    """Send the image + prompt to Gemini and return the edited image."""
    from google import genai
    from google.genai import types

    image_cfg = {}
    if model.startswith("gemini-3"):
        image_cfg["image_size"] = resolution
        if aspect_ratio != "Auto":
            image_cfg["aspect_ratio"] = aspect_ratio

    config = types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(**image_cfg) if image_cfg else None,
    )

    client = genai.Client(
        api_key=get_image_key(),
        http_options=types.HttpOptions(timeout=180_000),
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

    texts = [p.text for p in parts if getattr(p, "text", None)]
    raise RuntimeError(
        "Gemini returned no image. "
        + (" ".join(texts) if texts else "Try rephrasing the prompt.")
    )


def write_lyrics(theme: str, genre: str, mood: str) -> str:
    """Use a Gemini text model to draft song lyrics from a theme."""
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=get_image_key(),
        http_options=types.HttpOptions(timeout=60_000),
    )
    prompt = (
        f"Write original song lyrics about: {theme}.\n"
        f"Genre: {genre}. Mood: {mood}.\n"
        "Use section tags like [Verse], [Chorus], and [Bridge]. "
        "Keep it concise — around 12 to 20 lines total. "
        "Return ONLY the lyrics, with no title or commentary."
    )
    resp = client.models.generate_content(model=LYRICS_MODEL, contents=prompt)
    return (resp.text or "").strip()


def img_to_png_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Music generation (ElevenLabs Music)
# --------------------------------------------------------------------------- #
def build_style_string(genre, mood, vocals, tempo, extra) -> str:
    parts = [genre, mood, f"{tempo} tempo" if tempo else None,
             vocals if vocals and vocals != "No preference" else None,
             (extra or "").strip() or None]
    return ", ".join(p for p in parts if p)


def build_music_prompt(lyrics: str, style: str, instrumental: bool) -> str:
    """Compose a single prompt describing the song for the music model."""
    style = style.strip()
    lyrics = lyrics.strip()
    if instrumental or not lyrics:
        return style or "An expressive instrumental piece."
    head = style or "A song"
    return f"{head}. Sing exactly these lyrics, do not change the words:\n\n{lyrics}"


def compose_music(lyrics: str, style: str, length_s: int,
                  instrumental: bool = False) -> bytes:
    """Generate a song with ElevenLabs Music and return MP3 bytes."""
    from elevenlabs import ElevenLabs
    from elevenlabs.core.api_error import ApiError

    client = ElevenLabs(api_key=get_music_key())
    try:
        audio = client.music.compose(
            prompt=build_music_prompt(lyrics, style, instrumental),
            music_length_ms=int(length_s) * 1000,
            model_id=MUSIC_MODEL,
            force_instrumental=instrumental,
            output_format="mp3_44100_128",
        )
        return audio if isinstance(audio, (bytes, bytearray)) else b"".join(audio)
    except ApiError as exc:
        raise RuntimeError(_format_eleven_error(exc)) from exc


def _format_eleven_error(exc) -> str:
    """Turn an opaque ElevenLabs ApiError into a readable, actionable message."""
    body = getattr(exc, "body", None)
    detail = body.get("detail") if isinstance(body, dict) else None
    status = (detail or {}).get("status") if isinstance(detail, dict) else None
    message = (detail or {}).get("message") if isinstance(detail, dict) else None
    code = getattr(exc, "status_code", "?")

    if status == "missing_permissions":
        return (
            "Your ElevenLabs API key lacks the **music_generation** permission. "
            "In elevenlabs.io → Profile → API Keys, edit the key and enable "
            "‘Music’ (or use a key with no scope restrictions), then restart."
        )
    if code == 401:
        return f"ElevenLabs auth failed (401): {message or 'check your API key.'}"
    return f"ElevenLabs error {code}: {message or body or exc}"


# --------------------------------------------------------------------------- #
# Page setup + session state
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="AI Creative Studio", page_icon="🎨", layout="wide")

ss = st.session_state
ss.setdefault("original", None)
ss.setdefault("current", None)
ss.setdefault("upload_id", None)
ss.setdefault("song", None)
ss.setdefault("song_label", "")
ss.setdefault("lyrics_text", "")


# --------------------------------------------------------------------------- #
# Image Editor tool
# --------------------------------------------------------------------------- #
def render_image_editor():
    st.title("🪄 Image Editor")
    st.caption("Upload a photo, pick a one-click style (or write your own), and "
               "Gemini edits it. Each result feeds back in so you can keep refining.")

    key = get_image_key()
    if not key:
        st.error(
            "No image API key. Add **GEMINI_API_KEY** (or **GOOGLE_API_KEY**) to "
            "`.env`, then restart. Get one at https://aistudio.google.com/apikey"
        )

    with st.sidebar:
        st.subheader("Upload")
        uploaded = st.file_uploader(
            "Image", type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=False, label_visibility="collapsed",
        )
        if uploaded is not None and uploaded.file_id != ss.upload_id:
            img = Image.open(uploaded).convert("RGBA")
            ss.original = img
            ss.current = img
            ss.upload_id = uploaded.file_id

        with st.expander("⚙️ Advanced (model & quality)"):
            model = st.selectbox(
                "Model", ALLOWED_MODELS,
                index=ALLOWED_MODELS.index(DEFAULT_MODEL) if DEFAULT_MODEL in ALLOWED_MODELS else 0,
                help="Flash = fast. Pro = best quality but slower.",
            )
            is_gemini3 = model.startswith("gemini-3")
            resolution = st.selectbox(
                "Resolution", RESOLUTIONS, index=0, disabled=not is_gemini3,
                help="1K is ~5× faster than 2K.",
            )
            aspect_ratio = st.selectbox(
                "Aspect ratio", ASPECT_RATIOS, index=0, disabled=not is_gemini3,
                help="‘Auto’ keeps the source proportions.",
            )

        if st.button("↩︎ Reset to original", use_container_width=True,
                     disabled=ss.original is None):
            ss.current = ss.original
            st.rerun()

    if ss.current is None:
        st.info("⬅️ Upload an image in the sidebar to get started.")
        return

    st.subheader("Pick a style")
    preset_names = list(IMAGE_PRESETS.keys())
    choice = st.pills(
        "Style", preset_names + [CUSTOM_LABEL],
        selection_mode="single", default=preset_names[0], label_visibility="collapsed",
    ) or preset_names[0]

    if choice == CUSTOM_LABEL:
        prompt = st.text_area(
            "Describe your edit",
            placeholder="e.g. add a small red boat on the water, make it sunset…",
            height=90,
        )
    else:
        prompt = IMAGE_PRESETS[choice]
        st.caption(f"➡️ {prompt}")

    generate = st.button("✨ Apply edit", type="primary",
                         use_container_width=True, disabled=not key)
    if generate:
        if not prompt.strip():
            st.warning("Pick a style or write a custom instruction first.")
        else:
            try:
                with st.spinner(f"Editing with {model} at {resolution}…"):
                    ss.current = run_edit(ss.current, prompt.strip(), model,
                                          resolution, aspect_ratio)
                st.success("Done ✨ — pick another style to keep refining.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"AI edit failed: {exc}")

    left, right = st.columns(2)
    with left:
        st.subheader("Original")
        if ss.original is not None:
            st.image(ss.original, use_container_width=True)
    with right:
        st.subheader("Current")
        st.image(ss.current, use_container_width=True)
        st.download_button(
            "⤓ Download PNG", data=img_to_png_bytes(ss.current),
            file_name="edited.png", mime="image/png", use_container_width=True,
        )


# --------------------------------------------------------------------------- #
# Music Studio tool
# --------------------------------------------------------------------------- #
def render_music_studio():
    st.title("🎵 Music Studio")
    st.caption("Pick a style, write (or AI-generate) lyrics, and ElevenLabs "
               "composes a full song with vocals — or go instrumental.")

    key = get_music_key()
    if not key:
        st.error(
            "No music API key. Add **ELEVENLABS_API_KEY** to `.env`, then restart. "
            "Get one at https://elevenlabs.io → Profile → API Keys."
        )

    st.subheader("1 · Pick your style")
    genre = st.pills("Genre", MUSIC_GENRES, selection_mode="single",
                     default=MUSIC_GENRES[0]) or MUSIC_GENRES[0]
    mood = st.pills("Mood", MUSIC_MOODS, selection_mode="single",
                    default=MUSIC_MOODS[0]) or MUSIC_MOODS[0]
    col1, col2 = st.columns(2)
    with col1:
        tempo = st.pills("Tempo", MUSIC_TEMPOS, selection_mode="single",
                         default="Medium") or "Medium"
    with col2:
        vocals = st.pills("Vocals", MUSIC_VOCALS, selection_mode="single",
                          default=MUSIC_VOCALS[0]) or MUSIC_VOCALS[0]
    extra = st.text_input("Extra notes (optional)", placeholder="e.g. 90 BPM, piano riff")

    st.subheader("2 · Length")
    length_label = st.pills("Length", list(LENGTH_PRESETS.keys()),
                            selection_mode="single", default="Standard (30s)",
                            label_visibility="collapsed") or "Standard (30s)"
    length_s = LENGTH_PRESETS[length_label]
    instrumental = st.toggle("🎹 Instrumental (no vocals / lyrics)")

    style = build_style_string(genre, mood, vocals, tempo, extra)
    st.markdown(f"**Selected style:** {style}")

    if not instrumental:
        st.subheader("3 · Lyrics")
        src = st.pills("Lyrics source", ["✍️ Write my own", "🤖 Generate with AI"],
                       selection_mode="single", default="✍️ Write my own",
                       label_visibility="collapsed") or "✍️ Write my own"
        if src.endswith("with AI"):
            has_gem = get_image_key() is not None
            theme = st.text_input("Song theme / topic",
                                  placeholder="e.g. chasing dreams in a big city at night")
            if st.button("🤖 Write lyrics for me", disabled=not has_gem):
                if not theme.strip():
                    st.warning("Describe a theme first.")
                else:
                    try:
                        with st.spinner("Writing lyrics…"):
                            ss.lyrics_text = write_lyrics(theme, genre, mood)
                        st.rerun()
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Couldn't write lyrics: {exc}")
            if not has_gem:
                st.caption("⚠️ AI lyrics need a GEMINI_API_KEY.")

        st.text_area(
            "Lyrics", key="lyrics_text", height=240,
            placeholder="[Verse]\nCity lights are calling out my name\n\n"
                        "[Chorus]\nWe were never meant to stay the same…",
            help="Use [Verse], [Chorus], [Bridge] tags to shape the song.",
        )

    st.subheader("4 · Compose" if not instrumental else "3 · Compose")
    make = st.button("🎼 Compose song", type="primary",
                     use_container_width=True, disabled=not key)

    if make:
        if not instrumental and not ss.lyrics_text.strip():
            st.warning("Add some lyrics (or use the AI writer), or tick ‘Instrumental’.")
        else:
            try:
                with st.spinner(f"Composing ~{length_s}s of music…"):
                    ss.song = compose_music(ss.lyrics_text, style, length_s, instrumental)
                    ss.song_label = f"{style} · {length_s}s"
                st.success("Done 🎶")
            except Exception as exc:  # noqa: BLE001
                ss.song = None
                st.error(f"Music generation failed: {exc}")

    if ss.song:
        st.subheader("Your track")
        st.caption(ss.song_label)
        st.audio(ss.song, format="audio/mp3")
        st.download_button(
            "⤓ Download MP3", data=ss.song, file_name="song.mp3",
            mime="audio/mpeg", use_container_width=True,
        )


# --------------------------------------------------------------------------- #
# Top-level navigation
# --------------------------------------------------------------------------- #
st.sidebar.title("🎨 AI Creative Studio")
tool = st.sidebar.radio("Tool", ["🎵 Music Studio", "🖼️ Image Editor"]) or "🎵 Music Studio"
st.sidebar.divider()

if tool.endswith("Image Editor"):
    render_image_editor()
else:
    render_music_studio()

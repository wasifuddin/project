# 🎨 AI Creative Studio (Streamlit)

Two AI tools in one app, switchable from the sidebar:

- **🪄 Image Editor** — edit an image from a text prompt (Google Gemini)
- **🎵 Music Studio** — turn lyrics + a style into a full song (ElevenLabs Music)

## Setup

```bash
pip install -r requirements.txt
```

Put your keys in a `.env` file in this folder:

```
GEMINI_API_KEY=AIza...          # image editing (or GOOGLE_API_KEY)
ELEVENLABS_API_KEY=sk_...        # music generation
```

- Image key: <https://aistudio.google.com/apikey>
- Music key: <https://elevenlabs.io> → Profile → API Keys

Each tool only needs its own key — you can use one without the other. Then run:

```bash
streamlit run app.py
```

Streamlit opens the app in your browser (default <http://localhost:8501>).

> The app opens on **Music Studio** by default; switch tools from the sidebar.

## 🎵 Music Studio

1. **Pick your style** by tapping tags: Genre, Mood, Tempo, Vocals (single-select
   pills), plus an optional notes field. The composed style is shown back to you.
2. Choose a **length** tag (15s / 30s / 60s / 120s).
3. **Lyrics:** write your own (with `[Verse]` / `[Chorus]` tags), or pick
   *Generate with AI*, enter a theme, and **Write lyrics for me** drafts them
   (uses your Gemini key). Toggle **Instrumental** to skip lyrics entirely.
4. **Compose song** — play it inline and **Download MP3**.

## 🪄 Image Editor

1. **Upload** an image in the sidebar (PNG / JPG / WebP).
2. **Pick a style** tag — Watercolor, Pencil sketch, Pop art, Anime, Cyberpunk,
   Black & white, Remove background, Blur background, and more — or tap
   *Custom instruction…* to type your own edit.
3. (Optional) open **Advanced** in the sidebar for model / resolution / aspect.
4. Click **Apply edit**. The result feeds back in, so you can stack styles.
   **Download PNG** when happy; **Reset to original** starts over.

Uses ElevenLabs Music (`music_v1`); override the model via `ELEVENLABS_MUSIC_MODEL`.

## Models

The picker offers, best/newest first:

| Model                    | Notes                                  |
|--------------------------|----------------------------------------|
| `gemini-3-pro-image`     | **Default.** Highest quality (Pro).    |
| `gemini-3.1-flash-image` | Latest flash — faster / cheaper.       |
| `gemini-2.5-flash-image` | Previous-gen flash.                    |

Override the default without code changes via `GEMINI_IMAGE_MODEL` in `.env`.

### Speed vs. quality

The Gemini 3 models expose a **Resolution** control (1K / 2K / 4K) in the
sidebar. Resolution is the main speed lever:

| Resolution | Approx. time (Pro) | Output     |
|------------|--------------------|------------|
| **1K** (default) | ~18s         | 1024 px    |
| 2K               | ~85s         | 2048 px    |
| 4K               | longer       | 4096 px    |

For fast iteration, stay at **1K** (or pick `gemini-3.1-flash-image`), then bump
to 2K/4K for a final high-res render. An **Aspect ratio** control is also
available; *Auto* keeps the source proportions. `gemini-2.5-flash-image` always
outputs ~1K and ignores both controls.

## Configuration

| Env var               | Purpose                                          |
|-----------------------|--------------------------------------------------|
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Required. Your Gemini API key.     |
| `GEMINI_IMAGE_MODEL`  | Optional. Default model (`gemini-3-pro-image`).  |

## Notes

- Everything lives in a single file: `app.py`.
- Gemini image generation may require billing enabled on your Google AI / Cloud
  project depending on the model and your quota.
```

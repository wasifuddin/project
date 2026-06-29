# AI Creative Studio (Streamlit)

Two AI tools in one app, switchable from the sidebar:

- **Image Editor** - edit an image from a text prompt or one-click style (Google Gemini)
- **Music Studio** - turn lyrics + a style into a full song (ElevenLabs Music)

## Setup

```bash
pip install -r requirements.txt
```

Put your keys in a `.env` file in this folder:

```
GEMINI_API_KEY=AIza...          # image editing + AI lyric writer (or GOOGLE_API_KEY)
ELEVENLABS_API_KEY=sk_...        # music generation
```

- Image key: <https://aistudio.google.com/apikey>
- Music key: <https://elevenlabs.io> (Profile -> API Keys; the key needs the
  Music Generation permission)

Each tool only needs its own key - you can use one without the other. Then run:

```bash
streamlit run app.py
```

Streamlit opens the app in your browser (default <http://localhost:8501>). The app
opens on Music Studio by default; switch tools from the sidebar.

## Music Studio

1. **Choose your sound** - two paths:
   - **Quick preset:** one tap on a ready-made combo (Travel reel, Romantic,
     Gym pump, Aesthetic, Party, Sad, Gaming, Cinematic).
   - **Build my own:** set distinct tags yourself - Genre, Mood, Tone (multi),
     Use-case, Tempo, Vocals. The exact style sent to the AI is shown back to you.
2. Pick a **length** (15s / 30s / 60s / 120s) and optionally toggle **Instrumental**.
3. **Lyrics:** write your own (with `[Verse]` / `[Chorus]` tags), or pick
   *Generate with AI*. You can enter a theme, **upload the photos you plan to
   post** (optional) so the lyrics are written about what's in them, or both;
   then **Write lyrics for me** drafts them. Lyrics are sized to the chosen
   length automatically (a short hook for 15s up to a full song for 120s).
4. **Compose song** - play it inline and **Download MP3**.

Uses ElevenLabs Music (`music_v1`); override via `ELEVENLABS_MUSIC_MODEL`.

## Image Editor

1. **Upload** an image in the sidebar (PNG / JPG / WebP).
2. **Pick a style** tag - Watercolor, Pencil sketch, Pop art, Anime, Cyberpunk,
   Black & white, Remove background, Blur background, and more - or tap
   *Custom instruction* to type your own edit.
3. (Optional) open **Advanced** in the sidebar for model / resolution / aspect.
4. Click **Apply edit**. The result feeds back in, so you can stack styles.
   **Download PNG** when happy; **Reset to original** starts over.

### Image models and speed

| Model                    | Notes                                   |
|--------------------------|-----------------------------------------|
| `gemini-3.1-flash-image` | Default. Fast / cheaper.                |
| `gemini-3-pro-image`     | Best quality (Pro), but slower.         |
| `gemini-2.5-flash-image` | Previous-gen flash (always ~1K).        |

Resolution (Gemini 3 models) is the main speed lever: 1K is ~18s, 2K is ~85s, 4K
longer. Use 1K for iteration, bump to 2K/4K for a final render. Override the
default model via `GEMINI_IMAGE_MODEL` in `.env`.

## Configuration

| Env var                             | Purpose                                   |
|-------------------------------------|-------------------------------------------|
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Image editing + AI lyric writer.          |
| `ELEVENLABS_API_KEY`                | Music generation.                         |
| `GEMINI_IMAGE_MODEL`                | Optional. Default `gemini-3.1-flash-image`. |
| `ELEVENLABS_MUSIC_MODEL`            | Optional. Default `music_v1`.             |

## Notes

- Everything lives in a single file: `app.py`.
- Image/music generation may require billing enabled on the respective accounts.

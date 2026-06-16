# 🪄 AI Image Editor (Google Gemini · Streamlit)

A focused Streamlit app: upload an image, describe a change in plain language,
and a Gemini image model edits it. Each result becomes the working image, so you
can keep refining prompt-by-prompt.

## Setup

```bash
pip install -r requirements.txt
```

Put your key in a `.env` file in this folder (either name works):

```
GEMINI_API_KEY=AIza...
# or
GOOGLE_API_KEY=AIza...
```

Get a key at <https://aistudio.google.com/apikey>. Then run:

```bash
streamlit run app.py
```

Streamlit opens the app in your browser (default <http://localhost:8501>).

## How to use

1. Upload an image in the sidebar (PNG / JPG / WebP).
2. Type a prompt (e.g. *"make it look like a watercolor painting"*).
3. Pick a model, then **Generate edit**.
4. **Download PNG**, or edit again to refine. **Reset to original** restores the
   uploaded image.

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

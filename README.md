# AI Vision Glasses Demo

A tiny, educational demo that mirrors the **glasses → phone → server → vision AI → spoken answer** loop. The backend accepts an image upload, forwards it to a vision-capable LLM (OpenAI compatible), and returns an answer plus a short explanation. A lightweight web UI lets you capture/upload a photo, send it to the API, and play back the result via the browser's text-to-speech.

> This project is intended for teacher training and awareness, **not** covert exam use. If the `OPENAI_API_KEY` is missing, the API responds with a clear fallback message so demos remain transparent.

## Quick start

1. Install dependencies (preferably in a virtual environment):

   ```bash
   pip install -r requirements.txt
   ```

2. Add your API key (required for live vision answers):

   - **You do not need to share your key with anyone.** Keep it local on the machine running the server; the app only reads it from the environment and never uploads or stores it.

   **macOS/Linux (bash/zsh):**

   ```bash
   export OPENAI_API_KEY=sk-...
   # Optional: override model (default gpt-4o-mini)
   export OPENAI_MODEL=gpt-4o
   ```

   **Windows (PowerShell):**

   ```powershell
   setx OPENAI_API_KEY "sk-..."
   setx OPENAI_MODEL "gpt-4o"   # optional
   # restart the shell so the variables are available
   ```

   **Tip:** if you prefer a `.env` file, copy `.env.example` to `.env` and add your key (and optional `OPENAI_MODEL=...`), then
   run `source .env` before starting the server.

3. Run the server:

   ```bash
   uvicorn app.main:app --reload
   ```

4. Open the demo UI at <http://localhost:8000>. Use the **Ask AI** button to send an image to `/api/solve`. Click **Read aloud** to hear the answer.

## Endpoints

- `GET /health` — uptime probe.
- `POST /api/solve` — multipart form with fields:
  - `image` (required): image upload from glasses/phone.
  - `prompt` (optional): guidance text for the vision model.

Response body:

```json
{
  "answer": "Short headline answer",
  "explanation": "Longer explanation returned by the model",
  "model": "gpt-4o-mini",
  "used_fallback": false
}
```

If no API key is configured, `used_fallback` will be `true` and the payload will explain that the model call was skipped.

## Notes for demos

- The HTML page is served directly from `/` and lives in `frontend/index.html`.
- The browser uses the Web Speech API for audio playback; no extra setup needed on Chrome, Edge, or Safari.
- For production, place the server behind HTTPS and tighten CORS/auth as needed.

## Using Meta Ray-Ban Smart Glasses (Gen 2)

You can keep the pipeline simple and visible for teachers while still capturing photos hands-free:

1. **Pair the glasses in Meta View** and enable automatic photo import to your phone’s gallery.
2. **Run the server** on a laptop or cloud host with network access that your phone can reach (e.g., `uvicorn app.main:app --host 0.0.0.0 --port 8000`).
3. On your phone, **open the demo page** at `http://<your-server>:8000`, tap the file picker, and choose the latest glasses photo (or capture directly with the phone camera if the glasses fail).
4. Tap **Ask AI** to send the image to `/api/solve`; tap **Read aloud** to hear the answer via your phone’s speaker or connected earbuds.
5. If you want one-tap automation, create a **shortcut/automation** on your phone that grabs the most recent glasses photo and POSTs it to `/api/solve`—the response JSON’s `answer` field can be spoken with the phone’s TTS.

## FAQ

**Do you need my API key?**

No. Keep your OpenAI (or compatible) API key private on the machine that runs the server. The app reads it from the environment
when handling your request and does not send, log, or store the key anywhere else. For development, you can set it with
`export OPENAI_API_KEY=...` or by filling in `.env` (see `.env.example`), but never commit real keys to version control.

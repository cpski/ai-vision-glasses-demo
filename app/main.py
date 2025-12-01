import base64
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI Vision Glasses Demo",
    description=(
        "Educational demo showing how a glasses → phone → server pipeline can call a vision AI model "
        "and read back an answer."
    ),
    version="0.1.0",
)


class SolveResponse(BaseModel):
    answer: str
    explanation: str
    model: str
    used_fallback: bool = False


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def read_root() -> HTMLResponse:
    """Serve the single-page demo UI."""
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=500, detail="Demo page is missing")
    return HTMLResponse(INDEX_FILE.read_text(encoding="utf-8"))


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Simple health endpoint for uptime checks."""
    return {"status": "ok"}


def _openai_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not configured; returning fallback response")
        return None
    return OpenAI(api_key=api_key)


def _call_vision_model(image_bytes: bytes, prompt: str) -> tuple[str, str, str]:
    client = _openai_client()
    if client is None:
        answer = (
            "Vision model not configured. Set OPENAI_API_KEY to enable live analysis; "
            "this fallback just echoes the demo intent."
        )
        explanation = (
            "In a real deployment, this endpoint would send the image to a vision model such as "
            "gpt-4o to extract the question and answer it."
        )
        return answer, explanation, "fallback"

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    image_url = f"data:image/jpeg;base64,{base64_image}"

    system_prompt = (
        "You are an educational assistant helping teachers understand AI-assisted cheating. "
        "Read the attached photo, identify any question text, and provide a concise answer plus a "
        "brief explanation that could be spoken aloud."
    )

    logger.info("Calling OpenAI vision model %s", model)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        max_tokens=350,
    )

    message_content = response.choices[0].message.content or ""
    explanation = message_content
    answer = message_content.split("\n", 1)[0].strip()

    return answer, explanation, model


@app.post("/api/solve", response_model=SolveResponse)
async def solve_question(
    image: UploadFile = File(..., description="Photo captured from glasses or phone"),
    prompt: str = Form(
        "Identify the question in this photo and answer it clearly in one or two sentences.",
        description="Optional guidance for the vision model",
    ),
) -> SolveResponse:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image upload")

    try:
        answer, explanation, model = _call_vision_model(image_bytes, prompt)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Vision model call failed")
        raise HTTPException(status_code=502, detail=f"Model call failed: {exc}") from exc

    return SolveResponse(
        answer=answer,
        explanation=explanation,
        model=model,
        used_fallback=model == "fallback",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)

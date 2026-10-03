import base64
import json
import os

import httpx
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="TinkerSight API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-vl:2b")


class GuideResponse(BaseModel):
    appliance: str
    model: str | None = None
    observation: str
    confidence: str
    step: str
    question: str | None = None
    safety: str
    manual_note: str


SYSTEM_PROMPT = """You are TinkerSight, a cautious household technical guide.
Your job is to inspect a photo and help an ordinary person operate everyday equipment.

Rules:
- Describe only what is actually visible.
- Do not invent a model number. If it is not readable, return null.
- Do not claim an official manual was checked unless manual text is supplied.
- Give short, concrete, layman-friendly guidance.
- Prefer visible descriptions such as "green button" or "second port from the left" over technical names.
- If the image is unclear, say what needs to be photographed again.
- Never give instructions for exposed mains electricity, gas systems, internal repairs, sparks, burning smells, or other hazardous intervention. Set safety to "stop" in those cases.
- Return JSON only.
"""

USER_TEMPLATE = """The user wants to do this:
{goal}

Analyze the uploaded photo.

Return exactly this JSON shape:
{{
  "appliance": "what the device appears to be",
  "model": "exact model if clearly readable, otherwise null",
  "observation": "one short sentence about what is visible",
  "confidence": "high|medium|low",
  "step": "the safest useful next action in simple language",
  "question": "one short question if information is missing, otherwise null",
  "safety": "normal|caution|stop",
  "manual_note": "say 'Manual required' because the official manufacturer manual has not yet been retrieved"
}}
"""


@app.get("/health")
def health():
    return {"status": "ok", "service": "tinkersight", "model": OLLAMA_MODEL}


@app.post("/api/guide", response_model=GuideResponse)
async def guide(image: UploadFile = File(...), goal: str = Form(...)):
    image_bytes = await image.read()
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_TEMPLATE.format(goal=goal),
                "images": [encoded],
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        return GuideResponse(
            appliance="I couldn't inspect the photo yet.",
            model=None,
            observation="The local vision model is not reachable.",
            confidence="low",
            step="Start Ollama and make sure the TinkerSight vision model is installed.",
            question=None,
            safety="caution",
            manual_note=f"Local AI connection error: {exc}",
        )

    raw = data.get("message", {}).get("content", "")
    try:
        result = json.loads(raw)
        return GuideResponse(**result)
    except (json.JSONDecodeError, TypeError, ValueError):
        return GuideResponse(
            appliance="Unknown device",
            model=None,
            observation=raw[:300] or "The model returned no usable result.",
            confidence="low",
            step="Take a clearer photo showing the full control panel.",
            question=None,
            safety="caution",
            manual_note="Manual required",
        )

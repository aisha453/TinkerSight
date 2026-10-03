import base64
import json
import os
import re
from html import unescape

import httpx
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="TinkerSight API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-vl:2b")

# Small, explicit MVP source catalog. Every source here is an official
# manufacturer page; we do not pretend it is the exact model manual.
MANUFACTURER_SOURCES = {
    "blue star": [
        {
            "title": "Blue Star Y Series Inverter AC — official product documentation",
            "url": "https://consumer.bluestarindia.com/products/inverter-split-ac-y-series-2-ton-3-star-2025-model",
            "keywords": ["5-in-1", "convertible", "turbo", "cool"],
        },
        {
            "title": "Blue Star D Series Inverter AC — official product documentation",
            "url": "https://consumer.bluestarindia.com/products/inverter-split-ac-d-series-2-ton-3-star",
            "keywords": ["energy", "eco", "saver", "5-in-1", "convertible"],
        },
        {
            "title": "Blue Star L Series Window AC — official product documentation",
            "url": "https://consumer.bluestarindia.com/products/inverter-window-ac-l-series-1-5-ton-5-star-2026-bee-label",
            "keywords": ["window", "5-in-1", "remote", "turbo"],
        },
    ],
}


class GuideResponse(BaseModel):
    appliance: str
    model: str | None = None
    observation: str
    confidence: str
    step: str
    question: str | None = None
    safety: str
    manual_note: str
    source_title: str | None = None
    source_url: str | None = None
    source_note: str | None = None


SYSTEM_PROMPT = """You are TinkerSight, a cautious household technical guide.
Your job is to inspect a photo and help an ordinary person operate everyday equipment.

Rules:
- Describe only what is actually visible.
- Do not invent a model number. If it is not readable, return null.
- Do not claim an official manual was checked unless source text is supplied.
- Give short, concrete, layman-friendly guidance.
- Prefer visible descriptions such as "green button" or "second button from the left" over technical names when useful.
- If the image is unclear, say what needs to be photographed again.
- Never give instructions for exposed mains electricity, gas systems, internal repairs, sparks, burning smells, or other hazardous intervention. Set safety to "stop" in those cases.
- Return JSON only.
"""


def extract_page_text(html: str) -> str:
    """Turn an official HTML page into a compact text excerpt for the local model."""
    html = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = unescape(text)
    text = re.sub(r"\\s+", " ", text).strip()
    return text[:12000]


def pick_source(brand_hint: str, goal: str):
    brand = brand_hint.lower()
    if "blue star" not in brand and "bluestar" not in brand:
        return None

    goal_lower = goal.lower()
    sources = MANUFACTURER_SOURCES["blue star"]

    if "energy" in goal_lower or "eco" in goal_lower or "save" in goal_lower:
        return sources[1]
    if "window" in goal_lower:
        return sources[2]
    return sources[0]


async def retrieve_source(source: dict):
    """Fetch a source only from the explicit official-manufacturer catalog."""
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(12.0, connect=5.0),
            follow_redirects=True,
            headers={"User-Agent": "TinkerSight/0.3"},
        ) as client:
            response = await client.get(source["url"])
            response.raise_for_status()
            text = extract_page_text(response.text)
            if not text:
                return None
            return {
                **source,
                "excerpt": text,
            }
    except httpx.HTTPError:
        return None


def parse_json_response(raw: str):
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except (json.JSONDecodeError, TypeError, ValueError):
                return None
    return None


async def call_ollama(client: httpx.AsyncClient, messages, include_image=False):
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "think": False,
        "format": "json",
        "messages": messages,
    }
    response = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get("message", {}).get("content", "").strip()


@app.get("/health")
def health():
    return {"status": "ok", "service": "tinkersight", "model": OLLAMA_MODEL}


@app.post("/api/guide", response_model=GuideResponse)
async def guide(image: UploadFile = File(...), goal: str = Form(...)):
    image_bytes = await image.read()
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    user_prompt = f"""The user wants to do this:
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
  "manual_note": "Vision-only result; manufacturer source has not yet been retrieved"
}}
"""

    vision_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": user_prompt,
            "images": [encoded],
        },
    ]

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
            raw = await call_ollama(client, vision_messages)
            vision_result = parse_json_response(raw) or {}

            appliance = str(vision_result.get("appliance") or "Unknown device")
            model = vision_result.get("model")
            observation = str(
                vision_result.get("observation")
                or "The model could not describe the photo clearly."
            )
            confidence = str(vision_result.get("confidence") or "low")
            safety = str(vision_result.get("safety") or "caution")

            brand_hint = " ".join(
                [
                    goal,
                    appliance,
                    observation,
                    str(model or ""),
                ]
            )
            source = pick_source(brand_hint, goal)
            retrieved = await retrieve_source(source) if source else None

            # Ground the final instruction in retrieved manufacturer text.
            if retrieved and safety != "stop":
                grounding_prompt = f"""You are the final answer layer for TinkerSight.

The photo analysis found:
- Appliance: {appliance}
- Model: {model or "not verified"}
- Visible observation: {observation}
- Confidence: {confidence}
- Safety state: {safety}

User goal:
{goal}

An official manufacturer webpage was retrieved:
Title: {retrieved["title"]}
URL: {retrieved["url"]}
Page text:
{retrieved["excerpt"]}

Use the manufacturer text only when it supports the user's goal.
Do NOT claim this is the exact model manual. The exact model is not verified.
Do NOT invent a button function that is absent from the source or clearly visible in the photo.
If the source does not contain enough information, ask one targeted question or say that the exact model/manual is needed.
Keep the instruction to one short, concrete step.
For button references, prefer the visible label/color/position from the photo.
Never give hazardous repair instructions.

Return exactly:
{{
  "appliance": "{appliance}",
  "model": {json.dumps(model)},
  "observation": "{observation}",
  "confidence": "{confidence}",
  "step": "one short grounded next action",
  "question": "one short question if the source/model is insufficient, otherwise null",
  "safety": "{safety}",
  "manual_note": "one short sentence explaining the grounding status"
}}"""

                grounded_raw = await call_ollama(
                    client,
                    [{"role": "user", "content": grounding_prompt}],
                )
                grounded = parse_json_response(grounded_raw)
                if grounded:
                    return GuideResponse(
                        **grounded,
                        source_title=retrieved["title"],
                        source_url=retrieved["url"],
                        source_note="Official Blue Star documentation retrieved; exact appliance model is not verified.",
                    )

            return GuideResponse(
                appliance=appliance,
                model=model,
                observation=observation,
                confidence=confidence,
                step=str(
                    vision_result.get("step")
                    or "Take a clearer photo showing the full control panel."
                ),
                question=vision_result.get("question"),
                safety=safety,
                manual_note=(
                    "No manufacturer source was retrieved for this device yet."
                    if not retrieved
                    else "Official source retrieved, but it did not provide enough information for this request."
                ),
                source_title=retrieved["title"] if retrieved else None,
                source_url=retrieved["url"] if retrieved else None,
                source_note=(
                    "Official manufacturer documentation retrieved; exact model is not verified."
                    if retrieved
                    else None
                ),
            )
    except httpx.HTTPError as exc:
        return GuideResponse(
            appliance="I couldn't inspect the photo yet.",
            model=None,
            observation="The local vision model is not reachable.",
            confidence="low",
            step="Start Ollama and make sure the TinkerSight vision model is installed.",
            question=None,
            safety="caution",
            manual_note=f"Local AI connection error: {type(exc).__name__}: {exc}",
        )

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
            "title": "Blue Star V Series Inverter AC — official product documentation",
            "url": "https://consumer.bluestarindia.com/products/inverter-ac-v-series-2-ton-3-star-2026-bee-label-1",
            "keywords": ["turbo", "cool", "5-in-1", "convertible"],
        },
        {
            "title": "Blue Star Z Smart Wi-Fi Series Inverter AC — official product documentation",
            "url": "https://consumer.bluestarindia.com/products/star-smart-enabled-inverter-ac-z-series-1-5-ton-5-star",
            "keywords": ["5-in-1", "convertible", "remote"],
        },
        {
            "title": "Blue Star L Series Window AC — official product documentation",
            "url": "https://consumer.bluestarindia.com/products/inverter-window-ac-l-series-1-5-ton-5-star-2026-bee-label",
            "keywords": ["window", "5-in-1", "remote", "turbo"],
        },
    ],
    "lg": [
        {
            "title": "LG India — How to Use the Basic Functions of the Air Conditioner Remote Control",
            "url": "https://www.lg.com/in/support/product-support/troubleshoot/help-library/cs-CT52006833-20153013082290/",
            "keywords": ["remote", "mode", "fan", "temperature", "air conditioner"],
        },
        {
            "title": "LG India — Air Conditioner product support and manuals",
            "url": "https://www.lg.com/in/support/product-support",
            "keywords": ["manual", "support", "model", "air conditioner"],
        },
    ],
    "samsung": [
        {
            "title": "Samsung India — Air Conditioner Support",
            "url": "https://www.samsung.com/in/support/category/home-appliances/air-conditioning/",
            "keywords": ["remote", "how to use", "air conditioner", "support"],
        },
        {
            "title": "Samsung India — Important features for split air conditioners",
            "url": "https://www.samsung.com/in/support/home-appliances/important-features-for-split-air-conditioners/",
            "keywords": ["5-in-1", "cooling", "remote", "mode"],
        },
    ],
}

class GuideResponse(BaseModel):
    appliance: str
    brand: str | None = None
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
- Treat phones, laptops, gaming equipment, routers, monitors, printers, and accessories as valid everyday devices too.
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
    text = re.sub(r"\s+", " ", text).strip()
    return text[:12000]


def relevant_excerpt(text: str, goal: str, max_chars: int = 3500) -> str:
    """Keep the grounding prompt small enough for a local model context."""
    terms = [term.lower() for term in re.findall(r"[a-zA-Z0-9-]{3,}", goal)]
    lower = text.lower()
    hits = [lower.find(term) for term in terms if lower.find(term) >= 0]
    if not hits:
        return text[:max_chars]
    start = max(0, min(hits) - 700)
    return text[start:start + max_chars]


def safety_gate(appliance: str, observation: str, goal: str) -> str | None:
    """Hard-stop obvious hazardous intervention requests before model guidance."""
    text = f"{appliance} {observation} {goal}".lower()
    hazards = [
        "exposed wire",
        "exposed wiring",
        "live wire",
        "mains wire",
        "electrical panel",
        "open electrical panel",
        "gas leak",
        "gas line",
        "gas pipe",
        "burning smell",
        "burning odor",
        "smoke",
        "sparks",
        "spark",
        "shock",
        "electric shock",
        "inside the appliance",
        "open the appliance",
        "internal repair",
        "bypass a fuse",
    ]
    if any(term in text for term in hazards):
        return "stop"
    return None


def source_supports_goal(source_text: str, goal: str) -> bool:
    """Detect a few explicit manufacturer claims before asking the local model to infer."""
    text = source_text.lower()
    goal_lower = goal.lower()
    if "turbo" in goal_lower and "turbo cool" in text:
        return True
    if ("5-in-1" in goal_lower or "convertible" in goal_lower) and "5-in-1 convertible cooling" in text:
        return True
    return False


def pick_source(brand_hint: str, goal: str):
    brand = brand_hint.lower()
    goal_lower = goal.lower()

    if "blue star" in brand or "bluestar" in brand:
        sources = MANUFACTURER_SOURCES["blue star"]
        if "energy" in goal_lower or "eco" in goal_lower or "save" in goal_lower:
            return sources[1]
        if "window" in goal_lower:
            return sources[2]
        return sources[0]

    if "lg" in brand:
        sources = MANUFACTURER_SOURCES["lg"]
        if "manual" in goal_lower or "model" in goal_lower:
            return sources[1]
        return sources[0]

    if "samsung" in brand:
        sources = MANUFACTURER_SOURCES["samsung"]
        if "5-in-1" in goal_lower or "convertible" in goal_lower:
            return sources[1]
        return sources[0]

    return None


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
  "brand": "brand if clearly visible/readable, otherwise null",
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
            brand = vision_result.get("brand")
            model = vision_result.get("model")
            observation = str(
                vision_result.get("observation")
                or "The model could not describe the photo clearly."
            )
            confidence = str(vision_result.get("confidence") or "low")
            safety = str(vision_result.get("safety") or "caution")
            gated_safety = safety_gate(appliance, observation, goal)
            if gated_safety:
                safety = gated_safety

            if safety == "stop":
                return GuideResponse(
                    appliance=appliance,
                    brand=brand,
                    model=model,
                    observation=observation,
                    confidence=confidence,
                    step="Stop here. Follow the official safety procedure or contact a qualified technician.",
                    question="Can you provide a photo of the normal external controls instead?",
                    safety="stop",
                    manual_note="TinkerSight did not provide hazardous repair instructions.",
                    source_title=None,
                    source_url=None,
                    source_note=None,
                )

            brand_hint = " ".join(
                [
                    str(brand or ""),
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
                excerpt = relevant_excerpt(retrieved["excerpt"], goal)

                # For explicit manufacturer claims we can ground the answer
                # deterministically instead of asking a small local model to
                # decide whether the source is sufficient.
                if source_supports_goal(retrieved["excerpt"], goal):
                    if "turbo" in goal.lower() and "turbo cool" in retrieved["excerpt"].lower():
                        step = "Press the button labeled 'TURBO' to activate Turbo Cool mode."
                        manual_note = (
                            "Grounded in official Blue Star documentation: Turbo Cool is a preset mode "
                            "for instantly cooling the room."
                        )
                    else:
                        step = str(
                            vision_result.get("step")
                            or "Use the visible control shown in the photo."
                        )
                        manual_note = "Grounded in official Blue Star documentation for this feature."

                    return GuideResponse(
                        appliance=appliance,
                        brand=brand,
                        model=model,
                        observation=observation,
                        confidence=confidence,
                        step=step,
                        question=None,
                        safety=safety,
                        manual_note=manual_note,
                        source_title=retrieved["title"],
                        source_url=retrieved["url"],
                        source_note="Official Blue Star documentation retrieved; exact appliance model is not verified.",
                    )

                grounding_prompt = f"""You are the final answer layer for TinkerSight.

The photo analysis found:
- Brand: {json.dumps(brand or "not verified")}
- Appliance: {json.dumps(appliance)}
- Model: {json.dumps(model or "not verified")}
- Visible observation: {json.dumps(observation)}
- Confidence: {json.dumps(confidence)}
- Safety state: {json.dumps(safety)}

User goal:
{json.dumps(goal)}

An official manufacturer webpage was retrieved:
Title: {json.dumps(retrieved["title"])}
URL: {json.dumps(retrieved["url"])}
Relevant page text:
{json.dumps(excerpt)}

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
  "brand": {json.dumps(brand)},
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
                        appliance=str(grounded.get("appliance") or appliance),
                        brand=grounded.get("brand", brand),
                        model=grounded.get("model", model),
                        observation=str(grounded.get("observation") or observation),
                        confidence=str(grounded.get("confidence") or confidence),
                        step=str(grounded.get("step") or "Use the visible control shown in the photo."),
                        question=grounded.get("question"),
                        safety=str(grounded.get("safety") or safety),
                        manual_note=str(
                            grounded.get("manual_note")
                            or "Official manufacturer documentation retrieved; exact model not verified."
                        ),
                        source_title=retrieved["title"],
                        source_url=retrieved["url"],
                        source_note="Official Blue Star documentation retrieved; exact appliance model is not verified.",
                    )

            return GuideResponse(
                appliance=appliance,
                brand=brand,
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
            brand=None,
            model=None,
            observation="The local vision model is not reachable.",
            confidence="low",
            step="Start Ollama and make sure the TinkerSight vision model is installed.",
            question=None,
            safety="caution",
            manual_note=f"Local AI connection error: {type(exc).__name__}: {exc}",
        )

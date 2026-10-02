from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI(title="TinkerSight API", version="0.1.0")


class GuideResponse(BaseModel):
    appliance: str
    observation: str
    step: str
    question: str | None = None
    safety: str = "normal"


@app.get("/health")
def health():
    return {"status": "ok", "service": "tinkersight"}


@app.post("/api/guide", response_model=GuideResponse)
async def guide(image: UploadFile = File(...)):
    # Prototype response. The open-weight VLM and manual retrieval layer
    # will replace this mock once the UI flow is validated.
    return GuideResponse(
        appliance="Household appliance",
        observation="I can see the appliance and its control panel.",
        step="Tell me what you want the appliance to do.",
        question="What are you trying to do?",
    )

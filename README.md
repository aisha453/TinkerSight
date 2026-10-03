# TinkerSight

> Everyday technical help, explained like a person standing beside you.

TinkerSight is an open-source, vision-first technical guide for everyday devices, appliances, and equipment. Show it a photo, tell it what you want to do, and it turns what it can see plus verified manufacturer documentation into a simple next action.

## Core idea

**See → Ground → Simplify → Guide**

1. **See** — inspect the user's photo and identify only what is visible.
2. **Ground** — retrieve relevant official manufacturer documentation when a supported source is available.
3. **Simplify** — translate technical language into ordinary words.
4. **Guide** — give one short, safe action and ask for clarification when important information is missing.

TinkerSight is deliberately cautious: it does not claim an exact model or manual match when that has not been verified.

## What it can handle

The prototype is designed for everyday equipment such as:

- washing machines and air conditioners
- laptops, phones, monitors, and printers
- routers and networking equipment
- gaming equipment and accessories
- remotes, control panels, and other visible interfaces

The current manufacturer catalog is intentionally small and explicit. It includes selected official documentation from Blue Star, LG, and Samsung for the prototype.

## Example

Instead of:

> Set the wash temperature to 60°C using the temperature selector.

TinkerSight aims for:

> **Press the temperature button 3 times.**

For a supported manufacturer feature, it can also show the official source used for grounding.

## Safety

TinkerSight is intended for safe operation guidance and low-risk troubleshooting. It must not provide step-by-step instructions for exposed mains electricity, gas systems, internal repairs, sparks, burning smells, or other hazardous interventions. In those cases it stops and directs the user toward the official safety procedure or a qualified professional.

## Architecture

- **Frontend:** React + Vite + CSS
- **Backend:** FastAPI
- **AI:** Qwen3-VL 2B through local Ollama inference
- **Grounding:** selected official manufacturer webpages
- **Image handling:** browser-side resizing before local vision inference

## Run locally

### Backend

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Make sure Ollama is running with the configured vision model. By default TinkerSight uses `qwen3-vl:2b`.

## Project status

Early working prototype built during the Hacktoberfest Weekend 2026 Build for a Friend challenge.

The project is intentionally small: the goal is to demonstrate a trustworthy interaction pattern rather than pretend to be a complete universal technical-support system.

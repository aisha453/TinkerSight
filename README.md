# TinkerSight

> Everyday technical help, explained like a person standing beside you.

TinkerSight is an open-source, vision-first household technical guide. It is designed to help people understand and operate everyday appliances and equipment without forcing them to decode technical manuals.

## Core idea

**See → Ground → Simplify → Guide**

1. The user shows TinkerSight an appliance or control panel.
2. TinkerSight identifies what it can see and, when available, the exact model.
3. It grounds instructions in the manufacturer's official documentation.
4. It turns technical instructions into short, visual, layman-friendly actions.
5. It gives one step at a time and checks before continuing.

## MVP

The first prototype focuses on everyday appliance operation, starting with washing-machine style control panels and expanding to routers, air conditioners, microwaves, printers and other household equipment.

### Example

Instead of:

> Set the wash temperature to 60°C using the temperature selector.

TinkerSight should say:

> **Press the temperature button 3 times.**

The goal is not to replace a technician or the manufacturer manual. It is to make everyday technical information understandable.

## Safety

TinkerSight must not provide step-by-step instructions for exposed mains electricity, gas systems, dangerous repairs, or other hazardous interventions. In those cases it should stop, explain the risk in simple language, and direct the user to the official manual or a qualified professional.

## Planned architecture

- **Frontend:** React + Vite + Tailwind CSS
- **Backend:** FastAPI
- **AI:** open-weight vision-language model with local inference
- **Grounding:** manufacturer manuals / official documentation
- **Retrieval:** small local document store for the prototype

## Status

Early prototype — built during the Hacktoberfest Weekend 2026 Build for a Friend challenge.

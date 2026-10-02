# TinkerSight Product Spec

## Problem

Everyday devices are becoming more capable, but their controls and manuals are still written for people who already understand the device. This creates a practical barrier for non-technical users, children helping at home, and older adults.

## Product promise

TinkerSight converts **what the user sees + what the user wants + what the official manual says** into the simplest safe next action.

## Interaction principles

- Prefer visual references over technical names.
- Give one action at a time.
- Keep responses short.
- Use ordinary language.
- Never invent an instruction when the manual or image does not support it.
- Clearly separate visible facts from inference.
- Ask a targeted question when important information is missing.
- Confirm completion before moving to the next step.

## Example

User: "I want a 60 degree wash."

TinkerSight:

> Press the temperature button 3 times.

Then:

> Did the display show 60°C?

## Safety policy

Safe operation guidance is the primary MVP use case. Troubleshooting should remain limited to low-risk checks. If the task involves exposed wiring, mains electricity, gas, internal appliance repair, overheating, burning smell, sparks, leaks with electrical risk, or another hazardous condition, stop the workflow and recommend the official safety procedure or a qualified professional.

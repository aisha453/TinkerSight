# TinkerSight Product Spec

## Problem

Everyday devices are becoming more capable, but their controls and manuals are still written for people who already understand the device. This creates a practical barrier for people who just need to complete one task without decoding technical documentation.

## Product promise

TinkerSight converts **what the user sees + what the user wants + what verified documentation says** into the simplest safe next action.

## Interaction principles

- Prefer visual references over technical names.
- Give one action at a time.
- Keep responses short.
- Use ordinary language.
- Never invent an instruction when the image or retrieved source does not support it.
- Clearly distinguish visible facts, inferred information, and unknown information.
- Ask a targeted question when an important detail is missing.
- If the image is unclear, ask for a more useful photo rather than guessing.
- Do not claim the exact model manual was checked unless that match has actually been verified.

## Grounding

The prototype uses a small, explicit catalog of official manufacturer webpages. A source is retrieved only when the detected brand/goal matches a supported catalog entry.

A retrieved source is **not automatically treated as the exact manual for the photographed device**. The UI tells the user when the exact model has not been verified.

## Safety policy

Safe operation guidance is the primary use case. Troubleshooting remains limited to low-risk checks. If the task involves exposed wiring, mains electricity, gas, internal appliance repair, overheating, burning smell, sparks, leaks with electrical risk, or another hazardous condition, stop the workflow and recommend the official safety procedure or a qualified professional.

## Current scope

The prototype supports everyday appliances, personal devices, networking equipment, gaming equipment, printers, remotes, and visible control panels. Manufacturer grounding is currently strongest for selected air-conditioner documentation from Blue Star, LG, and Samsung.

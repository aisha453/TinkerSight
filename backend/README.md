# TinkerSight backend

FastAPI service for the TinkerSight prototype.

Planned responsibilities:

- accept an appliance image
- identify / classify the device
- retrieve relevant official documentation
- call the open-weight VLM
- return structured observations and the next safe action

The first implementation intentionally uses mock analysis so the frontend can be developed independently of the local model runtime.

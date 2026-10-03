# TinkerSight backend

FastAPI service for the TinkerSight prototype.

## Responsibilities

- accept a device or appliance image and the user's goal
- call the local open-weight vision-language model through Ollama
- identify visible device information without inventing an exact model
- retrieve selected official manufacturer documentation
- ground supported instructions in retrieved source text
- apply a deterministic safety gate before returning guidance
- return a structured next-step response to the React frontend

## Local model

The default model is `qwen3-vl:2b` running through Ollama at:

```
http://127.0.0.1:11434
```

Override the defaults with `OLLAMA_URL` and `OLLAMA_MODEL` environment variables if needed.

## Safety

The backend refuses hazardous intervention requests involving exposed electrical systems, gas, sparks, smoke, burning smells, internal repairs, and similar conditions. The prototype is designed for safe operation guidance, not repair instructions.

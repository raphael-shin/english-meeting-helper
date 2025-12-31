# API (apps/api)

FastAPI backend for streaming transcription, translation, suggestions, and summaries.

## Run
```bash
cd apps/api
uvicorn app.main:app --reload
```

## Tests
```bash
cd apps/api
pytest
```

## Environment
- Copy: `apps/api/.env.example` → `apps/api/.env`
- Key vars: `PROVIDER_MODE`, `AWS_REGION`, `AWS_PROFILE`, Bedrock/OpenAI model IDs

## Key Paths
- WebSocket: `/ws/v1/meetings/{sessionId}`
- REST API: `/api/v1`

## Structure (high level)
- `app/main.py`: FastAPI app + CORS
- `app/ws/meetings.py`: WebSocket session handler
- `app/services/`: STT, translation, suggestions, summary, correction
- `app/domain/models/`: Event and session models

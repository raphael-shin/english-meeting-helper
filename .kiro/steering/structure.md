---
inclusion: always
---

# Project Structure

## Monorepo Layout

| Path | Purpose |
|------|---------|
| `apps/api/` | FastAPI backend (Python 3.11+) |
| `apps/web/` | React frontend (TypeScript strict) |
| `packages/contracts/` | Shared JSON Schema → TS/Python types |
| `infra/cdk/` | AWS CDK infrastructure (Python) |
| `infra/docker/` | Dockerfiles for containerization |

## Backend Structure (`apps/api/app/`)

| Path | Responsibility |
|------|----------------|
| `main.py` | FastAPI entry, CORS, router registration |
| `core/` | Config (`config.py`), logging, dependency injection |
| `api/` | REST routes (`/api/v1`) - validate input, delegate to services |
| `ws/` | WebSocket routes (`/ws/v1`) - real-time audio/event handlers |
| `services/` | Business logic - pure Python, HTTP-independent |
| `services/stt/` | STT adapters: `aws.py` (Transcribe), `openai.py` (Whisper) |
| `services/translation/` | Translation adapters: `aws.py` (Bedrock), `openai.py` |
| `domain/models/` | Pydantic v2 models, internal data structures |

## Frontend Structure (`apps/web/src/`)

| Path | Responsibility |
|------|----------------|
| `main.tsx` | React entry point |
| `App.tsx` | Root component with tab layout |
| `components/` | Reusable UI components (TailwindCSS) |
| `hooks/` | Custom hooks: `useMeeting.ts`, `useTranslate.ts` |
| `lib/` | Utilities: `ws.ts`, `api.ts`, `audio.ts`, `debug.ts` |
| `types/` | TypeScript types (generated from contracts) |
| `features/` | Feature-specific components |

## Contracts (`packages/contracts/`)

| Path | Purpose |
|------|---------|
| `schema/` | JSON Schema definitions (source of truth) |
| `generated/ts/` | Auto-generated TypeScript types (DO NOT EDIT) |
| `generated/py/` | Auto-generated Python types (DO NOT EDIT) |
| `scripts/` | Type generation scripts |

## Code Placement Rules

**ALWAYS follow these conventions when adding code:**

| Task | Location | Notes |
|------|----------|-------|
| New REST endpoint | `apps/api/app/api/` | Thin controller, delegate to services |
| New WebSocket handler | `apps/api/app/ws/` | Handle connection lifecycle |
| New business logic | `apps/api/app/services/` | Pure Python, no HTTP dependencies |
| New external service adapter | `apps/api/app/services/<category>/` | Follow adapter pattern |
| New Pydantic model | `apps/api/app/domain/models/` | Use Pydantic v2 syntax |
| New React component | `apps/web/src/components/` | Functional component + hooks |
| New React hook | `apps/web/src/hooks/` | Prefix with `use` |
| New utility function | `apps/web/src/lib/` | Keep pure, testable |
| New shared type | `packages/contracts/schema/` | Run `npm run contracts:generate` after |

## Architectural Patterns

### Backend Patterns (MUST follow)
- **Adapter Pattern**: External services abstracted in `services/stt/` and `services/translation/`
- **State Machine**: `MeetingSession` in `domain/models/session.py` manages all transcript state
- **Display Buffer**: Manages Live tab display (max 4 confirmed + 1 composing segment)
- **Event-Driven**: All real-time updates via WebSocket events
- **Async Queue**: Background LLM correction when `LLM_CORRECTION_ENABLED=true`

### Frontend Patterns (MUST follow)
- **Single Hook Pattern**: `useMeeting` encapsulates WebSocket + meeting state
- **Reverse Display**: Confirmed transcripts shown newest-first
- **Progressive Updates**: Maintain same `segmentId` during partial streaming
- **Scroll Handling**: Composing area uses `max-h-32` with overflow scroll

### Data Flow
```
Audio → STT Service → MeetingSession → Display Buffer → WebSocket Events → Frontend
                           ↓
                     Transcript Storage → Translation Service → (Optional) Correction Queue
```

## Testing Conventions

| Test Type | Location | Command |
|-----------|----------|---------|
| Backend unit/integration | `apps/api/tests/` | `npm run test:api` |
| Frontend unit/component | `apps/web/src/**/*.test.tsx` | `npm run test:web` |
| CDK infrastructure | `infra/cdk/tests/` | `npm run test:cdk` |

**Testing rules:**
- Backend: Use `pytest-mock` for external service mocking
- Frontend: Use React Testing Library, co-locate tests with components
- Mock all external services (AWS, OpenAI) in tests

## Import Conventions

**Backend (Python):**
```python
# Absolute imports from app root
from app.services.translation.aws import BedrockTranslationService
from app.domain.models.session import MeetingSession
from app.core.config import settings
```

**Frontend (TypeScript):**
```typescript
// Relative imports within same feature
import { SubtitleItem } from './SubtitleItem';
// Absolute-style for cross-feature
import { useMeeting } from '../hooks/useMeeting';
```

## Key Files Reference

| Purpose | File |
|---------|------|
| Backend config | `apps/api/app/core/config.py` |
| Meeting state machine | `apps/api/app/domain/models/session.py` |
| WebSocket meeting handler | `apps/api/app/ws/meetings.py` |
| Main meeting hook | `apps/web/src/hooks/useMeeting.ts` |
| WebSocket client | `apps/web/src/lib/ws.ts` |
| Audio capture | `apps/web/src/lib/audio.ts` |

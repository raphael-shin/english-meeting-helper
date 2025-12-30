# Project Structure

## Monorepo Layout
```
apps/
  api/                    # FastAPI backend
  web/                    # React frontend
packages/
  contracts/              # Shared JSON Schema → TS/Python types
infra/
  cdk/                    # AWS CDK infrastructure
  docker/                 # Dockerfiles
```

## Backend (`apps/api/app/`)
```
main.py                   # FastAPI app entry, CORS, routers
core/                     # Settings, logging, dependencies
api/                      # REST routes (/api/v1)
  health.py               # Health check endpoint
  translate.py            # Quick translate endpoint
ws/                       # WebSocket routes (/ws/v1)
  meetings.py             # Real-time meeting session handler
services/
  stt/                    # Speech-to-text adapters (AWS, OpenAI)
  translation/            # Translation adapters (AWS Bedrock, OpenAI)
  suggestion.py           # AI suggestion service
  correction.py           # LLM correction queue (optional)
domain/models/            # Pydantic models
  events.py               # WebSocket event types
  session.py              # MeetingSession state machine
  subtitle.py             # SubtitleSegment, DisplayBuffer
  translate.py            # Translation models
```

## Frontend (`apps/web/src/`)
```
main.tsx                  # React entry point
App.tsx                   # Root component with layout
components/               # Shared UI components
  MeetingPanel.tsx        # Live/History transcript display
  SubtitleItem.tsx        # Individual subtitle with scroll support
  QuickTranslate.tsx      # Korean→English input
  SuggestionsPanel.tsx    # AI suggestions display
  TopBar.tsx              # Controls, status, settings
hooks/                    # Custom React hooks
  useMeeting.ts           # WebSocket + meeting state
  useTranslate.ts         # Translation API hook
lib/                      # Utilities
  ws.ts                   # WebSocket client
  api.ts                  # REST client
  audio.ts                # Mic capture, resampling
  debug.ts                # Debug logging utilities
types/                    # TypeScript types (from contracts)
  events.ts               # WebSocket event types
  provider.ts             # Provider mode types
```

## Contracts (`packages/contracts/`)
```
schema/                   # JSON Schema definitions
generated/
  ts/                     # Generated TypeScript types
  py/                     # Generated Python types
scripts/                  # Generation scripts
```

## Key Architectural Patterns

### Backend
- **Adapter Pattern**: External services (STT, translation) abstracted behind interfaces
- **State Machine**: `MeetingSession` manages transcript/translation state
- **Display Buffer**: Separate from transcript storage, manages Live tab display
- **Event-Driven**: WebSocket events for all real-time updates
- **Async Queue**: Optional LLM correction with background processing

### Frontend
- **Single Hook**: `useMeeting` encapsulates all WebSocket and state logic
- **Reverse Display**: Confirmed transcripts shown newest-first
- **Progressive Updates**: Same segmentId maintained during partial streaming
- **Scroll Handling**: Composing area scrolls for long text (max-h-32)

### Data Flow
```
Audio → STT Service → MeetingSession → Display Buffer → WebSocket Events → Frontend
                          ↓
                    Transcript Storage
                          ↓
                    Translation Service
                          ↓
                    (Optional) Correction Queue
```

## Testing Structure
- **Backend**: 60 tests covering session logic, display buffer, correction queue
- **Frontend**: 15 tests covering hooks, components, event handling
- **Integration**: WebSocket flow tests with mock services

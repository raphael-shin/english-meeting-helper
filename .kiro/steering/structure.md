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
domain/models/            # Pydantic models (events, session, translate)
```

## Frontend (`apps/web/src/`)
```
main.tsx                  # React entry point
App.tsx                   # Root component with layout
app/                      # Page-level components
components/               # Shared UI components
  MeetingPanel.tsx        # Live/History transcript display
  QuickTranslate.tsx      # Korean→English input
  SuggestionsPanel.tsx    # AI suggestions display
  TopBar.tsx              # Controls, status, settings
features/                 # Feature-specific modules
  meeting/                # Meeting transcript feature
  translate/              # Quick translate feature
  suggestions/            # AI suggestions feature
hooks/                    # Custom React hooks
  useMeeting.ts           # WebSocket + meeting state
  useTranslate.ts         # Translation API hook
lib/                      # Utilities
  ws.ts                   # WebSocket client
  api.ts                  # REST client
  audio.ts                # Mic capture, resampling
types/                    # TypeScript types (from contracts)
```

## Contracts (`packages/contracts/`)
```
schema/                   # JSON Schema definitions
generated/
  ts/                     # Generated TypeScript types
  py/                     # Generated Python types
scripts/                  # Generation scripts
```

## Key Patterns
- Adapter pattern for external services (STT, translation)
- WebSocket for real-time audio streaming and events
- JSON Schema as single source of truth for shared types
- Feature-based frontend organization

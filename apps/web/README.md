# Web (apps/web)

React frontend for live transcription, history, AI suggestions, and quick translate.

## Run
```bash
cd apps/web
npm install
npm run dev
```

## Tests
```bash
cd apps/web
npm run test
```

## Environment
- Copy: `apps/web/.env.example` → `apps/web/.env` (optional)
- Key vars: `VITE_API_BASE_URL`, `VITE_WS_BASE_URL`

## Structure (high level)
- `src/App.tsx`: Layout + panels
- `src/components/MeetingPanel.tsx`: Live + History transcript UI
- `src/components/SuggestionsPanel.tsx`: AI suggestions
- `src/components/QuickTranslate.tsx`: KO→EN input
- `src/hooks/useMeeting.ts`: WebSocket state + audio control

---
inclusion: always
---

# English Meeting Helper - Product Context

Real-time AI assistant for Korean speakers in English meetings. Provides live transcription, translation (EN→KO, KO→EN), and AI suggestions.

## Target Users
Korean speakers needing real-time language assistance during English meetings.

## Core Features

| Feature | Description | Latency Target |
|---------|-------------|----------------|
| Live STT | English speech-to-text (AWS Transcribe / OpenAI Whisper) | <2s |
| Translation | EN→KO real-time translation (Bedrock Nova/Claude) | <3s |
| Quick Translate | KO→EN text input for composing responses | Instant |
| AI Suggestions | Context-aware response suggestions | On-demand |
| LLM Correction | Optional typo/spacing fix with re-translation | Background |

## UI Structure

- **Live Tab**: Active transcription view
  - Composing Area: Current partial transcript (streaming)
  - Confirmed Area: Up to 4 recent finalized transcripts (newest first, FIFO)
- **History Tab**: Complete transcript archive with translations
- **Quick Translate Panel**: Korean→English input (bottom)
- **Suggestions Panel**: AI suggestions with customizable prompts
- **Top Bar**: Mic settings, provider toggle (AWS/OpenAI), controls

## Design Constraints (Must Follow)

1. **No Chunking**: Keep final transcripts as single segments—never split
2. **Progressive Streaming**: Maintain same `segmentId` during partial updates
3. **Display Buffer Limit**: Max 4 confirmed + 1 composing in Live tab
4. **Scroll Overflow**: Composing area scrolls when text exceeds `max-h-32` (128px)
5. **Single Speaker Mode**: No speaker diarization—simplified UX
6. **Newest First**: Confirmed transcripts display in reverse chronological order

## Provider Support

| Provider | STT | Translation | Status |
|----------|-----|-------------|--------|
| AWS | Transcribe Streaming | Bedrock (Claude/Nova) | ✅ Implemented |
| OpenAI | Whisper | GPT-4o-mini | ✅ Implemented |
| Google | - | - | ❌ Not implemented |

## LLM Correction (Optional Feature)

When `LLM_CORRECTION_ENABLED=true`:
- Batch size: 5 segments
- Interval: 5 seconds
- Triggers re-translation after correction

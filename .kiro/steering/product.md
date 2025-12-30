# English Meeting Helper - Product Overview

## What It Does
Real-time AI assistant for English meetings. Helps non-native speakers participate effectively through live transcription, translation, and AI-powered suggestions.

## Core Features

### Live Transcription & Display
- **Real-time STT**: English speech-to-text with <2s latency (AWS Transcribe / OpenAI Whisper)
- **Live Tab**: 
  - **Composing Area**: Shows current partial transcript (progressive streaming)
  - **Confirmed Area**: Shows up to 4 most recent finalized transcripts (FIFO)
  - Newest transcripts appear at top
  - Partial Result Stabilization (high) for faster finalization
- **History Tab**: Complete transcript archive with translations

### Translation
- **Real-time Translation**: English → Korean with <3s latency (AWS Bedrock Nova/Claude)
- **Quick Translate**: Instant Korean → English text translation for composing responses
- Context-aware translation using recent conversation history

### AI Suggestions
- Context-aware question/response suggestions based on meeting content
- Customizable prompts via Settings in Suggestions panel
- Powered by AWS Bedrock (Claude/Nova models)

### LLM Correction (Optional)
- Automatic typo and spacing correction for finalized transcripts
- Batch processing (5 segments per batch, 5s interval)
- Re-translation after correction
- Configurable via `LLM_CORRECTION_ENABLED` environment variable

## User Interface
- **Live Tab**: Composing (current) + Confirmed (recent 4) transcripts
- **History Tab**: Complete transcript archive with translations
- **Quick Translate**: Bottom panel for Korean → English input
- **Suggestions Panel**: AI-powered suggestions with customizable prompts
- **Top Bar**: Mic settings, provider selection (AWS/OpenAI), transcription controls

## Target Users
Korean speakers participating in English meetings who need real-time language assistance.

## Key Design Decisions
- **No Chunking**: Final transcripts kept as single segments for clarity
- **Progressive Display**: Composing area shows streaming partial updates
- **Scroll for Long Text**: Composing area scrolls if text exceeds 128px height
- **Single Speaker Mode**: Simplified UX without speaker diarization
- **Confirmed FIFO**: Only 4 most recent confirmed transcripts in Live tab

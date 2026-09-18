# System Architecture: Bilingual AI Calling Platform MVP

This document outlines the architectural blueprint for the Bilingual (Bangla `bn-BD` & English `en-US` / Banglish) AI Calling Platform MVP connecting to Asterisk/FreePBX via PJSIP Extension `7000`.

---

## 1. High-Level Topology

```text
               +-------------------------------------------------------+
               |                  Next.js Dashboard                    |
               |       (Active Calls, Live Transcript, Controls)       |
               +---------------------------+---------------------------+
                                           ^
                                     REST / WebSocket
                                           v
               +-------------------------------------------------------+
               |                   FastAPI API Gateway                 |
               |          (Routing, Security, Event Dispatcher)        |
               +---------------------------+---------------------------+
                                           ^
                             Redis Pub/Sub / Event Bus
                                           v
+-----------------------------------------------------------------------------------+
|                                  Voice Runtime                                    |
|                                                                                   |
| Caller Audio ---> RTP ---> VAD ---> Streaming STT ---> Language Detector          |
|                                                                |                  |
|                                                                v                  |
| Caller <--------- RTP <--- Streaming TTS <--- Streaming LLM <-- AI Receptionist  |
|                                                                                   |
|                               [Barge-In Detector]                                 |
+-----------------------------------------------------------------------------------+
                                           ^
                                           | ARI / RTP Stream
                                           v
+-----------------------------------------------------------------------------------+
|                               Asterisk / FreePBX                                  |
|                            (PJSIP Extension 7000)                                 |
+-----------------------------------------------------------------------------------+
                                           ^
                                           | SIP Trunk
                                           v
                                    PSTN / Mobile
```

> **Key Rule**: The browser is **never** part of the telephone audio path. Audio flows exclusively between Caller ↔ Asterisk ↔ Voice Runtime ↔ AI Voice Engine. The browser only exchanges metadata, state events, and transcripts via WebSocket.

---

## 2. Core Subsystems

### 2.1 Telephony Layer (`packages/telephony`)
- **Abstract Interface**: `TelephonyProvider` defines operations for call initialization, answer, hangup, hold, resume, DTMF, and status inquiries.
- **Implementations**:
  - `MockTelephonyProvider`: Simulates phone calls, ring timings, user speech triggers, and state transitions without PBX hardware.
  - `AsteriskTelephonyProvider`: Integrates with Asterisk ARI (Asterisk REST Interface) and PJSIP for real SIP extensions (`7000`) and trunks.

### 2.2 Voice & Media Runtime (`services/voice-runtime`, `packages/stt`, `packages/tts`)
- **Voice Activity Detection (VAD)**: Detects start and end of caller speech.
- **Speech-to-Text (STT)**: Streams caller audio to transcripts with language confidence.
- **Language Detection**: Automatically classifies caller input as `bn-BD`, `en-US`, or Banglish (`mixed`).
- **Text-to-Speech (TTS)**: Synthesizes conversational responses in the caller's language.
- **Barge-In / Interruption Engine**: When caller speech is detected while the AI is currently speaking, TTS streaming is instantly interrupted, the active audio buffer is flushed, and the agent enters `LISTENING` mode to process the caller's intervention.

### 2.3 AI Agent Core (`packages/agent-core`)
- **AI Receptionist (`AIReceptionistAgent`)**: Polite, conversational agent designed specifically for telephone dialogues (1-3 sentences per response, strictly no Markdown, no robotic monologues, no hallucinated customer details).
- **Call State Machine**: Enforces strict transitions:
  `IDLE` → `DIALING` → `RINGING` → `CONNECTED` → `LISTENING` → `THINKING` → `SPEAKING` → `ENDED` / `ERROR`.

### 2.4 API & Real-Time Event Gateway (`apps/api`)
- **FastAPI**: REST endpoints for health, calls, agents, and simulation.
- **Event Bus**: Redis Pub/Sub backend with transparent in-process `asyncio.Queue` fallback for development mode (`DEV_MODE=true`).
- **WebSocket Gateway**:
  - `/ws/dashboard`: Global live updates for call counts, agent statuses, and alerts.
  - `/ws/calls/{call_id}`: Dedicated per-call streaming channel for transcripts and state changes.

### 2.5 Real-Time Contact Center Dashboard (`apps/dashboard`)
- Built with **Next.js**, **TypeScript**, and **Tailwind CSS**.
- Real-time updates without page reloads.
- Call detail drawer/page with live transcript, latency metrics (STT, LLM, TTS), and call termination controls.

---

## 3. Database Schema

The database is built on PostgreSQL (or SQLite in lightweight local dev mode) with the following relational models:

### `calls`
- `id` (UUID / String, Primary Key)
- `phone_number` (String, Caller ID / Destination)
- `direction` (Enum: `INBOUND`, `OUTBOUND`)
- `language` (String: `bn-BD`, `en-US`, `mixed`)
- `status` (Enum: `RINGING`, `CONNECTED`, `LISTENING`, `THINKING`, `SPEAKING`, `ENDED`, `ERROR`)
- `started_at` (DateTime)
- `answered_at` (DateTime, Nullable)
- `ended_at` (DateTime, Nullable)
- `duration` (Integer, seconds)

### `transcript_messages`
- `id` (UUID / String, Primary Key)
- `call_id` (ForeignKey → `calls.id`)
- `speaker` (Enum: `customer`, `ai`, `system`)
- `text` (Text)
- `language` (String)
- `latency_ms` (Integer, Nullable)
- `timestamp` (DateTime)

### `agents`
- `id` (String, Primary Key, e.g. `ai-receptionist-01`)
- `name` (String, "AI Receptionist")
- `status` (Enum: `ONLINE`, `BUSY`, `OFFLINE`)
- `current_call_id` (ForeignKey → `calls.id`, Nullable)
- `stt_latency_ms` (Integer)
- `llm_latency_ms` (Integer)
- `tts_latency_ms` (Integer)

---

## 4. Call State Transition Matrix

```text
[IDLE]
  |
  +--(make_call)-----> [DIALING] ---> [RINGING]
  |                                      |
  +--(incoming)------------------------->+
                                         | (answer_call)
                                         v
                                   [CONNECTED]
                                         |
                                         v
                         +--------> [LISTENING]
                         |               | (caller pauses / VAD end)
                         |               v
                         |          [THINKING]
                         |               | (LLM generates first token)
                         |               v
                         |          [SPEAKING]
                         |          /        \
       (caller barge-in / speech)  /          \ (TTS complete)
                         +--------+            +--------> [LISTENING]
                                                       |
                                               (call terminated)
                                                       v
                                                    [ENDED]
```

---

## 5. Security & Extensibility

- **Secrets Isolation**: No PBX passwords, SIP credentials, or AI API keys are exposed to the client or checked into version control.
- **LLM Boundary**: The LLM generates text for the conversation. It has zero access to host shell commands.
- **Agentic ASI OS Compatibility**: The `Agent` and `TelephonyProvider` abstractions ensure voice calling can be packaged as a modular Agent Template in future autonomous AI agent systems.

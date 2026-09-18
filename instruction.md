# Antigravity Development Instruction

## Build a Production-Ready Bilingual AI Calling MVP

You are the **lead software architect, senior full-stack engineer, AI voice engineer, and SIP/PBX engineer**.

Your task is to build a **small but actually working MVP** of a bilingual AI phone-calling platform.

Do not build the full enterprise platform yet.

The primary goal is:

```text
Phone Call
    ↓
SIP Trunk
    ↓
Asterisk / FreePBX
    ↓
AI Extension 7000
    ↓
Voice Runtime
    ↓
STT
    ↓
AI Agent / LLM
    ↓
TTS
    ↓
Asterisk
    ↓
Phone Caller
```

At the same time:

```text
Asterisk / Voice Runtime
        ↓
     FastAPI
        ↓
     WebSocket
        ↓
   Next.js Dashboard
```

The dashboard must show the active call, AI state, language, duration, and live transcript.

---

# 1. IMPORTANT DEVELOPMENT RULE

Build the system incrementally.

Do NOT attempt to implement the entire platform in one step.

Always:

1. Inspect the repository.
2. Understand the existing code before modifying it.
3. Create/update architecture documentation.
4. Implement one small working feature.
5. Run tests.
6. Start the application.
7. Verify it in a browser.
8. Fix errors.
9. Only then continue.

Never claim a feature works unless it has actually been tested.

If an external service is unavailable, implement a clean adapter and mock provider so development can continue.

---

# 2. MVP SCOPE

The MVP contains exactly:

### Telephony

* Asterisk / FreePBX
* PJSIP
* One AI extension: `7000`
* Incoming calls
* Outgoing calls
* Answer
* Hangup

### AI Agent

One agent:

```text
AI Receptionist
```

Capabilities:

* Bangla
* English
* Banglish where possible
* Automatic language detection
* Conversation context
* STT
* LLM
* TTS
* Voice activity detection
* Caller interruption / barge-in

### Dashboard

Only:

* Dashboard
* Live Calls
* Agents
* Call History

Do not build additional enterprise features yet.

---

# 3. CONCRETE DEPLOYMENT TARGET

Design the MVP for:

```text
1 Ubuntu 24.04 VPS
1 existing Asterisk/FreePBX server
1 AI voice agent
1 concurrent call initially
1 test phone
1 web dashboard
1 PostgreSQL database
1 Redis instance
```

Recommended VPS baseline:

```text
CPU: 4 vCPU
RAM: 8 GB
SSD: 80 GB+
OS: Ubuntu 24.04 LTS
```

AI inference may be cloud-hosted.

The architecture must also allow later replacement with local/self-hosted models.

---

# 4. NETWORK TOPOLOGY

Preferred production topology:

```text
                 INTERNET
                    |
                 HTTPS
                    |
                NGINX
                    |
          +---------+---------+
          |                   |
     Next.js Dashboard     FastAPI
                              |
                         Redis/Postgres
                              |
                         Voice Runtime
                              |
                         Secure Network
                              |
                       Asterisk / FreePBX
                              |
                         SIP Trunk
                              |
                         PSTN / Mobile
```

IMPORTANT:

**The browser must never be part of the telephone audio path.**

Audio must flow between:

```text
Caller ↔ Asterisk ↔ Voice Runtime ↔ AI Voice Provider
```

The dashboard only receives metadata/events/transcripts.

---

# 5. TECHNOLOGY STACK

Use:

## Frontend

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic

## Database

* PostgreSQL

## Real-Time

* Redis
* WebSocket

## Telephony

* Asterisk / FreePBX
* PJSIP
* ARI where appropriate
* RTP/media streaming

## AI

Use provider abstractions:

```text
STTProvider
LLMProvider
TTSProvider
```

Do not tightly couple the application to one AI vendor.

Support configuration through environment variables.

---

# 6. REPOSITORY STRUCTURE

Create a clean structure similar to:

```text
ai-calling-platform/
│
├── apps/
│   ├── dashboard/
│   └── api/
│
├── services/
│   └── voice-runtime/
│
├── packages/
│   ├── agent-core/
│   ├── telephony/
│   ├── stt/
│   ├── llm/
│   └── tts/
│
├── database/
│   └── migrations/
│
├── infra/
│   ├── nginx/
│   └── asterisk/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── TELEPHONY.md
│   ├── DEVELOPMENT.md
│   └── DEPLOYMENT.md
│
├── docker-compose.yml
├── .env.example
└── README.md
```

Keep the architecture modular.

Do not create unnecessary microservices.

---

# 7. DEVELOPMENT MODE FIRST

The entire application must run without:

* Asterisk
* SIP trunk
* real STT
* real LLM
* real TTS

Create:

```text
MockTelephonyProvider
MockSTTProvider
MockLLMProvider
MockTTSProvider
```

Add:

```env
DEV_MODE=true
```

In development mode, create simulated calls.

Example:

```text
Call #1001

Caller:
Demo Caller

Language:
bn-BD

Status:
SPEAKING
```

Simulate:

```text
CONNECTED
    ↓
LISTENING
    ↓
THINKING
    ↓
SPEAKING
    ↓
LISTENING
    ↓
ENDED
```

The dashboard must display these changes in real time.

---

# 8. TELEPHONY ABSTRACTION

Create a generic interface:

```python
class TelephonyProvider:

    async def make_call(self, destination: str):
        ...

    async def answer_call(self, call_id: str):
        ...

    async def hangup_call(self, call_id: str):
        ...

    async def get_call_status(self, call_id: str):
        ...

    async def get_active_calls(self):
        ...
```

Implement:

```text
MockTelephonyProvider
AsteriskTelephonyProvider
```

The AI Agent must never directly depend on Asterisk-specific code.

---

# 9. ASTERISK INTEGRATION

The real MVP should use:

```text
Asterisk
PJSIP
ARI
RTP/media
```

Create documentation for configuring:

```text
AI Extension:
7000

Username:
ai-agent
```

The exact credentials must come from environment variables.

Example:

```env
PBX_HOST=
PBX_PORT=8088
PBX_ARI_USERNAME=
PBX_ARI_PASSWORD=

SIP_EXTENSION=7000
SIP_USERNAME=
SIP_PASSWORD=
SIP_DOMAIN=
```

Do not expose credentials in frontend code.

Do not hard-code PBX addresses.

---

# 10. VOICE PIPELINE

Implement:

```text
Caller Audio
      ↓
RTP / Media Stream
      ↓
Voice Activity Detection
      ↓
Streaming STT
      ↓
Language Detection
      ↓
AI Receptionist
      ↓
Streaming LLM
      ↓
Streaming TTS
      ↓
RTP
      ↓
Caller
```

Use streaming wherever the selected provider supports it.

Design the interfaces so the provider can later be replaced.

---

# 11. BILINGUAL VOICE

Primary languages:

```text
Bangla:  bn-BD
English: en-US
```

Also handle mixed speech where possible:

```text
"ভাই আমার orderটা কবে deliver হবে?"
```

The agent should automatically detect the caller's language.

Call session should contain:

```text
detected_language
preferred_language
language_confidence
```

Behavior:

* Bangla caller → respond in Bangla
* English caller → respond in English
* Mixed caller → naturally handle mixed language
* Caller changes language → agent follows the caller

---

# 12. AI RECEPTIONIST

Create exactly one initial agent:

```text
AI Receptionist
```

Example behavior:

```text
Start politely.

If caller speaks Bangla:
respond in Bangla.

If caller speaks English:
respond in English.

Keep telephone responses short.

Do not invent customer information.

Ask clarification when necessary.

If the system cannot answer something,
respond honestly rather than hallucinating.
```

Typical response length:

```text
1–3 sentences
```

Avoid:

* Markdown
* long explanations
* URLs
* unnecessary lists
* robotic responses

---

# 13. AGENT ARCHITECTURE

Create a generic Agent interface:

```python
class Agent:

    async def start_call(...):
        ...

    async def receive_audio(...):
        ...

    async def process_speech(...):
        ...

    async def generate_response(...):
        ...

    async def speak(...):
        ...

    async def end_call(...):
        ...
```

The initial implementation:

```text
AIReceptionistAgent
```

Keep the interface generic so future agents can be added without rewriting the voice runtime.

---

# 14. CALL STATE MACHINE

Use these states:

```text
IDLE
DIALING
RINGING
CONNECTED
LISTENING
THINKING
SPEAKING
ENDED
ERROR
```

State transitions must be validated.

Example:

```text
RINGING
  ↓
CONNECTED
  ↓
LISTENING
  ↓
THINKING
  ↓
SPEAKING
  ↓
LISTENING
```

Invalid transitions should produce structured errors.

---

# 15. BARGE-IN

Implement caller interruption.

Required behavior:

```text
AI is speaking
      ↓
Caller starts speaking
      ↓
VAD detects caller speech
      ↓
Stop current TTS
      ↓
Capture caller speech
      ↓
STT
      ↓
LLM
      ↓
TTS
```

Do not wait until the AI finishes speaking before processing an interruption.

This is important for natural phone conversations.

---

# 16. DASHBOARD

Build a professional AI contact-center dashboard.

Do not over-design it.

Use:

* Sidebar
* Status cards
* Tables
* Real-time status indicators
* Live transcript
* Agent cards
* Responsive layout
* Dark/light mode

---

# 17. DASHBOARD PAGE

Show:

```text
Active Calls
Today's Calls
AI Agent Status
System Status
```

Example:

```text
ACTIVE CALLS       1
CALLS TODAY       28
AI RECEPTIONIST   ONLINE
SYSTEM            HEALTHY
```

---

# 18. LIVE CALLS

Display:

```text
Call ID
Phone Number
Direction
Language
Agent
Status
Duration
```

Example:

```text
#1001
+8801XXXXXXXXX
INBOUND
bn-BD
AI Receptionist
LISTENING
02:31
```

Clicking the call opens the live call detail.

---

# 19. LIVE CALL DETAIL

Display:

```text
Call ID
Phone Number
Direction
Language
Agent
Status
Duration
```

Then show live transcript:

```text
CUSTOMER

আপনাদের অফিস কখন খোলা?


AI

আমাদের অফিস সকাল ৯টা থেকে সন্ধ্যা ৬টা পর্যন্ত খোলা।
```

Add only:

```text
END CALL
```

Do not implement complicated operator controls in MVP.

---

# 20. AGENT PAGE

Display:

```text
AI Receptionist

Status: ONLINE

Current Call:
#1001

Language:
bn-BD

State:
LISTENING
```

Also show:

```text
STT latency
LLM latency
TTS latency
```

when available.

---

# 21. CALL HISTORY

Store and display:

```text
Call ID
Phone Number
Direction
Duration
Language
Status
Date/Time
```

Allow basic filtering.

No advanced analytics yet.

---

# 22. REAL-TIME EVENTS

Create an event model.

Examples:

```text
call.created
call.ringing
call.connected
call.ended

agent.listening
agent.thinking
agent.speaking

stt.completed
llm.completed
tts.completed

call.error
```

Flow:

```text
Service
   ↓
Redis
   ↓
FastAPI WebSocket
   ↓
Next.js
```

The dashboard must update without page refresh.

---

# 23. DATABASE

For MVP create only:

## calls

```text
id
phone_number
direction
language
status
started_at
answered_at
ended_at
duration
```

## transcript_messages

```text
id
call_id
speaker
text
language
timestamp
```

## agents

```text
id
name
status
current_call_id
```

Use UUIDs where appropriate.

Use Alembic migrations.

---

# 24. ENVIRONMENT

Create `.env.example`:

```env
APP_ENV=development
DEV_MODE=true

DATABASE_URL=
REDIS_URL=

PBX_HOST=
PBX_PORT=8088
PBX_ARI_USERNAME=
PBX_ARI_PASSWORD=

SIP_EXTENSION=7000
SIP_USERNAME=
SIP_PASSWORD=
SIP_DOMAIN=

LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=

STT_PROVIDER=
STT_API_KEY=
STT_MODEL=

TTS_PROVIDER=
TTS_API_KEY=
TTS_MODEL=

JWT_SECRET=
```

Never commit `.env`.

---

# 25. DOCKER

Create:

```text
docker-compose.yml
```

Initial services:

```text
dashboard
api
voice-runtime
postgres
redis
nginx
```

Asterisk may remain external.

The application must be able to connect to an existing Asterisk/FreePBX installation.

---

# 26. SECURITY

Implement basic production security:

* HTTPS-ready
* Environment-based secrets
* API authentication
* WebSocket authentication
* Input validation
* API rate limiting
* Structured audit logging for call controls
* No credentials in frontend
* No arbitrary shell execution by the LLM

The LLM must never be allowed to execute arbitrary operating-system commands.

---

# 27. LOGGING

Use structured logs.

Example:

```json
{
  "level": "INFO",
  "service": "voice-runtime",
  "event": "tts.completed",
  "call_id": "123",
  "latency_ms": 310
}
```

Every call should have a correlation ID.

Trace:

```text
Call
 ↓
STT
 ↓
Agent
 ↓
LLM
 ↓
TTS
 ↓
Asterisk
```

---

# 28. API

Implement minimum APIs:

```text
GET  /api/health

GET  /api/calls
GET  /api/calls/{id}

POST /api/calls
POST /api/calls/{id}/hangup

GET  /api/agents
GET  /api/agents/{id}

GET  /api/events
```

WebSocket:

```text
/ws/dashboard
/ws/calls/{call_id}
```

Document the API.

---

# 29. TESTING

Create automated tests for:

### Backend

* Health API
* Calls API
* Agents API
* Call state transitions
* Database operations

### WebSocket

* Connection
* Authentication
* Event delivery

### Agent

* Language selection
* Conversation state
* Response generation

### Providers

* Mock Telephony
* Mock STT
* Mock LLM
* Mock TTS

### Integration

Test:

```text
Mock Call
→ Agent
→ Transcript
→ State changes
→ Dashboard event
```

The test suite must run without external credentials.

---

# 30. DOCUMENTATION

Create:

```text
README.md
ARCHITECTURE.md
DEVELOPMENT.md
TELEPHONY.md
DEPLOYMENT.md
```

Document:

* Local installation
* Docker startup
* Environment configuration
* Mock mode
* Dashboard usage
* Asterisk configuration
* PJSIP extension 7000
* SIP trunk configuration
* AI provider configuration
* Incoming call testing
* Outgoing call testing
* Troubleshooting

Use Mermaid diagrams where useful.

---

# 31. IMPLEMENTATION PHASES

Follow this exact order.

## PHASE 1 — Foundation

Build:

```text
Repository
FastAPI
Next.js
PostgreSQL
Redis
Docker Compose
Environment configuration
Documentation
```

Acceptance:

```text
docker compose up
```

starts successfully.

---

## PHASE 2 — Dashboard

Build:

```text
Dashboard
Live Calls
Agents
Call History
```

Use mock data initially.

Acceptance:

Dashboard loads correctly in browser.

---

## PHASE 3 — Real-Time Mock Calls

Implement:

```text
MockTelephonyProvider
MockSTT
MockLLM
MockTTS
```

Create simulated calls.

Acceptance:

Dashboard shows:

```text
CONNECTED
→ LISTENING
→ THINKING
→ SPEAKING
→ LISTENING
→ ENDED
```

in real time.

---

## PHASE 4 — Agent Runtime

Implement:

```text
Agent interface
AIReceptionistAgent
Conversation state
Language detection
LLM provider abstraction
```

Acceptance:

Simulated Bangla and English conversations work.

---

## PHASE 5 — Voice Runtime

Implement:

```text
VAD
STT
TTS
Streaming
Barge-in
```

Acceptance:

The voice pipeline works independently of Asterisk.

---

## PHASE 6 — Asterisk

Implement:

```text
AsteriskTelephonyProvider
PJSIP
ARI
RTP/media integration
Extension 7000
```

Acceptance:

A real SIP call reaches the AI extension.

---

## PHASE 7 — REAL INBOUND CALL

Test:

```text
Mobile
 ↓
SIP Trunk
 ↓
Asterisk
 ↓
7000
 ↓
AI Receptionist
```

Acceptance:

Caller can have a real conversation with the AI.

---

## PHASE 8 — REAL OUTBOUND CALL

Test:

```text
Dashboard/API
 ↓
AI Agent
 ↓
Asterisk
 ↓
SIP Trunk
 ↓
Mobile
```

Acceptance:

AI can initiate a real outbound call.

---

## PHASE 9 — PRODUCTION HARDENING

Add:

* HTTPS
* authentication
* secure WebSocket
* health checks
* structured logging
* error handling
* restart policies
* backup documentation
* production environment configuration

---

# 32. EXPLICITLY OUT OF SCOPE

Do NOT implement these yet:

```text
Multi-tenant
Campaign management
Bulk dialing
CRM
ERP
MCP
RAG
Long-term memory
Multiple agents
Advanced RBAC
Call recording
Advanced analytics
Kubernetes
Complex microservices
WhatsApp
SMS
Email
Human transfer
```

Keep extension points for these features, but do not build them now.

---

# 33. FUTURE ARCHITECTURE

The MVP must remain compatible with a future Agentic AI / ASI OS.

Future architecture:

```text
ASI OS
   ↓
Agent Runtime
   ↓
Agent Template
   ↓
AI Calling Agent
   ↓
Voice Capability
   ↓
Telephony / SIP
```

The calling system should eventually be usable as an Agent Template.

Do not let MVP implementation choices make that future architecture impossible.

---

# 34. CODE QUALITY RULES

Follow these rules strictly:

* Prefer simple architecture.
* Avoid premature microservices.
* Use clear interfaces.
* Use dependency injection.
* Keep providers replaceable.
* Keep business logic separate from transport.
* Keep telephony separate from AI.
* Keep dashboard separate from audio.
* Never hard-code secrets.
* Never hard-code provider-specific logic into the Agent.
* Validate all external input.
* Use type hints.
* Use structured logging.
* Write tests for important logic.
* Avoid giant files.
* Avoid unnecessary abstractions.
* Document architectural decisions.

---

# 35. BROWSER VERIFICATION

Whenever the frontend is changed:

1. Start the development server.
2. Open the dashboard in a browser.
3. Verify the page loads.
4. Check browser console errors.
5. Verify key UI elements.
6. Test real-time updates.
7. Fix errors before continuing.

Do not rely only on compilation.

---

# 36. FINAL MVP ACCEPTANCE TEST

The MVP is complete only when this end-to-end scenario works:

```text
Mobile/PSTN
     ↓
SIP Trunk
     ↓
Asterisk
     ↓
PJSIP Extension 7000
     ↓
AI Receptionist
     ↓
STT
     ↓
Bangla / English Understanding
     ↓
LLM
     ↓
TTS
     ↓
Asterisk
     ↓
Caller
```

And simultaneously:

```text
Next.js Dashboard
       ↓
Active call appears
       ↓
Agent = AI Receptionist
       ↓
Language = bn-BD / en-US
       ↓
Status:
CONNECTED
LISTENING
THINKING
SPEAKING
       ↓
Live transcript updates
       ↓
Caller interrupts AI
       ↓
AI stops speaking
       ↓
AI processes caller
       ↓
AI responds
       ↓
Call ends
       ↓
Call appears in Call History
```

---

# 37. FIRST ACTION

Start by inspecting the existing repository.

Then:

1. Create `ARCHITECTURE.md`.
2. Create the project structure.
3. Create `.env.example`.
4. Create Docker Compose.
5. Build FastAPI foundation.
6. Build PostgreSQL models/migrations.
7. Build Redis event infrastructure.
8. Build the Next.js dashboard.
9. Implement MockTelephonyProvider.
10. Implement simulated calls.
11. Verify the dashboard in a browser.

Do not start with Asterisk.

**First produce a completely working mock end-to-end MVP, then progressively replace mock components with real telephony and AI services.**

At the end of every phase report:

```text
PHASE:
STATUS:

Implemented:
- ...

Files changed:
- ...

Tests:
- ...

Browser verification:
- ...

Remaining:
- ...

Problems:
- ...
```

Always keep the application runnable after each phase.

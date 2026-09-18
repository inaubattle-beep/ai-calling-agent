# Build: Bilingual AI Calling Agent + SIP/PBX + Real-Time Dashboard

You are the lead architect and senior full-stack/AI/telephony engineer.

Build a production-ready, modular **AI Calling Agent Platform** that connects to an existing **SIP/PBX server**, can receive and make phone calls, understand and speak **Bangla (bn-BD) and English (en-US)**, and provide a real-time web dashboard for monitoring and controlling calls and AI agents.

The architecture must be designed so that the Voice Calling Agent can later become a module of a larger **Agentic AI / ASI OS** platform.

---

# 1. Core Objective

Build a system with these capabilities:

1. Connect to Asterisk/FreePBX through SIP/PJSIP.
2. Receive incoming calls.
3. Make outbound calls.
4. Answer calls automatically using an AI agent.
5. Stream caller audio to Speech-to-Text.
6. Understand Bangla and English.
7. Understand mixed Bangla-English / Banglish where possible.
8. Generate an intelligent response using an LLM.
9. Convert AI responses to speech using TTS.
10. Stream speech back to the caller.
11. Support natural conversation.
12. Support caller interruption / barge-in.
13. Transfer calls to human extensions.
14. Put calls on hold.
15. End calls.
16. Maintain conversation context.
17. Store call metadata and transcripts.
18. Provide real-time call monitoring.
19. Provide real-time AI-agent monitoring.
20. Support outbound calling campaigns.
21. Provide analytics.
22. Provide authentication and role-based access.
23. Provide detailed system/event logs.
24. Be Docker-ready.
25. Be extensible through MCP, Skills, Tools, and Agent Templates.

---

# 2. High-Level Architecture

Use this architecture:

```
                WEB DASHBOARD
                Next.js
                     |
                REST/WebSocket
                     |
                FastAPI API
                     |
   +-----------------+------------------+
   |                 |                  |
```

Agent Runtime     Call Manager      Campaign Manager
|                 |                  |
|              Asterisk/PJSIP       |
|                 |                  |
+-------- Voice Runtime ------------+
|
STT -> LLM -> TTS
|
RTP
|
SIP / PBX
|
SIP Trunk
|
PSTN/Mobile

Do NOT make the LLM directly responsible for SIP protocol handling.

Separate:

* Telephony layer
* Media/voice layer
* Agent intelligence layer
* API/control layer
* Dashboard
* Persistence
* Infrastructure

---

# 3. Recommended Technology

Use:

Frontend:

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui
* Recharts or equivalent chart library
* WebSocket for real-time updates

Backend:

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic

Database:

* PostgreSQL
* pgvector for future memory/RAG

Real-time/event infrastructure:

* Redis
* Redis Pub/Sub or Streams

Telephony:

* Asterisk
* PJSIP
* Asterisk ARI
* RTP/media streaming

AI:

* Provider abstraction for LLM
* OpenAI-compatible API support
* OpenRouter support
* Local LLM support
* Ollama support

STT:

* Whisper-compatible abstraction
* Streaming STT architecture

TTS:

* Provider abstraction
* Support multilingual voices
* Bangla + English

Deployment:

* Docker
* Docker Compose
* Linux-first
* Environment variables
* Health checks

---

# 4. Repository Structure

Create a clean monorepo:

/ai-calling-platform

/apps
/dashboard
/api
/voice-runtime

/services
/agent-runtime
/call-manager
/campaign-manager
/event-service

/packages
/agent-core
/telephony
/voice
/llm
/stt
/tts
/memory
/mcp
/shared

/agents
/templates
/customer-support
/sales
/receptionist
/appointment
/custom

/database
/migrations
/seed

/infra
/docker
/asterisk
/nginx

/docs
ARCHITECTURE.md
API.md
TELEPHONY.md
AGENTS.md
DEPLOYMENT.md

docker-compose.yml
.env.example
README.md

Keep modules loosely coupled.

---

# 5. Telephony Layer

Implement an abstraction:

TelephonyProvider

with operations:

* register()
* make_call()
* answer_call()
* reject_call()
* hangup_call()
* hold_call()
* resume_call()
* transfer_call()
* send_dtmf()
* get_call_status()
* get_active_calls()
* get_extension_status()

Primary implementation:

AsteriskTelephonyProvider

Use PJSIP and ARI where appropriate.

Do not hard-code one PBX implementation into the agent runtime.

Future providers should be possible:

* Asterisk
* FreeSWITCH
* SIP server
* Cloud telephony provider

---

# 6. SIP Configuration

Provide configuration through environment variables.

Example:

PBX_HOST=
PBX_PORT=8088
PBX_ARI_USERNAME=
PBX_ARI_PASSWORD=

SIP_USERNAME=
SIP_PASSWORD=
SIP_DOMAIN=
SIP_EXTENSION=

Do not store credentials in source code.

Create:

.env.example

with safe placeholder values.

---

# 7. Voice Runtime

Create a real-time voice pipeline:

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
Agent Runtime
↓
Streaming LLM
↓
Streaming TTS
↓
RTP
↓
Caller

The pipeline must support low latency.

Do not wait for an entire conversation before processing.

Use streaming wherever possible.

---

# 8. Language Support

Primary languages:

* Bangla: bn-BD
* English: en-US

Support:

Bangla:
"ভাই, আমার অর্ডারটা কবে আসবে?"

English:
"When will my order arrive?"

Banglish:
"Bhai amar order ta kobe ashbe?"

Mixed language:

"আমার orderটা কবে deliver হবে?"

The agent should preserve the caller's language preference.

Add language state to the call session:

language:
detected
preferred
confidence

Allow:

AUTO
BANGLA
ENGLISH

---

# 9. Agent Runtime

Create a generic AgentRuntime.

Responsibilities:

* Load agent template
* Load system prompt
* Maintain conversation state
* Manage tools
* Call LLM
* Manage memory
* Decide actions
* Handle interruptions
* Handle escalation
* Produce structured events

The LLM must NOT directly execute arbitrary system commands.

All actions must go through registered tools.

---

# 10. Agent Tools

Create tools such as:

call.answer
call.hangup
call.transfer
call.hold
call.resume
call.send_dtmf

customer.lookup
customer.create
customer.update

order.lookup
order.create

ticket.create
ticket.lookup

appointment.create
appointment.cancel

agent.transfer_to_human

memory.search
memory.store

Every tool must have:

* name
* description
* input schema
* output schema
* permission
* timeout
* audit logging

---

# 11. Human Transfer

Support:

AI → Human

Example:

Caller:
"আমি একজন কর্মকর্তার সাথে কথা বলতে চাই।"

Agent decides:

transfer_to_human(extension="101")

The dashboard must show:

TRANSFERRING

then:

TRANSFERRED

If transfer fails:

TRANSFER_FAILED

and the AI should recover gracefully.

---

# 12. Barge-In / Interruption

Implement:

Caller speaks
↓
AI is speaking
↓
Caller interrupts
↓
Detect speech
↓
Stop TTS
↓
Process caller speech
↓
Continue conversation

This is required for natural phone conversations.

---

# 13. Agent Templates

Create an Agent Template system.

Example:

```yaml
id: customer-support-bd
name: Customer Support Bangladesh

languages:
  - bn-BD
  - en-US

voice:
  input:
    stt: whisper
  output:
    tts: provider

behavior:
  interruption: true
  barge_in: true
  max_call_duration: 1800

tools:
  - customer.lookup
  - order.lookup
  - ticket.create
  - call.transfer

memory:
  enabled: true
```

Templates must be data/config driven.

Do not hard-code every agent.

---

# 14. Dashboard

Build a professional real-time dashboard.

Main navigation:

Dashboard
Live Calls
Agents
Campaigns
Contacts
Call History
Transcripts
Recordings
Analytics
Tools
Agent Templates
System
Settings
Audit Logs

---

# 15. Main Dashboard

Display cards:

Active Calls
Queued Calls
Completed Calls
Failed Calls
AI Agents Online
AI Agents Busy
Calls Today
Average Call Duration

Example:

ACTIVE CALLS: 12
QUEUED: 37
COMPLETED: 428
AI AGENTS: 8/10

Use real-time updates.

---

# 16. Live Calls Page

Display:

Call ID
Phone Number
Direction
Agent
Language
Status
Duration
Start Time

Statuses:

OFFLINE
STARTING
IDLE
DIALING
RINGING
CONNECTED
LISTENING
THINKING
SPEAKING
TRANSFERRING
ON_HOLD
ENDING
ERROR

Clicking a call opens a detailed call view.

---

# 17. Live Call Detail

Show:

Caller number
Agent
Language
Duration
Call status
PBX extension
SIP information
Current AI state

Show live conversation transcript:

CUSTOMER
"ভাই, আপনাদের পণ্যটা কি available?"

AI
"জি, আমাদের পণ্যটি বর্তমানে available।"

Provide controls:

Mute
Hold
Resume
Transfer
End Call

Only authorized users can execute call controls.

---

# 18. Agent Dashboard

For every agent show:

Agent name
Template
Status
Current call
Language
Model
STT latency
LLM latency
TTS latency
Call duration
Errors

Example:

Sales Agent 01
● BUSY

Call: #1021
Language: bn-BD
Model: configured-model
STT: 180 ms
LLM: 620 ms
TTS: 310 ms

---

# 19. Agent Status

Implement:

OFFLINE
STARTING
IDLE
DIALING
RINGING
CONNECTED
LISTENING
THINKING
SPEAKING
TRANSFERRING
ON_HOLD
ERROR

Publish agent state changes through Redis/WebSocket.

---

# 20. Campaign System

Create outbound campaigns.

Campaign fields:

name
description
agent_template
contact_list
calling_schedule
max_concurrent_calls
retry_policy
language
prompt
enabled

Campaign statistics:

Total Contacts
Dialed
Answered
No Answer
Busy
Failed
Interested
Not Interested
Callback Required
Transferred

Implement safe rate/concurrency controls.

---

# 21. Contact Management

Contact fields:

name
phone
email
language
tags
notes
customer_id
consent/status fields where applicable

Add:

Import CSV
Export CSV
Search
Filter
Tags

Do not expose unnecessary personal data to unauthorized users.

---

# 22. Call History

Store:

call_id
direction
caller
destination
agent
campaign
start_time
answer_time
end_time
duration
status
language
transfer_status
recording_reference
transcript_reference

Allow filtering by:

date
agent
campaign
language
status
phone

---

# 23. Transcript

Store conversation turns:

timestamp
speaker
text
language
confidence
latency

Example:

```json
{
  "speaker": "customer",
  "text": "আমার অর্ডারটা কবে আসবে?",
  "language": "bn-BD"
}
```

---

# 24. Call Recording

Design recording support, but make it configurable.

Configuration:

RECORD_CALLS=true/false

Store only references/metadata in PostgreSQL.

Use object storage or filesystem abstraction for actual audio.

Implement retention configuration.

Do not make recordings publicly accessible.

---

# 25. Real-Time Event System

Create an event model.

Examples:

call.created
call.ringing
call.connected
call.ended

agent.started
agent.idle
agent.listening
agent.thinking
agent.speaking
agent.error

stt.started
stt.completed

llm.started
llm.completed

tts.started
tts.completed

tool.started
tool.completed
tool.failed

transfer.started
transfer.completed
transfer.failed

Publish events to Redis.

Dashboard consumes them through WebSocket.

---

# 26. Live Event Stream

Create a system event panel.

Example:

19:45:12 CALL 1021 connected
19:45:13 Agent Sales-01 listening
19:45:17 Customer speech detected
19:45:18 STT completed
19:45:19 LLM started
19:45:20 Tool customer.lookup()
19:45:21 LLM completed
19:45:21 TTS started
19:45:22 Agent speaking
19:45:25 Customer interrupted

---

# 27. Analytics

Create charts for:

Calls per day
Answered calls
Missed calls
Failed calls
Average duration
Calls by language
Calls by agent
Calls by campaign
Transfers
AI resolution
Human transfers

AI performance:

STT latency
LLM latency
TTS latency
Total response latency
Tool failures
Agent errors
Interruptions

---

# 28. System Monitoring

Show:

PBX status
SIP trunk status
AI runtime status
STT status
TTS status
LLM provider status
Redis status
PostgreSQL status
MCP status

Infrastructure:

CPU
RAM
GPU
VRAM
Network
Active RTP streams

Use health-check endpoints.

---

# 29. Authentication

Implement secure authentication.

Roles:

ADMIN
SUPERVISOR
OPERATOR
AGENT_MANAGER
ANALYST

Permissions should control:

view calls
control calls
view recordings
view transcripts
manage agents
manage campaigns
manage PBX
manage users
view system logs

---

# 30. Security

Follow these rules:

* Never expose SIP passwords in frontend.
* Never expose API keys.
* Never allow LLM arbitrary shell execution.
* Validate all tool parameters.
* Validate phone numbers.
* Rate-limit APIs.
* Authenticate WebSocket connections.
* Audit call-control actions.
* Audit tool calls.
* Protect recordings.
* Protect transcripts.
* Use HTTPS in production.
* Use secure secrets/environment configuration.
* Add request IDs and correlation IDs.

---

# 31. MCP Architecture

Prepare the platform for MCP.

Architecture:

Agent
↓
MCP Client
↓
MCP Servers
├── CRM
├── ERP
├── Database
├── Ticketing
├── Calendar
└── Custom Business Tools

The Agent Runtime should not depend directly on individual business applications.

---

# 32. Memory

Implement memory abstraction.

Short-term:
current conversation

Long-term:
customer history

Vector memory:
pgvector

Provide:

memory.search()
memory.store()

Memory must be scoped by:

tenant
customer
agent
conversation

---

# 33. Multi-Tenant Readiness

Design database and APIs so the system can eventually support multiple organizations.

Every relevant entity should have:

tenant_id

Avoid hard-coding one company.

---

# 34. API

Create REST endpoints such as:

GET /api/health

GET /api/calls
GET /api/calls/{id}

POST /api/calls
POST /api/calls/{id}/answer
POST /api/calls/{id}/hangup
POST /api/calls/{id}/hold
POST /api/calls/{id}/resume
POST /api/calls/{id}/transfer

GET /api/agents
POST /api/agents
GET /api/agents/{id}

GET /api/campaigns
POST /api/campaigns

GET /api/contacts
POST /api/contacts

GET /api/analytics

GET /api/events

WebSocket:

/ws/dashboard
/ws/calls/{call_id}
/ws/agents

Document all APIs.

---

# 35. Database

Use PostgreSQL.

Create models for:

users
roles
tenants
agents
agent_templates
calls
call_events
call_recordings
call_transcripts
transcript_messages
contacts
campaigns
campaign_contacts
sip_extensions
sip_trunks
agent_sessions
agent_tools
tool_calls
memories
system_events
audit_logs

Use UUID primary keys where appropriate.

Create migrations.

---

# 36. Docker

Create:

docker-compose.yml

Services:

postgres
redis
api
dashboard
voice-runtime
agent-runtime
nginx

Asterisk can either be:

1. External PBX

or

2. Optional Docker service.

Make PBX connection configurable.

---

# 37. Configuration

Create:

.env.example

Include:

DATABASE_URL
REDIS_URL

PBX_HOST
PBX_PORT
PBX_ARI_USERNAME
PBX_ARI_PASSWORD

SIP_USERNAME
SIP_PASSWORD
SIP_EXTENSION

LLM_PROVIDER
LLM_API_KEY
LLM_MODEL

STT_PROVIDER
STT_API_KEY
STT_MODEL

TTS_PROVIDER
TTS_API_KEY
TTS_MODEL

RECORD_CALLS

JWT_SECRET

Do not commit .env.

---

# 38. Error Handling

Every service must have structured error handling.

Errors should contain:

error_id
service
component
operation
message
timestamp
correlation_id

Dashboard must display meaningful errors.

---

# 39. Logging

Use structured JSON logs.

Example:

{
"timestamp": "...",
"level": "INFO",
"service": "voice-runtime",
"event": "tts.completed",
"call_id": "...",
"agent_id": "...",
"latency_ms": 310
}

---

# 40. Testing

Create:

Unit tests
Integration tests
API tests
Agent tests
Telephony mock tests
WebSocket tests

Do not require a real PBX for normal automated tests.

Create a MockTelephonyProvider.

Create MockSTT.

Create MockTTS.

Create MockLLM.

This allows the entire system to run in development without external services.

---

# 41. Development Mode

Provide:

DEV_MODE=true

In development mode:

* Mock PBX
* Mock calls
* Mock STT
* Mock TTS
* Mock LLM

Create simulated calls so the dashboard can be tested.

Example:

CALL #1001
Customer: Demo Customer
Language: bn-BD
Status: SPEAKING

This should make the UI demonstrable without a physical SIP trunk.

---

# 42. Production Mode

Production should allow:

Real Asterisk
Real SIP trunk
Real STT
Real LLM
Real TTS

All providers must be configurable.

Do not tightly couple the implementation to one vendor.

---

# 43. UI Design

Use a modern professional call-center design.

Requirements:

* Responsive
* Desktop-first
* Dark/light mode
* Sidebar navigation
* Real-time status indicators
* Tables
* Charts
* Call detail drawer/page
* Agent cards
* Toast notifications
* Loading states
* Empty states
* Error states

Do not create a generic template-looking dashboard.

Make it look like a professional AI contact-center platform.

---

# 44. Important UX

When a call is active, the operator should immediately see:

Who is calling
Which AI agent is handling it
Language
Call duration
Current agent state
Live transcript
Current tool/action
Latency
Transfer option
End-call option

---

# 45. AI Agent Prompt Architecture

Do not hard-code one giant prompt.

Use:

Base System Prompt
+
Agent Template Prompt
+
Business Instructions
+
Conversation Context
+
Customer Context
+
Available Tools

The final prompt should be assembled dynamically.

---

# 46. Example Agent

Create a demo:

"Bangladesh Customer Support Agent"

Behavior:

* Start in Bangla when caller speaks Bangla.
* Start in English when caller speaks English.
* Follow the caller's language.
* Handle Banglish where possible.
* Answer only using available knowledge/tools.
* Never invent customer/order information.
* Transfer to human when required.
* Keep responses concise and natural for phone conversation.
* Confirm important information when necessary.

---

# 47. Voice Conversation Requirements

Optimize for telephone conversation.

AI responses should generally be:

1–3 sentences.

Avoid:

* Markdown
* Long lists
* URLs read aloud
* Excessive explanations
* Robotic language

The AI should sound conversational.

---

# 48. Latency

Target:

Audio detection → STT
STT → LLM
LLM → TTS

Keep total perceived response latency as low as practical.

Expose latency metrics in the dashboard.

---

# 49. Observability

Every call must have a correlation ID.

Trace:

Call
→ Audio
→ STT
→ Agent
→ Tool
→ LLM
→ TTS
→ PBX

This allows debugging individual calls.

---

# 50. Documentation

Create:

README.md
ARCHITECTURE.md
API.md
TELEPHONY.md
AGENTS.md
DEPLOYMENT.md
DEVELOPMENT.md

Include diagrams using Mermaid where useful.

Document:

* local setup
* Docker setup
* Asterisk setup
* SIP configuration
* STT configuration
* TTS configuration
* LLM configuration
* dashboard usage
* creating an agent
* creating a campaign
* troubleshooting

---

# 51. Implementation Strategy

Do not attempt to build everything in one giant step.

Work incrementally:

PHASE 1
Project foundation
Database
FastAPI
Next.js
Docker
Authentication

PHASE 2
Dashboard
Mock calls
Mock agents
WebSocket events

PHASE 3
Agent Runtime
LLM abstraction
Agent Templates
Tool system

PHASE 4
Voice Runtime
STT
TTS
VAD
Barge-in

PHASE 5
Asterisk/PJSIP integration
Incoming calls
Outgoing calls

PHASE 6
Campaigns
Contacts
Call history
Recording

PHASE 7
MCP
Memory
RAG
Business integrations

PHASE 8
Security
Monitoring
Testing
Production hardening

---

# 52. Coding Rules

Follow these rules:

* Type-safe code where possible.
* Small modular services.
* Dependency injection.
* Clear interfaces.
* No unnecessary duplication.
* No hard-coded secrets.
* No hard-coded provider dependencies.
* No giant monolithic files.
* Strong validation.
* Structured logging.
* Comprehensive error handling.
* Tests for important logic.
* Write documentation while implementing.
* Keep configuration separate from code.

---

# 53. Important Architecture Principle

The platform must distinguish:

VOICE
↓
TELEPHONY

INTELLIGENCE
↓
AGENT RUNTIME

CAPABILITIES
↓
TOOLS / MCP

KNOWLEDGE
↓
MEMORY / RAG

CONTROL
↓
API

OBSERVABILITY
↓
DASHBOARD

Do not mix these responsibilities.

---

# 54. Future ASI OS Compatibility

The final architecture must allow this Voice Agent to become:

ASI OS
↓
Agent Runtime
↓
Agent Template
↓
Voice Calling Capability
↓
SIP/MCP/Tools

The Voice Calling Agent should therefore be installable/configurable as an Agent Template.

Future agents should be able to use:

call.make()
call.receive()
call.transfer()
call.speak()
call.listen()

through a standard capability interface.

---

# 55. Deliverables

At the end, provide:

1. Complete source code.
2. Monorepo structure.
3. Docker Compose.
4. .env.example.
5. Database migrations.
6. FastAPI backend.
7. Next.js dashboard.
8. WebSocket real-time event system.
9. Agent Runtime.
10. Voice Runtime.
11. Asterisk integration.
12. SIP configuration examples.
13. Agent Template system.
14. Mock providers.
15. Tests.
16. Documentation.
17. Deployment instructions.

---

# 56. Antigravity Working Rules

Before writing large amounts of code:

1. Inspect the repository.
2. Create/update ARCHITECTURE.md.
3. Define interfaces first.
4. Implement the smallest working vertical slice.
5. Run tests.
6. Start the development environment.
7. Verify the dashboard in a browser.
8. Fix console/runtime errors.
9. Continue to the next phase.

Do not claim something works unless you actually test it.

When a dependency or external API is unavailable, create a clean adapter/interface and a mock implementation rather than blocking the entire project.

At every major phase, report:

* What was implemented
* Files changed
* Tests executed
* Current status
* Remaining work
* Any configuration required

Start with PHASE 1 and continue through the phases while keeping the application runnable at every stage.

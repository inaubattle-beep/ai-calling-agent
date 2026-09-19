import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from packages.agent_core.agent import AgentConfig
from packages.agent_core.receptionist import AIReceptionistAgent
from packages.llm.mock import MockLLMProvider
from packages.llm.openai_compat import OpenAICompatibleLLMProvider
from packages.stt.mock import MockSTTProvider
from packages.stt.whisper import WhisperSTTProvider
from packages.telephony.asterisk import AsteriskTelephonyProvider
from packages.telephony.base import CallDirection, CallSession, CallState, TelephonyProvider
from packages.telephony.mock import MockTelephonyProvider
from packages.tts.mock import MockTTSProvider
from packages.tts.provider import OpenAICompatibleTTSProvider

from ..config import settings
from ..database import AsyncSessionLocal
from ..events.bus import event_bus
from ..models.agent import AgentModel
from ..models.call import CallModel
from ..models.transcript import TranscriptMessageModel
from ..models.settings import AppSettingsModel

logger = logging.getLogger("service.call_manager")


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class CallManager:
    """
    Central Call and Voice Pipeline Orchestrator.
    Manages telephony lifecycles, real-time AI dialogue processing, database persistence,
    and live dashboard telemetry.
    """

    def __init__(self) -> None:
        # Initialize Telephony Provider
        if settings.DEV_MODE or settings.PBX_HOST == "127.0.0.1" and not settings.PBX_ARI_PASSWORD:
            self.telephony: TelephonyProvider = MockTelephonyProvider()
            logger.info("Using MockTelephonyProvider (DEV_MODE)")
        else:
            self.telephony = AsteriskTelephonyProvider(
                host=settings.PBX_HOST,
                port=settings.PBX_PORT,
                username=settings.PBX_ARI_USERNAME,
                password=settings.PBX_ARI_PASSWORD,
                app_name=settings.PBX_ARI_APP,
                sip_extension=settings.SIP_EXTENSION,
            )
            logger.info("Using AsteriskTelephonyProvider")

        # Initialize AI Providers
        if settings.LLM_PROVIDER == "openai" and settings.LLM_API_KEY:
            self.llm = OpenAICompatibleLLMProvider(
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                base_url=settings.LLM_BASE_URL,
            )
        else:
            self.llm = MockLLMProvider()

        if settings.STT_PROVIDER == "whisper" and settings.STT_API_KEY:
            self.stt = WhisperSTTProvider(api_key=settings.STT_API_KEY, model=settings.STT_MODEL)
        else:
            self.stt = MockSTTProvider()

        if settings.TTS_PROVIDER == "openai" and settings.TTS_API_KEY:
            self.tts = OpenAICompatibleTTSProvider(
                api_key=settings.TTS_API_KEY,
                model=settings.TTS_MODEL,
                default_voice=settings.TTS_VOICE,
            )
        else:
            self.tts = MockTTSProvider()

        # Active agents per call
        self.active_agents: Dict[str, AIReceptionistAgent] = {}
        self._interrupted_calls: set[str] = set()
        self._simulation_tasks: Dict[str, asyncio.Task] = {}

        # Register telephony event forwarder
        self.telephony.register_event_handler(self._on_telephony_event)

    async def _on_telephony_event(self, event_name: str, data: Dict[str, Any]) -> None:
        call_id = data.get("call_id")
        await event_bus.publish(event_name, data, call_id=call_id)

    async def init_agent_record(self) -> None:
        """Create editable defaults once; runtime values remain database-backed."""
        async with AsyncSessionLocal() as session:
            app_settings = await session.get(AppSettingsModel, 1)
            if not app_settings:
                app_settings = AppSettingsModel(id=1)
                session.add(app_settings)
            stmt = select(AgentModel).where(AgentModel.id == "ai-receptionist-01")
            res = await session.execute(stmt)
            agent = res.scalar_one_or_none()
            if not agent:
                agent = AgentModel(
                    id="ai-receptionist-01",
                    name="AI Receptionist",
                    status="ONLINE",
                    model="bilingual-receptionist-v1",
                    primary_language="bn-BD",
                    stt_latency_ms=140,
                    llm_latency_ms=220,
                    tts_latency_ms=180,
                    description="Bilingual AI receptionist",
                    greeting="আসসালামু আলাইকুম, AI কল সেন্টারে আপনাকে স্বাগতম। আমি কীভাবে সাহায্য করতে পারি?",
                    system_prompt="You are a polite, helpful, and professional telephone AI Receptionist.",
                    supported_languages='["bn-BD", "en-US", "mixed"]',
                )
                session.add(agent)
                await session.commit()
                logger.info("Initialized default AI Receptionist record in database.")

    async def create_call(
        self,
        phone_number: str,
        direction: str = "OUTBOUND",
        language: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> CallModel:
        call_id = f"call-{uuid.uuid4().hex[:8]}"

        async with AsyncSessionLocal() as session:
            app_settings = await session.get(AppSettingsModel, 1)
            language = language or (app_settings.default_language if app_settings else "bn-BD")
            agent_id = agent_id or (app_settings.default_agent_id if app_settings else "ai-receptionist-01")
            if not await session.get(AgentModel, agent_id):
                raise ValueError(f"Agent {agent_id} not found")
            call = CallModel(
                id=call_id,
                phone_number=phone_number,
                direction=direction,
                language=language,
                status="DIALING" if direction == "OUTBOUND" else "RINGING",
                agent_id=agent_id,
                started_at=datetime.now(timezone.utc),
            )
            session.add(call)

            # Update agent status
            stmt = update(AgentModel).where(AgentModel.id == agent_id).values(
                status="BUSY", current_call_id=call_id
            )
            await session.execute(stmt)
            await session.commit()

        # Telephony make_call
        if direction == "OUTBOUND":
            await self.telephony.make_call(destination=phone_number, call_id=call_id)
        else:
            if isinstance(self.telephony, MockTelephonyProvider):
                await self.telephony.simulate_inbound_call(phone_number, language=language, call_id=call_id)

        await event_bus.publish(
            "call.created",
            {
                "call_id": call_id,
                "phone_number": phone_number,
                "direction": direction,
                "language": language,
                "status": "DIALING" if direction == "OUTBOUND" else "RINGING",
                "agent_id": agent_id,
            },
            call_id=call_id,
            agent_id=agent_id,
        )

        return call

    async def answer_call(self, call_id: str) -> None:
        async with AsyncSessionLocal() as session:
            call = await session.get(CallModel, call_id)
            if not call:
                return

            call.status = "CONNECTED"
            call.answered_at = datetime.now(timezone.utc)
            await session.commit()

        async with AsyncSessionLocal() as session:
            agent_record = await session.get(AgentModel, call.agent_id)
        if not agent_record:
            logger.error("Agent %s not found for call %s", call.agent_id, call_id)
            return
        agent_config = AgentConfig(
            agent_id=agent_record.id,
            name=agent_record.name,
            default_language=call.language or agent_record.primary_language,
            model=agent_record.model,
            greeting=agent_record.greeting,
            system_prompt=agent_record.system_prompt,
        )
        agent = AIReceptionistAgent(llm_provider=self.llm, config=agent_config)
        self.active_agents[call_id] = agent

        await self.telephony.answer_call(call_id)
        await event_bus.publish(
            "call.connected",
            {"call_id": call_id, "status": "CONNECTED"},
            call_id=call_id,
        )

        # Greet caller
        greeting = await agent.start_call(call_id, call.phone_number)
        await self.record_transcript(call_id, "ai", greeting, agent.current_language)

        # Transition agent state: SPEAKING greeting -> LISTENING
        await self.set_call_status(call_id, "SPEAKING")
        await asyncio.sleep(1.0)
        await self.set_call_status(call_id, "LISTENING")

    async def set_call_status(self, call_id: str, new_status: str) -> None:
        async with AsyncSessionLocal() as session:
            call = await session.get(CallModel, call_id)
            if call:
                call.status = new_status
                await session.commit()

        event_name = "call.state_changed"
        if new_status == "LISTENING":
            event_name = "agent.listening"
        elif new_status == "THINKING":
            event_name = "agent.thinking"
        elif new_status == "SPEAKING":
            event_name = "agent.speaking"

        await event_bus.publish(
            event_name,
            {"call_id": call_id, "status": new_status},
            call_id=call_id,
        )

    async def record_transcript(
        self,
        call_id: str,
        speaker: str,
        text: str,
        language: str = "bn-BD",
        latency_ms: Optional[int] = None,
    ) -> TranscriptMessageModel:
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        async with AsyncSessionLocal() as session:
            msg = TranscriptMessageModel(
                id=msg_id,
                call_id=call_id,
                speaker=speaker,
                text=text,
                language=language,
                latency_ms=latency_ms,
                timestamp=now,
            )
            session.add(msg)
            await session.commit()

        await event_bus.publish(
            "transcript.created",
            {
                "id": msg_id,
                "call_id": call_id,
                "speaker": speaker,
                "text": text,
                "language": language,
                "latency_ms": latency_ms,
                "timestamp": now.isoformat(),
            },
            call_id=call_id,
        )
        return msg

    async def process_caller_utterance(self, call_id: str, speech_text: str) -> str:
        """Runs the Voice Pipeline: STT -> Agent -> LLM -> TTS."""
        agent = self.active_agents.get(call_id)
        if not agent:
            agent = AIReceptionistAgent(llm_provider=self.llm)
            self.active_agents[call_id] = agent

        # Record Customer Speech
        await self.record_transcript(call_id, "customer", speech_text, agent.current_language)

        # Transition to THINKING
        await self.set_call_status(call_id, "THINKING")

        # LLM response generation
        ai_response = await agent.process_speech(call_id, speech_text)

        # Check if caller interrupted while thinking
        if call_id in self._interrupted_calls:
            self._interrupted_calls.discard(call_id)
            await self.set_call_status(call_id, "LISTENING")
            return ""

        # Transition to SPEAKING
        await self.set_call_status(call_id, "SPEAKING")
        agent.is_speaking = True

        # Synthesize TTS
        tts_res = await self.tts.synthesize(ai_response, language=agent.current_language)

        # Record AI transcript turn
        await self.record_transcript(
            call_id, "ai", ai_response, agent.current_language, latency_ms=tts_res.latency_ms
        )

        # Simulate audio playback duration with interruption check
        duration_sec = min(5.0, tts_res.duration_ms / 1000.0)
        elapsed = 0.0
        step = 0.2
        while elapsed < duration_sec:
            if call_id in self._interrupted_calls:
                logger.info(f"Barge-in: playback canceled for call {call_id}")
                self._interrupted_calls.discard(call_id)
                await agent.handle_interruption(call_id)
                await event_bus.publish(
                    "agent.interrupted",
                    {"call_id": call_id, "message": "Caller interrupted AI speech"},
                    call_id=call_id,
                )
                break
            await asyncio.sleep(step)
            elapsed += step

        agent.is_speaking = False
        await self.set_call_status(call_id, "LISTENING")
        return ai_response

    async def trigger_barge_in(self, call_id: str) -> None:
        """Simulates caller interruption (barge-in) when AI is speaking."""
        self._interrupted_calls.add(call_id)
        agent = self.active_agents.get(call_id)
        if agent and agent.is_speaking:
            await agent.handle_interruption(call_id)

        await event_bus.publish(
            "agent.interrupted",
            {"call_id": call_id, "status": "BARGE_IN_TRIGGERED"},
            call_id=call_id,
        )
        await self.set_call_status(call_id, "LISTENING")

    async def hangup_call(self, call_id: str, reason: str = "normal") -> None:
        # Cancel any ongoing simulation task for this call
        sim_task = self._simulation_tasks.pop(call_id, None)
        if sim_task and not sim_task.done():
            sim_task.cancel()

        now = datetime.now(timezone.utc)
        duration = 0

        async with AsyncSessionLocal() as session:
            call = await session.get(CallModel, call_id)
            if call and call.status != "ENDED":
                call.status = "ENDED"
                call.ended_at = now
                answered = ensure_utc(call.answered_at)
                started = ensure_utc(call.started_at)
                if answered:
                    duration = max(0, int((now - answered).total_seconds()))
                elif started:
                    duration = max(0, int((now - started).total_seconds()))
                call.duration = duration

                # Reset agent status to ONLINE
                if call.agent_id:
                    stmt = update(AgentModel).where(AgentModel.id == call.agent_id).values(
                        status="ONLINE", current_call_id=None
                    )
                    await session.execute(stmt)

                await session.commit()

        if call_id in self.active_agents:
            await self.active_agents[call_id].end_call(call_id)
            del self.active_agents[call_id]

        if isinstance(self.telephony, MockTelephonyProvider):
            try:
                await self.telephony.hangup_call(call_id, reason=reason)
            except KeyError:
                pass

        await event_bus.publish(
            "call.ended",
            {"call_id": call_id, "status": "ENDED", "duration": duration, "reason": reason},
            call_id=call_id,
        )

    async def simulate_realistic_call(
        self,
        phone_number: Optional[str] = None,
        language: Optional[str] = None,
        barge_in: bool = False,
    ) -> str:
        """
        Runs an automated end-to-end simulated conversation with realistic dialogue timing.
        """
        if not phone_number or not language:
            async with AsyncSessionLocal() as session:
                app_settings = await session.get(AppSettingsModel, 1)
                phone_number = phone_number or (app_settings.default_phone_number if app_settings else "+8801819203040")
                language = language or (app_settings.default_language if app_settings else "bn-BD")
        call = await self.create_call(phone_number, direction="INBOUND", language=language)
        call_id = call.id

        async def run_scenario():
            try:
                # Ringing for 1.2s
                await asyncio.sleep(1.2)
                # Answer
                await self.answer_call(call_id)
                await asyncio.sleep(1.5)

                if language == "bn-BD":
                    utterances = [
                        "আপনাদের কাস্টমার কেয়ার অফিস কখন পর্যন্ত খোলা থাকে?",
                        "আমার একটা পার্সেল আসার কথা ছিল, ডেলিভারি স্ট্যাটাস কি চেক করা যাবে?",
                        "অনেক ধন্যবাদ আপনার সুন্দর তথ্যের জন্য!",
                    ]
                else:
                    utterances = [
                        "Hello, what are your customer service hours today?",
                        "I wanted to inquire about my order delivery time.",
                        "That is very helpful, thank you so much!",
                    ]

                for i, utterance in enumerate(utterances):
                    # Check if call was ended prematurely
                    async with AsyncSessionLocal() as session:
                        c = await session.get(CallModel, call_id)
                        if not c or c.status == "ENDED":
                            return

                    # Caller pauses, then speaks
                    await asyncio.sleep(1.2)

                    # Trigger barge-in on second turn if requested
                    if barge_in and i == 1:
                        # Start AI utterance, then barge in after 0.5s
                        interruption_task = asyncio.create_task(self._schedule_barge_in(call_id, 0.6))
                        await self.process_caller_utterance(call_id, utterance)
                        await interruption_task
                    else:
                        await self.process_caller_utterance(call_id, utterance)

                # Wait 2 seconds and politely hang up
                await asyncio.sleep(2.0)
                await self.hangup_call(call_id, reason="caller_completed")

            except asyncio.CancelledError:
                logger.info(f"Simulation task for {call_id} cancelled")
            except Exception as e:
                logger.error(f"Error in simulated call scenario: {e}", exc_info=True)

        task = asyncio.create_task(run_scenario())
        self._simulation_tasks[call_id] = task
        return call_id

    async def _schedule_barge_in(self, call_id: str, delay_sec: float) -> None:
        await asyncio.sleep(delay_sec)
        logger.info(f"Triggering scheduled caller barge-in on call {call_id}")
        await self.trigger_barge_in(call_id)


# Global singleton call manager
call_manager = CallManager()

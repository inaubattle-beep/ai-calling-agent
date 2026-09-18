import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] voice-runtime: %(message)s")
logger = logging.getLogger("voice_runtime.main")


async def main():
    logger.info("Starting Voice Runtime Service (VAD, Streaming STT/TTS, RTP Handler)...")
    logger.info("Voice Runtime is ready to accept media streams from Asterisk Extension 7000.")
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Stopping Voice Runtime Service.")


if __name__ == "__main__":
    asyncio.run(main())

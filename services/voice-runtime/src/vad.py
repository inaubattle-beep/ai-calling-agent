import math
import struct
from typing import Tuple


class VoiceActivityDetector:
    """
    Real-time Voice Activity Detector (VAD).
    Calculates Root-Mean-Square (RMS) and zero-crossing rates on 16-bit PCM audio frames
    to distinguish active human speech from background noise.
    """

    def __init__(self, sample_rate: int = 16000, frame_duration_ms: int = 20, energy_threshold: float = 400.0) -> None:
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
        self.energy_threshold = energy_threshold
        self._consecutive_speech_frames = 0
        self._consecutive_silence_frames = 0

    def calculate_rms(self, frame_bytes: bytes) -> float:
        """Computes RMS amplitude for a 16-bit mono PCM frame."""
        count = len(frame_bytes) // 2
        if count == 0:
            return 0.0

        shorts = struct.unpack(f"<{count}h", frame_bytes[: count * 2])
        sum_squares = sum(s * s for s in shorts)
        return math.sqrt(sum_squares / count)

    def is_speech(self, frame_bytes: bytes) -> bool:
        rms = self.calculate_rms(frame_bytes)
        return rms > self.energy_threshold

    def process_frame(self, frame_bytes: bytes) -> Tuple[bool, bool]:
        """
        Processes frame and returns: (is_currently_speech, speech_just_started).
        """
        speech = self.is_speech(frame_bytes)
        speech_started = False

        if speech:
            self._consecutive_speech_frames += 1
            self._consecutive_silence_frames = 0
            if self._consecutive_speech_frames == 2:  # debounce 40ms
                speech_started = True
        else:
            self._consecutive_silence_frames += 1
            if self._consecutive_silence_frames > 8:  # 160ms silence resets speech count
                self._consecutive_speech_frames = 0

        return speech, speech_started

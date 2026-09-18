from dataclasses import dataclass
import re
from typing import Optional


@dataclass
class LanguageDetectionResult:
    code: str  # 'bn-BD', 'en-US', or 'mixed'
    name: str
    confidence: float


class LanguageDetector:
    """
    Detects caller language for bilingual phone conversations:
    Supports:
    - Bengali (bn-BD) with Bengali unicode range (\u0980-\u09FF)
    - English (en-US)
    - Banglish / Mixed code-switching
    """

    BANGLISH_PATTERNS = [
        r"\bbhai\b",
        r"\bamar\b",
        r"\bapnader\b",
        r"\bkobe\b",
        r"\bashbe\b",
        r"\bkemon\b",
        r"\bachhen\b",
        r"\bdhonnobad\b",
        r"\bkotha\b",
        r"\bbolo\b",
        r"\blagbe\b",
        r"\bhobe\b",
        r"\bparsel\b",
    ]

    def detect(self, text: str) -> LanguageDetectionResult:
        if not text or not text.strip():
            return LanguageDetectionResult(code="bn-BD", name="Bangla", confidence=0.5)

        text_clean = text.strip()

        # Check for Bengali script
        bengali_chars = len(re.findall(r"[\u0980-\u09FF]", text_clean))
        total_letters = len(re.findall(r"\w", text_clean)) or 1

        bengali_ratio = bengali_chars / total_letters

        if bengali_ratio > 0.4:
            # Check if there is also noticeable English script (mixed)
            english_chars = len(re.findall(r"[a-zA-Z]", text_clean))
            if english_chars > 3:
                return LanguageDetectionResult(code="mixed", name="Bangla-English Mixed", confidence=0.9)
            return LanguageDetectionResult(code="bn-BD", name="Bangla", confidence=min(1.0, 0.85 + bengali_ratio * 0.15))

        # Check for Banglish phonetic keywords in Latin script
        lower_text = text_clean.lower()
        banglish_matches = sum(1 for pattern in self.BANGLISH_PATTERNS if re.search(pattern, lower_text))

        if banglish_matches >= 1:
            return LanguageDetectionResult(code="mixed", name="Banglish (Mixed)", confidence=0.88)

        # Default to English
        return LanguageDetectionResult(code="en-US", name="English", confidence=0.92)

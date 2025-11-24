"""Prompt injection and jailbreak detection"""

import logging
import re
from typing import Any, Dict, List, Optional

from opentelemetry import trace

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
tracer = trace.get_tracer(__name__)

# Global instance
_prompt_injection_detector: Optional["PromptInjectionDetector"] = None


class PromptInjectionDetector:
    """Detect prompt injection and jailbreak attempts"""

    def __init__(self):
        """Initialize prompt injection detector"""
        self.enabled = settings.prompt_injection_detection_enabled
        self.patterns = self._load_injection_patterns()
        self.jailbreak_patterns = self._load_jailbreak_patterns()

    def _load_injection_patterns(self) -> List[re.Pattern]:
        """Load prompt injection patterns"""
        patterns = [
            # Instruction injection
            re.compile(r"ignore\s+(previous|above|all)\s+(instructions|prompts)", re.IGNORECASE),
            re.compile(r"forget\s+(previous|above|all)", re.IGNORECASE),
            re.compile(r"disregard\s+(previous|above|all)", re.IGNORECASE),
            # Role manipulation
            re.compile(r"you\s+are\s+(now|a|an)\s+", re.IGNORECASE),
            re.compile(r"act\s+as\s+if\s+you\s+are", re.IGNORECASE),
            re.compile(r"pretend\s+to\s+be", re.IGNORECASE),
            # System prompt extraction
            re.compile(r"system\s*:\s*", re.IGNORECASE),
            re.compile(r"system\s+prompt", re.IGNORECASE),
            re.compile(r"show\s+me\s+(your|the)\s+(system|original|initial)\s+prompt", re.IGNORECASE),
            # Token manipulation
            re.compile(r"repeat\s+(the\s+)?(word|token|phrase)\s+", re.IGNORECASE),
            re.compile(r"say\s+(the\s+)?(word|token|phrase)\s+", re.IGNORECASE),
            # Encoding tricks
            re.compile(r"\\x[0-9a-fA-F]{2}", re.IGNORECASE),  # Hex encoding
            re.compile(r"&#x[0-9a-fA-F]+;", re.IGNORECASE),  # HTML entities
            # Boundary markers
            re.compile(r"---+\s*(new|start|begin)", re.IGNORECASE),
            re.compile(r"```+\s*(new|start|begin|system)", re.IGNORECASE),
            # Direct command patterns
            re.compile(r"\[INST\]|\[/INST\]", re.IGNORECASE),
            re.compile(r"<\|im_start\|>|<\|im_end\|>", re.IGNORECASE),
        ]
        return patterns

    def _load_jailbreak_patterns(self) -> List[re.Pattern]:
        """Load jailbreak patterns"""
        patterns = [
            # DAN (Do Anything Now) variants
            re.compile(r"dan\s+mode|do\s+anything\s+now", re.IGNORECASE),
            re.compile(r"developer\s+mode|dev\s+mode", re.IGNORECASE),
            # Character roleplay
            re.compile(r"jailbreak|unrestricted|unfiltered", re.IGNORECASE),
            # Bypass requests
            re.compile(r"bypass\s+(safety|security|filter|restriction)", re.IGNORECASE),
            re.compile(r"remove\s+(safety|security|filter|restriction)", re.IGNORECASE),
            # Scenario manipulation
            re.compile(r"hypothetical\s+(scenario|situation|context)", re.IGNORECASE),
            re.compile(r"in\s+a\s+(hypothetical|fictional|imaginary)", re.IGNORECASE),
        ]
        return patterns

    def detect(self, text: str) -> Dict[str, Any]:
        """Detect prompt injection and jailbreak attempts"""
        if not self.enabled:
            return {
                "is_injection": False,
                "is_jailbreak": False,
                "score": 0.0,
                "patterns_matched": [],
                "risk_level": "low",
            }

        with tracer.start_as_current_span("prompt_injection_detection") as span:
            span.set_attribute("text_length", len(text))

            injection_matches = []
            jailbreak_matches = []

            # Check injection patterns
            for pattern in self.patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    injection_matches.append(
                        {
                            "pattern": pattern.pattern,
                            "match": match.group(),
                            "start": match.start(),
                            "end": match.end(),
                        }
                    )

            # Check jailbreak patterns
            for pattern in self.jailbreak_patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    jailbreak_matches.append(
                        {
                            "pattern": pattern.pattern,
                            "match": match.group(),
                            "start": match.start(),
                            "end": match.end(),
                        }
                    )

            # Calculate risk score (0.0 to 1.0)
            injection_count = len(injection_matches)
            jailbreak_count = len(jailbreak_matches)
            total_matches = injection_count + jailbreak_count

            # Base score from match count
            match_score = min(total_matches / 5.0, 1.0)

            # Boost score for jailbreaks (more dangerous)
            jailbreak_boost = jailbreak_count * 0.3

            # Boost score for multiple injection patterns
            injection_boost = min(injection_count * 0.2, 0.4)

            final_score = min(match_score + jailbreak_boost + injection_boost, 1.0)

            # Determine risk level
            if final_score >= 0.7:
                risk_level = "critical"
            elif final_score >= 0.4:
                risk_level = "high"
            elif final_score >= 0.2:
                risk_level = "medium"
            else:
                risk_level = "low"

            is_injection = injection_count > 0
            is_jailbreak = jailbreak_count > 0

            result = {
                "is_injection": is_injection,
                "is_jailbreak": is_jailbreak,
                "score": round(final_score, 3),
                "injection_matches": injection_matches,
                "jailbreak_matches": jailbreak_matches,
                "patterns_matched": injection_matches + jailbreak_matches,
                "risk_level": risk_level,
            }

            span.set_attribute("injection.detected", is_injection)
            span.set_attribute("injection.jailbreak", is_jailbreak)
            span.set_attribute("injection.score", final_score)
            span.set_attribute("injection.risk_level", risk_level)

            if is_injection or is_jailbreak:
                logger.warning(
                    f"Prompt injection detected: {risk_level} risk (score: {final_score})"
                )

            return result

    def is_safe(self, text: str, threshold: float = 0.3) -> bool:
        """Check if text is safe (score below threshold)"""
        detection = self.detect(text)
        return detection["score"] < threshold


# Global instance
_prompt_injection_detector: Optional[PromptInjectionDetector] = None


def get_prompt_injection_detector() -> PromptInjectionDetector:
    """Get or create prompt injection detector instance"""
    global _prompt_injection_detector

    if _prompt_injection_detector is None:
        _prompt_injection_detector = PromptInjectionDetector()

    return _prompt_injection_detector


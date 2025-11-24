"""Content policy checking"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from opentelemetry import trace

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
tracer = trace.get_tracer(__name__)

# Global instance
_content_policy_checker: Optional["ContentPolicyChecker"] = None


class ContentCategory(str, Enum):
    """Content categories for policy checking"""

    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    SEXUAL = "sexual"
    HARMFUL = "harmful"
    SELF_HARM = "self_harm"
    ILLEGAL = "illegal"
    MISINFORMATION = "misinformation"
    PRIVACY = "privacy"
    COPYRIGHT = "copyright"


class ContentPolicyChecker:
    """Check content against policy rules"""

    def __init__(self):
        """Initialize content policy checker"""
        self.enabled = settings.content_policy_enabled
        self.keywords = self._load_keywords()

    def _load_keywords(self) -> Dict[ContentCategory, List[str]]:
        """Load keyword lists for different content categories"""
        # This is a simplified version - in production, use ML models or external APIs
        return {
            ContentCategory.HATE_SPEECH: [
                # Add hate speech keywords here
            ],
            ContentCategory.VIOLENCE: [
                # Add violence keywords here
            ],
            ContentCategory.SEXUAL: [
                # Add sexual content keywords here
            ],
            ContentCategory.HARMFUL: [
                # Add harmful content keywords here
            ],
            ContentCategory.SELF_HARM: [
                "suicide",
                "self-harm",
                "kill myself",
                # Add self-harm keywords here
            ],
            ContentCategory.ILLEGAL: [
                # Add illegal activity keywords here
            ],
            ContentCategory.MISINFORMATION: [
                # Add misinformation patterns here
            ],
            ContentCategory.PRIVACY: [
                # Privacy violation patterns
            ],
            ContentCategory.COPYRIGHT: [
                # Copyright violation patterns
            ],
        }

    def check(
        self,
        text: str,
        categories: Optional[List[ContentCategory]] = None,
    ) -> Dict[str, Any]:
        """Check content against policy"""
        if not self.enabled:
            return {
                "violations": [],
                "is_violation": False,
                "violation_count": 0,
                "risk_score": 0.0,
            }

        with tracer.start_as_current_span("content_policy_check") as span:
            span.set_attribute("text_length", len(text))

            if categories is None:
                categories = list(ContentCategory)

            violations = []
            text_lower = text.lower()

            for category in categories:
                if category not in self.keywords:
                    continue

                keywords = self.keywords[category]
                matched_keywords = [
                    kw for kw in keywords if kw.lower() in text_lower
                ]

                if matched_keywords:
                    violations.append(
                        {
                            "category": category.value,
                            "matched_keywords": matched_keywords,
                        }
                    )

            violation_count = len(violations)
            risk_score = min(violation_count / len(categories), 1.0) if categories else 0.0

            result = {
                "violations": violations,
                "is_violation": violation_count > 0,
                "violation_count": violation_count,
                "risk_score": round(risk_score, 3),
            }

            span.set_attribute("policy.violations", violation_count)
            span.set_attribute("policy.risk_score", risk_score)

            if violations:
                logger.warning(
                    f"Content policy violation detected: {violation_count} violations"
                )

            return result

    def is_compliant(
        self,
        text: str,
        categories: Optional[List[ContentCategory]] = None,
        allow_threshold: float = 0.0,
    ) -> bool:
        """Check if content is policy compliant"""
        check_result = self.check(text, categories)
        return check_result["risk_score"] <= allow_threshold


# Global instance
_content_policy_checker: Optional[ContentPolicyChecker] = None


def get_content_policy_checker() -> ContentPolicyChecker:
    """Get or create content policy checker instance"""
    global _content_policy_checker

    if _content_policy_checker is None:
        _content_policy_checker = ContentPolicyChecker()

    return _content_policy_checker


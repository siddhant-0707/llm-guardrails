"""PII (Personally Identifiable Information) detection and redaction"""

import logging
from typing import Any, Dict, List, Optional

from opentelemetry import trace
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
tracer = trace.get_tracer(__name__)

# Global instance
_pii_detector: Optional["PIIDetector"] = None


class PIIDetector:
    """PII detection and redaction using Presidio"""

    def __init__(self):
        """Initialize PII detector with Presidio"""
        self.analyzer = None
        self.anonymizer = AnonymizerEngine()
        self.enabled = settings.pii_redaction_enabled
        
        try:
            # Check if spaCy model is available first
            import spacy
            try:
                nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model 'en_core_web_sm' is available")
            except OSError:
                logger.warning("spaCy model 'en_core_web_sm' not found. PII detection will be disabled.")
                logger.info("Install it with: uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl")
                self.enabled = False
                return
            
            # Initialize Presidio with explicit model configuration to prevent auto-download
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            from presidio_analyzer import AnalyzerEngine
            
            # Configure NLP engine provider to use existing model
            configuration = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
            }
            
            provider = NlpEngineProvider(nlp_configuration=configuration)
            nlp_engine = provider.create_engine()
            
            self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
            logger.info("Presidio AnalyzerEngine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Presidio AnalyzerEngine: {e}")
            logger.warning("PII detection will be disabled.")
            self.enabled = False

    def detect(self, text: str, language: str = "en") -> List[Dict[str, Any]]:
        """Detect PII entities in text"""
        if not self.enabled or self.analyzer is None:
            return []

        with tracer.start_as_current_span("pii_detection") as span:
            span.set_attribute("text_length", len(text))
            span.set_attribute("language", language)

            try:
                results = self.analyzer.analyze(text=text, language=language)
                detections = [
                    {
                        "entity_type": result.entity_type,
                        "start": result.start,
                        "end": result.end,
                        "score": result.score,
                        "text": text[result.start : result.end],
                    }
                    for result in results
                ]

                span.set_attribute("pii.detections_count", len(detections))
                span.set_attribute(
                    "pii.entity_types", [d["entity_type"] for d in detections]
                )

                logger.info(f"Detected {len(detections)} PII entities in text")
                return detections

            except Exception as e:
                span.record_exception(e)
                logger.error(f"Error detecting PII: {e}")
                return []

    def redact(
        self,
        text: str,
        language: str = "en",
        operator: str = "replace",
        anonymizer_config: Optional[Dict[str, OperatorConfig]] = None,
    ) -> Dict[str, Any]:
        """Redact PII entities from text"""
        if not self.enabled:
            return {"text": text, "detections": [], "redacted_count": 0}

        with tracer.start_as_current_span("pii_redaction") as span:
            span.set_attribute("text_length", len(text))
            span.set_attribute("language", language)
            span.set_attribute("operator", operator)

            try:
                # Detect PII
                detections = self.detect(text, language)
                if not detections:
                    return {"text": text, "detections": [], "redacted_count": 0}

                # Convert to Presidio format
                analyzer_results = [
                    type(
                        "AnalyzerResult",
                        (),
                        {
                            "entity_type": d["entity_type"],
                            "start": d["start"],
                            "end": d["end"],
                            "score": d["score"],
                        },
                    )()
                    for d in detections
                ]

                # Anonymize
                if anonymizer_config is None:
                    anonymizer_config = {
                        result.entity_type: OperatorConfig(operator, {})
                        for result in analyzer_results
                    }

                anonymized = self.anonymizer.anonymize(
                    text=text,
                    analyzer_results=analyzer_results,
                    operators=anonymizer_config,
                )

                span.set_attribute("pii.redacted_count", len(detections))
                logger.info(
                    f"Redacted {len(detections)} PII entities from text using '{operator}' operator"
                )

                return {
                    "text": anonymized.text,
                    "detections": detections,
                    "redacted_count": len(detections),
                }

            except Exception as e:
                span.record_exception(e)
                logger.error(f"Error redacting PII: {e}")
                return {"text": text, "detections": [], "redacted_count": 0}

    def mask(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Mask PII entities (replace with [REDACTED])"""
        return self.redact(text, language, operator="mask")

    def hash(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Hash PII entities"""
        return self.redact(text, language, operator="hash")


def get_pii_detector() -> PIIDetector:
    """Get or create PII detector instance"""
    global _pii_detector

    if _pii_detector is None:
        _pii_detector = PIIDetector()

    return _pii_detector


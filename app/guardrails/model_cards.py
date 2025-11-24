"""Model card management"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global instance
_model_card_manager: Optional["ModelCardManager"] = None


class ModelCard(BaseModel):
    """Model card schema"""

    model_id: str = Field(..., description="Unique model identifier")
    model_name: str = Field(..., description="Model name")
    provider: str = Field(..., description="Model provider (OpenAI, Anthropic, etc.)")
    version: str = Field(default="1.0", description="Model version")
    description: str = Field(..., description="Model description")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities")
    limitations: List[str] = Field(default_factory=list, description="Model limitations")
    safety_info: Dict[str, Any] = Field(
        default_factory=dict, description="Safety information"
    )
    usage_guidelines: List[str] = Field(
        default_factory=list, description="Usage guidelines"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "model_id": "gpt-4-turbo-preview",
                "model_name": "GPT-4 Turbo",
                "provider": "OpenAI",
                "version": "preview",
                "description": "Large multimodal model with improved capabilities",
                "capabilities": ["text-generation", "code-generation", "analysis"],
                "limitations": [
                    "May produce inaccurate information",
                    "Knowledge cutoff in 2023",
                ],
                "safety_info": {
                    "safety_filters": True,
                    "content_moderation": True,
                },
                "usage_guidelines": [
                    "Review outputs for accuracy",
                    "Use for appropriate use cases",
                ],
            }
        }


class ModelCardManager:
    """Manage model cards"""

    def __init__(self):
        """Initialize model card manager"""
        self._cards: Dict[str, ModelCard] = {}
        self._load_default_cards()

    def _load_default_cards(self) -> None:
        """Load default model cards"""
        default_cards = [
            ModelCard(
                model_id="gemini-pro",
                model_name="Gemini Pro",
                provider="Google",
                version="1.0",
                description="Google's advanced language model with strong reasoning and instruction following",
                capabilities=["text-generation", "code-generation", "analysis", "reasoning", "free-tier"],
                limitations=[
                    "May produce inaccurate information",
                    "Knowledge cutoff may vary",
                    "Rate limits on free tier",
                ],
                safety_info={
                    "safety_filters": True,
                    "content_moderation": True,
                    "refusal_behavior": True,
                },
                usage_guidelines=[
                    "Review outputs for accuracy and completeness",
                    "Use for appropriate use cases",
                    "Free tier available with rate limits",
                    "Implement additional guardrails for production",
                ],
            ),
            ModelCard(
                model_id="gemini-pro-vision",
                model_name="Gemini Pro Vision",
                provider="Google",
                version="1.0",
                description="Multimodal model that understands text and images",
                capabilities=["text-generation", "image-understanding", "multimodal", "free-tier"],
                limitations=[
                    "Image input requires specific formatting",
                    "May produce inaccurate information",
                    "Rate limits on free tier",
                ],
                safety_info={
                    "safety_filters": True,
                    "content_moderation": True,
                },
                usage_guidelines=[
                    "Suitable for multimodal tasks",
                    "Review outputs carefully",
                ],
            ),
            ModelCard(
                model_id="gpt-4-turbo-preview",
                model_name="GPT-4 Turbo",
                provider="OpenAI",
                version="preview",
                description="Large multimodal model with improved capabilities and knowledge cutoff",
                capabilities=["text-generation", "code-generation", "analysis", "multimodal"],
                limitations=[
                    "May produce inaccurate information",
                    "Knowledge cutoff in April 2023",
                    "Paid API required",
                ],
                safety_info={
                    "safety_filters": True,
                    "content_moderation": True,
                    "refusal_behavior": True,
                },
                usage_guidelines=[
                    "Review outputs for accuracy and completeness",
                    "Use for appropriate use cases",
                    "Implement additional guardrails for production",
                ],
            ),
        ]

        for card in default_cards:
            self._cards[card.model_id] = card

    def get_card(self, model_id: str) -> Optional[ModelCard]:
        """Get model card by ID"""
        return self._cards.get(model_id)

    def list_cards(self) -> List[ModelCard]:
        """List all model cards"""
        return list(self._cards.values())

    def create_card(self, card: ModelCard) -> ModelCard:
        """Create a new model card"""
        if card.model_id in self._cards:
            raise ValueError(f"Model card {card.model_id} already exists")

        self._cards[card.model_id] = card
        logger.info(f"Created model card for {card.model_id}")
        return card

    def update_card(self, model_id: str, updates: Dict[str, Any]) -> Optional[ModelCard]:
        """Update an existing model card"""
        if model_id not in self._cards:
            return None

        card = self._cards[model_id]
        update_data = updates.copy()
        update_data["updated_at"] = datetime.utcnow()

        # Update fields
        for key, value in update_data.items():
            if hasattr(card, key):
                setattr(card, key, value)

        logger.info(f"Updated model card for {model_id}")
        return card

    def delete_card(self, model_id: str) -> bool:
        """Delete a model card"""
        if model_id not in self._cards:
            return False

        del self._cards[model_id]
        logger.info(f"Deleted model card for {model_id}")
        return True


# Global instance
_model_card_manager: Optional[ModelCardManager] = None


def get_model_card_manager() -> ModelCardManager:
    """Get or create model card manager instance"""
    global _model_card_manager

    if _model_card_manager is None:
        _model_card_manager = ModelCardManager()

    return _model_card_manager


"""Guardrails API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.guardrails.pii import get_pii_detector, PIIDetector
from app.guardrails.prompt_injection import (
    get_prompt_injection_detector,
    PromptInjectionDetector,
)
from app.guardrails.content_policy import (
    ContentCategory,
    get_content_policy_checker,
    ContentPolicyChecker,
)
from app.guardrails.model_cards import (
    get_model_card_manager,
    ModelCardManager,
    ModelCard,
)

router = APIRouter()


class TextRequest(BaseModel):
    """Text analysis request"""

    text: str = Field(..., description="Text to analyze")
    language: str = Field(default="en", description="Language code")


class PIIDetectionResponse(BaseModel):
    """PII detection response"""

    detections: list
    redacted_text: str | None = None
    redacted_count: int = 0


class PromptInjectionResponse(BaseModel):
    """Prompt injection detection response"""

    is_injection: bool
    is_jailbreak: bool
    score: float
    risk_level: str
    patterns_matched: list


class ContentPolicyResponse(BaseModel):
    """Content policy check response"""

    is_violation: bool
    violations: list
    violation_count: int
    risk_score: float


@router.post("/pii/detect", response_model=PIIDetectionResponse)
async def detect_pii(
    request: TextRequest,
    detector: PIIDetector = Depends(get_pii_detector),
) -> PIIDetectionResponse:
    """Detect PII in text"""
    detections = detector.detect(request.text, request.language)
    return PIIDetectionResponse(
        detections=detections,
        redacted_count=len(detections),
    )


@router.post("/pii/redact", response_model=PIIDetectionResponse)
async def redact_pii(
    request: TextRequest,
    detector: PIIDetector = Depends(get_pii_detector),
) -> PIIDetectionResponse:
    """Redact PII from text"""
    result = detector.redact(request.text, request.language)
    return PIIDetectionResponse(
        detections=result["detections"],
        redacted_text=result["text"],
        redacted_count=result["redacted_count"],
    )


@router.post("/prompt-injection/detect", response_model=PromptInjectionResponse)
async def detect_prompt_injection(
    request: TextRequest,
    detector: PromptInjectionDetector = Depends(get_prompt_injection_detector),
) -> PromptInjectionResponse:
    """Detect prompt injection and jailbreak attempts"""
    result = detector.detect(request.text)
    return PromptInjectionResponse(
        is_injection=result["is_injection"],
        is_jailbreak=result["is_jailbreak"],
        score=result["score"],
        risk_level=result["risk_level"],
        patterns_matched=result["patterns_matched"],
    )


@router.post("/content-policy/check", response_model=ContentPolicyResponse)
async def check_content_policy(
    request: TextRequest,
    checker: ContentPolicyChecker = Depends(get_content_policy_checker),
) -> ContentPolicyResponse:
    """Check content against policy"""
    result = checker.check(request.text)
    return ContentPolicyResponse(
        is_violation=result["is_violation"],
        violations=result["violations"],
        violation_count=result["violation_count"],
        risk_score=result["risk_score"],
    )


@router.get("/model-cards", response_model=list[ModelCard])
async def list_model_cards(
    manager: ModelCardManager = Depends(get_model_card_manager),
) -> list[ModelCard]:
    """List all model cards"""
    return manager.list_cards()


@router.get("/model-cards/{model_id}", response_model=ModelCard)
async def get_model_card(
    model_id: str,
    manager: ModelCardManager = Depends(get_model_card_manager),
) -> ModelCard:
    """Get model card by ID"""
    card = manager.get_card(model_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model card {model_id} not found",
        )
    return card


@router.post("/model-cards", response_model=ModelCard, status_code=status.HTTP_201_CREATED)
async def create_model_card(
    card: ModelCard,
    manager: ModelCardManager = Depends(get_model_card_manager),
) -> ModelCard:
    """Create a new model card"""
    try:
        return manager.create_card(card)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/analyze", response_model=dict)
async def analyze_text(
    request: TextRequest,
    pii_detector: PIIDetector = Depends(get_pii_detector),
    injection_detector: PromptInjectionDetector = Depends(get_prompt_injection_detector),
    policy_checker: ContentPolicyChecker = Depends(get_content_policy_checker),
) -> dict:
    """Comprehensive text analysis with all guardrails"""
    results = {
        "text": request.text,
        "pii": pii_detector.detect(request.text, request.language),
        "prompt_injection": injection_detector.detect(request.text),
        "content_policy": policy_checker.check(request.text),
    }

    # Overall safety score
    safety_scores = [
        0.0 if results["pii"] else 1.0,
        1.0 - results["prompt_injection"]["score"],
        1.0 - results["content_policy"]["risk_score"],
    ]
    results["overall_safety_score"] = round(sum(safety_scores) / len(safety_scores), 3)
    results["is_safe"] = (
        len(results["pii"]) == 0
        and not results["prompt_injection"]["is_injection"]
        and not results["content_policy"]["is_violation"]
    )

    return results


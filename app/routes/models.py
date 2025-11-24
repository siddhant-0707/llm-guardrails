"""Model management and fine-tuning API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.models.training import ModelTrainer, get_model_trainer
from app.models.mlflow_client import MLflowClient, get_mlflow_client
from app.models.conversion import ONNXConverter, get_onnx_converter

router = APIRouter()


class TrainingRequest(BaseModel):
    """Model training request"""

    model_name: str = Field(..., description="Base model name (e.g., 'meta-llama/Llama-2-7b-hf')")
    training_data: List[Dict[str, str]] = Field(
        ..., description="Training data: list of {'text': '...'} dicts"
    )
    output_dir: str = Field(default="./checkpoints", description="Output directory")
    training_args: Optional[Dict[str, Any]] = Field(
        default=None, description="Training arguments"
    )
    lora_config: Optional[Dict[str, Any]] = Field(
        default=None, description="LoRA configuration"
    )


class TrainingResponse(BaseModel):
    """Model training response"""

    run_id: str
    model_uri: str
    output_dir: str
    training_loss: float
    metrics: Dict[str, Any]


class ConversionRequest(BaseModel):
    """Model conversion request"""

    model_path: str = Field(..., description="Path to model directory")
    output_path: str = Field(..., description="Output path")
    model_name: Optional[str] = Field(default=None, description="Model name")
    opset_version: int = Field(default=14, description="ONNX opset version")


class ConversionResponse(BaseModel):
    """Model conversion response"""

    output_path: str
    model_size: int
    input_shape: Optional[List[int]] = None
    output_shape: Optional[List[int]] = None


@router.post("/train", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
async def train_model(
    request: TrainingRequest,
    trainer: ModelTrainer = Depends(get_model_trainer),
) -> TrainingResponse:
    """Fine-tune a model using LoRA/PEFT"""
    try:
        result = trainer.train(
            model_name=request.model_name,
            training_data=request.training_data,
            output_dir=request.output_dir,
            training_args=request.training_args,
            lora_config=request.lora_config,
        )
        return TrainingResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {str(e)}",
        )


@router.post("/convert/onnx", response_model=ConversionResponse)
async def convert_to_onnx(
    request: ConversionRequest,
    converter: ONNXConverter = Depends(get_onnx_converter),
) -> ConversionResponse:
    """Convert model to ONNX format"""
    try:
        result = converter.convert_to_onnx(
            model_path=request.model_path,
            output_path=request.output_path,
            model_name=request.model_name,
            opset_version=request.opset_version,
        )
        return ConversionResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ONNX conversion failed: {str(e)}",
        )


@router.post("/convert/pytorch")
async def convert_to_pytorch(
    model_path: str,
    output_path: str,
    converter: ONNXConverter = Depends(get_onnx_converter),
) -> Dict[str, Any]:
    """Convert model to PyTorch format for edge deployment"""
    try:
        result = converter.convert_to_pytorch(
            model_path=model_path,
            output_path=output_path,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PyTorch conversion failed: {str(e)}",
        )


@router.get("/experiments")
async def list_experiments(
    mlflow_client: MLflowClient = Depends(get_mlflow_client),
) -> Dict[str, Any]:
    """List MLflow experiments and runs"""
    try:
        runs = mlflow_client.search_runs()
        return {"runs": runs, "count": len(runs)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list experiments: {str(e)}",
        )


@router.get("/experiments/{run_id}")
async def get_experiment(
    run_id: str,
    mlflow_client: MLflowClient = Depends(get_mlflow_client),
) -> Dict[str, Any]:
    """Get experiment run details"""
    try:
        run = mlflow_client.get_run(run_id)
        return run
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found: {str(e)}",
        )


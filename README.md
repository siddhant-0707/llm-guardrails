# LLM Guardrails & Observability Service

A production-ready microservice that wraps LLM calls with comprehensive guardrails, observability, and agent orchestration capabilities.

## Features

### 🛡️ Guardrails & Safety
- **Prompt Injection Detection**: Detect and prevent prompt injection and jailbreak attempts
- **PII Redaction**: Automatically detect and redact personally identifiable information
- **Content Policy Checking**: Enforce content policies and safety guidelines
- **Model Cards**: Manage and track model metadata, capabilities, and limitations

### ⚡ Performance & Reliability
- **Rate Limiting**: Redis-based rate limiting with per-minute and per-hour limits
- **Retry Logic**: Exponential backoff for resilient API calls
- **Health Checks**: Comprehensive health monitoring endpoints

### 📊 Observability
- **OpenTelemetry**: Full instrumentation for traces, metrics, and logs
- **Distributed Tracing**: Track requests across service boundaries
- **Metrics Export**: Prometheus-compatible metrics

### 🤖 Agents & Orchestration
- **LangGraph Integration**: Orchestrate tool-using agents with retrieval, reasoning, and action nodes
- **Mem0 Memory**: Long-term memory management for conversational agents
- **Vector Database Backends**: Pluggable backends (FAISS, pgvector, Qdrant) for retrieval

### 🧠 Model Management
- **Fine-tuning**: LoRA/PEFT fine-tuning for Llama/Phi models
- **MLflow Integration**: Track experiments, parameters, and metrics
- **Model Conversion**: Convert models to ONNX and PyTorch for edge deployment

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
│  (Main Service) │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────────┐
    │         │          │              │
┌───▼───┐ ┌──▼───┐ ┌────▼────┐ ┌──────▼──────┐
│ Redis │ │ Mem0 │ │ Vector  │ │   MLflow    │
│       │ │       │ │   DB    │ │             │
└───────┘ └───────┘ └─────────┘ └─────────────┘
```

## Quick Start

### Prerequisites
- Python 3.10+
- Docker and Docker Compose
- Redis (or use Docker Compose)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/llm-guardrails.git
cd llm-guardrails
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start dependencies with Docker Compose**
```bash
docker-compose up -d redis postgres qdrant mlflow otel-collector
```

6. **Run the application**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the service is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Checks
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health with dependencies

### Guardrails
- `POST /api/v1/guardrails/pii/detect` - Detect PII in text
- `POST /api/v1/guardrails/pii/redact` - Redact PII from text
- `POST /api/v1/guardrails/prompt-injection/detect` - Detect prompt injection attempts
- `POST /api/v1/guardrails/content-policy/check` - Check content against policy
- `POST /api/v1/guardrails/analyze` - Comprehensive text analysis
- `GET /api/v1/guardrails/model-cards` - List all model cards
- `GET /api/v1/guardrails/model-cards/{model_id}` - Get model card

### Agents
- `POST /api/v1/agents/execute` - Execute agent workflow
- `POST /api/v1/agents/memory` - Add memory
- `POST /api/v1/agents/memory/search` - Search memories
- `GET /api/v1/agents/memory/{user_id}` - Get all memories
- `DELETE /api/v1/agents/memory/{user_id}/{memory_id}` - Delete memory

### Models
- `POST /api/v1/models/train` - Fine-tune a model
- `POST /api/v1/models/convert/onnx` - Convert to ONNX
- `POST /api/v1/models/convert/pytorch` - Convert to PyTorch
- `GET /api/v1/models/experiments` - List MLflow experiments
- `GET /api/v1/models/experiments/{run_id}` - Get experiment details

## Configuration

Key configuration options in `.env`:

```env
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# Guardrails
GUARDRAILS_ENABLED=true
PII_REDACTION_ENABLED=true
CONTENT_POLICY_ENABLED=true
PROMPT_INJECTION_DETECTION_ENABLED=true

# Vector Database
VECTOR_DB_TYPE=faiss  # Options: faiss, pgvector, qdrant
```

## Development

### Running Tests
```bash
pytest tests/ -v --cov=app --cov-report=html
```

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy app/
```

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

## Vector Database Backends

The service supports multiple vector database backends:

### FAISS (Default)
Fast, in-memory similarity search. Good for development and small datasets.

```env
VECTOR_DB_TYPE=faiss
```

### pgvector
PostgreSQL with vector extension. Good for production with existing PostgreSQL infrastructure.

```env
VECTOR_DB_TYPE=pgvector
PGVECTOR_HOST=localhost
PGVECTOR_PORT=5432
PGVECTOR_DB=vectorstore
```

### Qdrant
Dedicated vector database. Good for large-scale production deployments.

```env
VECTOR_DB_TYPE=qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## Model Fine-tuning

Fine-tune models using LoRA/PEFT:

```python
POST /api/v1/models/train
{
    "model_name": "meta-llama/Llama-2-7b-hf",
    "training_data": [
        {"text": "Your training examples here..."}
    ],
    "lora_config": {
        "r": 8,
        "lora_alpha": 16,
        "target_modules": ["q_proj", "v_proj"]
    }
}
```

Experiments are automatically tracked in MLflow.

## Observability

### OpenTelemetry

The service is instrumented with OpenTelemetry. Configure the OTLP endpoint:

```env
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### Metrics

Metrics are exposed at `/metrics` endpoint (Prometheus format).

## Docker Deployment

Build and run with Docker:

```bash
docker build -t llm-guardrails .
docker run -p 8000:8000 --env-file .env llm-guardrails
```

Or use Docker Compose:

```bash
docker-compose up
```

## CI/CD

GitHub Actions workflows are included:
- **CI**: Linting, testing, and security scanning
- **CD**: Docker build and deployment (configure secrets)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.

## Roadmap

- [ ] Enhanced prompt injection detection with ML models
- [ ] Support for more LLM providers (Anthropic, Cohere, etc.)
- [ ] Advanced content policy enforcement
- [ ] Multi-tenant support
- [ ] GraphQL API endpoint
- [ ] WebSocket support for streaming responses


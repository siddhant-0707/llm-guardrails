# Quick Start Guide

This guide will help you get started with the LLM Guardrails & Observability Service quickly.

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- 8GB+ RAM (for running ML models)
- Git

## Installation Steps

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/llm-guardrails.git
cd llm-guardrails

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set your API keys
# At minimum, set:
# - GOOGLE_API_KEY=your_key_here (Get free API key from https://makersuite.google.com/app/apikey)
# - SECRET_KEY=your_secret_key_here
```

### 3. Start Dependencies

```bash
# Start all required services
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 4. Run the Application

```bash
# Using uvicorn directly
uvicorn app.main:app --reload

# Or using the Makefile
make run
```

The service will be available at `http://localhost:8000`

## Verify Installation

1. **Check Health**
```bash
curl http://localhost:8000/api/v1/health
```

2. **View API Documentation**
   - Open http://localhost:8000/docs in your browser

3. **Test Guardrails**
```bash
curl -X POST http://localhost:8000/api/v1/guardrails/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test message"}'
```

## Common Tasks

### Run Tests
```bash
pytest tests/ -v
```

### Format Code
```bash
make format
```

### Check Code Quality
```bash
make lint
```

### Stop Services
```bash
docker-compose down
```

## Next Steps

1. Read the [README.md](README.md) for full documentation
2. Explore the API at http://localhost:8000/docs
3. Review example requests in the test files
4. Customize guardrails for your use case

## Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
docker-compose ps redis
# Restart if needed
docker-compose restart redis
```

### Port Already in Use
```bash
# Change port in .env
API_PORT=8001
```

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

## Support

For issues, please open an issue on GitHub.


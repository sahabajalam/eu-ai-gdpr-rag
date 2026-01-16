# AI/ML Portfolio Project Best Practices

**Solo Developer | Entry-Level Portfolio | Jan 2026**

> **Your Context**: Building 5 portfolio projects (RAG, MLOps, GraphRAG, Multi-Agent, Fine-tuning) to demonstrate production-level skills for AI Engineer roles. Solo work, no team constraints.

**Philosophy**: Use modern tools, avoid over-engineering, focus on what recruiters actually check.

---

## 🎯 The Stack (No Options, This Is What You Use)

### Package Management
**Use: UV**
- Period. Don't use Poetry, pip-tools, or Conda.
- Fastest, modern, zero-config needed.

```bash
# Install UV once
curl -LsSf https://astral.sh/uv/install.sh | sh

# Every new project
uv init
uv python install 3.11
uv add torch transformers langchain fastapi pydantic uvicorn
uv add --dev pytest ruff mypy pre-commit pytest-cov pytest-snapshot
```

### Code Quality
**Use: Ruff (linting + formatting)**
- Don't use black, isort, flake8 separately
- Ruff does everything in one tool

---

## 📁 Project Structure (Use This Exact Layout)

```
project-name/
├── src/
│   ├── data/           # Data loading, validation
│   ├── features/       # Feature engineering
│   ├── models/         # Model definitions
│   ├── training/       # Training loops
│   ├── serving/        # API endpoints
│   └── utils/          # Shared utilities (logging, errors)
├── configs/            # YAML configs
├── tests/
│   ├── unit/           # 70% of your tests here
│   └── integration/    # 20% of your tests here
├── notebooks/          # Exploration ONLY
├── scripts/
│   ├── train.py
│   └── serve.py
├── .github/
│   └── workflows/      # CI/CD (GitHub Actions)
├── data/               # Gitignored (DVC tracked)
├── models/             # Gitignored
├── .env.example        # Commit this
├── .env                # DON'T commit
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
└── README.md
```

---

## 🔐 Secrets Management

### Setup Pattern

**1. Create `.env.example` (commit this)**
```bash
# .env.example (Safe to share)
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=postgresql://user:pass@localhost/db
NEO4J_URI=bolt://localhost:7687
```

**2. Create `.env` (DON'T commit)**
```bash
# Copy and fill with real values
cp .env.example .env
# Edit .env with actual secrets
```

**3. Loading Secrets (Pydantic)**
```python
# src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    database_url: str
    neo4j_uri: str = "bolt://localhost:7687"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" # Ignore extra env vars

settings = Settings()
```

---

## 📄 Complete Configuration Files

### pyproject.toml (Full Template)

```toml
[project]
name = "portfolio-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "torch>=2.1.0",
    "fastapi>=0.109.0",
    "pydantic>=2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-snapshot>=0.9.0",
    "ruff>=0.1.9",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B"]
ignore = ["E501"] # Formatting handles line length

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--cov=src", "--cov-report=term-missing"]

[tool.uv.scripts]
test = "pytest"
lint = "ruff check src/"
format = "ruff format src/"
run = "python -m src.serving.api"
```

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-added-large-files
        args: ['--maxkb=1000']
```

### .gitignore

```text
__pycache__/
*.py[cod]
.env
.venv/
data/
models/
*.log
.coverage
htmlcov/
.DS_Store
outputs/
mlruns/
.pytest_cache/
```

---

## 🪵 Logging Setup (Essential)

```python
# src/utils/logging.py
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: Path = None):
    """Configure logging for the application."""
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
```

---

## ⚠️ Error Handling Patterns

```python
# src/utils/error_handling.py
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def safe_execute(default_return=None, exceptions: tuple = (Exception,)):
    """Decorator for safe function execution with fallback."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                logger.error(f"{func.__name__} failed: {e}")
                return default_return
        return wrapper
    return decorator
```

---

## 🧪 Testing Strategy (Detailed)

### Coverage Goals
- **70% minimum** (recruiters check this)
- Unit tests: 70% | Integration tests: 20% | E2E: Skip

### 1. Preprocessing Invariants (Unit)
```python
# tests/unit/test_preprocessing.py
from src.data import TextPreprocessor

class TestPreprocessing:
    def test_lowercase_conversion(self):
        processor = TextPreprocessor()
        assert processor.transform("HELLO") == "hello"
    
    def test_handles_empty_input(self):
        processor = TextPreprocessor()
        assert processor.transform("") == ""
```

### 2. Model I/O Contracts (Unit)
```python
# tests/unit/test_model.py
def test_model_output_structure(mock_model):
    result = mock_model.predict("test query")
    assert "response" in result
    assert "sources" in result
    assert isinstance(result["sources"], list)
```

### 3. Prompt Testing (Snapshot)
Use `pytest-snapshot` to detect if your prompts change unexpectedly.

```python
# tests/unit/test_prompts.py
def test_prompt_generation(snapshot):
    from src.prompts import generate_rag_prompt
    prompt = generate_rag_prompt(query="AI", context="Context")
    # First run creates snapshot file. Future runs compare against it.
    snapshot.assert_match(prompt, "rag_prompt.txt")
```

---

## 🎯 Model Loading Best Practices

**Choose Pattern 1 for Portfolio (Simplest & Best).**

### Pattern 1: Lazy Loading (Recommended)
```python
# src/serving/model_cache.py
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_model(model_path: str = "models/latest.pkl"):
    """Load model once, cache in memory."""
    logger.info(f"Loading model from {model_path}...")
    # model = load_model(model_path) 
    # Return mock for demo
    return "LOADED_MODEL" 

# Usage in API
@app.post("/predict")
def predict(request: dict):
    model = get_model()  # Only loads once!
    return {"status": "success"}
```

---

## ⚡ Performance: Async Patterns

**When to use**: Multiple API calls (e.g., retrieving 5 documents, calling OpenAI).

```python
# src/utils/async_helpers.py
import asyncio

async def fetch_embedding(text: str):
    """Simulate Async IO."""
    await asyncio.sleep(0.1) # Non-blocking sleep
    return [0.1] * 768

async def batch_embed(texts: list[str]):
    """Embed in parallel."""
    # Run all at once, not one by one
    tasks = [fetch_embedding(t) for t in texts]
    return await asyncio.gather(*tasks)
```

---

## 🚀 Deployment (Standalone Guide)

### Level 1: Simple Dockerfile (Projects 1-3)
```dockerfile
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY . .
RUN uv sync --frozen
CMD ["uv", "run", "uvicorn", "src.serving.api:app", "--host", "0.0.0.0"]
```

### Level 2: Multi-Stage Docker (MLOps Project)
**Use this to impress.**

```dockerfile
# Build stage
FROM python:3.11-slim as builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Final stage
FROM python:3.11-slim
WORKDIR /app
# Copy virtualenv only
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
COPY models/ ./models/
# Add venv to path
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "src.serving.api:app", "--host", "0.0.0.0"]
```

---

## 💰 Cost Management

**Critical for Fine-tuning & RAG projects.**

```python
# src/utils/cost_tracker.py
import tiktoken

def estimate_cost(text: str, model: str = "gpt-4") -> float:
    tokens = len(tiktoken.encoding_for_model(model).encode(text))
    cost_per_1k = 0.03 # Check pricing
    return (tokens / 1000) * cost_per_1k
```

---

## 🐛 Debugging Guide

1.  **Isolate**: Don't run the whole pipeline. Test the failing function alone.
2.  **PDB**: `import pdb; pdb.set_trace()` pauses execution.
3.  **Logs**: Check `logs/app.log` if you set up logging.
4.  **Common Bugs**:
    *   **OOM**: Reduce batch size.
    *   **Rate Limit**: Use `tenacity` retry.
    *   **Import Error**: Run `python -m src.script` not `python src/script.py`.

---

## 🛠️ Automation (Progressive)

### Phase 1: Local (Weeks 1-2)
Use `uv run --script lint` manually.

### Phase 2: GitHub Actions (Week 3+)
**.github/workflows/ci.yml**
```yaml
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run pytest
```

---

## 🌿 Git Workflow

- **Branching**: Solo? Push to `main`. don't complicate it.
- **Commits**: `feat: add logging`, `fix: crash on empty input`.

---

**Version**: 3.0 (Diamond Edition)
**Last Updated**: Jan 2026
**Changes**: Full Standalone Configs, Detailed Tests, Async, Secrets, Model Loading.
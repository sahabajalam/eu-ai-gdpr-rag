# AIML Stack Decision Matrix (Diamond Edition)

**Strict guidance for Portfolio Projects vs Enterprise Realities.**

| Category | Scenario / Context | Recommended Stack | Banned / Alternative | Why? |
| :--- | :--- | :--- | :--- | :--- |
| **Package Manager** | **Portfolio / Solo** | **UV** | Poetry, Pip, Conda | `uv` is instant, zero-config, and handles Python installs. Don't waste time on others. |
| | **Enterprise Team** | **UV** or **Poetry** | Pip-tools | Teams might be locked into Poetry. That's fine. Avoid Conda unless forced by niche libraries. |
| **Configuration** | **Application (RAG, API)** | **Pydantic** | Yaml, JSON, Dicts | Strong typing prevents runtime errors. Pydantic is the industry standard for apps. |
| | **MLOps / Experiments** | **Hydra** | Argparse | Hydra allows complex overrides `model.layers=4` and sweeps for training runs. |
| **Testing** | **Logic & Math** | **Pytest** | Unittest | Fixtures are cleaner than classes. 70% coverage is the goal. |
| | **Prompts / LLMs** | **Snapshot Testing** | "Eye-balling it" | LLMs output text. Use `pytest-snapshot` to detect when "Hello" becomes "Hi there". |
| **CI/CD** | **Portfolio (Week 1-2)** | **Local Hooks (Pre-commit)** | GitHub Actions | Don't build CI until you have tests. It slows you down. |
| | **Portfolio (Week 3+)** | **GitHub Actions** | Jenkins, GitLab | Recruiters look for the "Green Checkmark" on GitHub. Mandatory for 'Senior' tag. |
| **Containerization** | **Basic App** | **Simple Dockerfile** | Multi-stage | Keep it simple. Get it running. |
| | **Production / MLOps** | **Multi-Stage Docker** | VM / Bare Metal | Optimize image size (~200MB) to show you know "Production Engineering". |
| **Secrets** | **Local Dev** | **.env + Pydantic** | Hardcoding | Never commit secrets. Use `pydantic-settings` to load `.env` safely. |
| **Data Tracking** | **Large Files (>100MB)** | **DVC** | Git LFS | Git is for code. DVC is for data. Push data to S3/Drive, not GitHub. |
| **Model Loading** | **Inference API** | **Lazy Loading (@lru_cache)** | Global Variables | Globals cause race conditions. Lazy loading is safe and efficient. |
| **Async** | **I/O Bound (APIs/DB)** | **Asyncio** | Threads | When calling OpenAI/VectorDB, use `await` to handle 10x more requests. |

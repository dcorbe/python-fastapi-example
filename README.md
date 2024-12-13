# Bridge Security Solutions Backend
This is the Bridge Security Solutions backend.  

This is primarily a
[FastAPI](https://github.com/fastapi/fastapi)
application that does the following:

- Implements API endpoits.
- Serves media streams for video players
- Ingests video streams from cameras and live feeds.

## Table of Contents
- [Setting Up A Development Environment (MacOS)](#setting-up-a-development-environment-macos)
- [To Do List](#to-do)

## To Do:
- [Rebuild Rust Backend in Python (CAD-6)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-6)
- [Ingest API endpoint (CAD-15)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-15)
- [Motion Detection (CAD-16)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-16)
- [Video Playback API (CAD-17)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-17)
- [Implement Refresh Tokens (CAD-22)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-22)
- [User Management API (CAD-24)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-24)
- [Group Management API (CAD-25)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-25)
- 

## Setting Up A Development Environment (MacOS)
1. Install Python 3.12:
```bash
brew install python@3.12
```

2. Install Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3.12 -
```

3. When working in this environment, always use the poetry shell:
```bash
export PATH="$HOME/.local/bin:$PATH"
poetry shell
```

4. Install pre-commit:
```bash
pip install pre-commit
```

5. Install dependencies:
```bash
poetry install
```

6. Install pre-commit hooks:
```bash
pre-commit install
```

## Type Checking

The project uses mypy for static type checking. Type checking is enforced through:
- Pre-commit hooks (runs on git commit)

To run type checking manually:
```bash
poetry run mypy .
```

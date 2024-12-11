# Bridge Security Solutions Backend

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

4. Install dependencies:
```bash
poetry install
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Type Checking

The project uses mypy for static type checking. Type checking is enforced through:
- Pre-commit hooks (runs on git commit)
- GitHub Actions (runs on push to main and pull requests)

To run type checking manually:
```bash
poetry run mypy .
```

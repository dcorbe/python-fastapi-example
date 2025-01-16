# FastAPI example application
This is primarily a
[FastAPI](https://github.com/fastapi/fastapi) which is intended to be used as a teaching tool and reference for building 
web APIs with Python.


## Table of Contents
- [Core Dependencies](#core-dependencies)
- [Setting Up A Development Environment](#setting-up-a-development-environment)
- [Database Setup](#database-setup)
- [Running the FastAPI Server](#running-the-fastapi-server)
- [Type Checking](#type-checking)
- [To Do List](#to-do)

## Core Dependencies

### Web Framework and API
- [**FastAPI**](https://fastapi.tiangolo.com/) - Modern web framework for building APIs
- [**Pydantic**](https://docs.pydantic.dev/) - Data validation using Python type annotations
- [**email-validator**](https://github.com/JoshData/python-email-validator) - Email validation for Pydantic models

### Authentication and Security
- [**PyJWT**](https://pyjwt.readthedocs.io/) - JSON Web Token implementation [with crypto]
- [**Passlib**](https://passlib.readthedocs.io/) - Password hashing library [with bcrypt]

### Database
- [**SQLAlchemy**](https://www.sqlalchemy.org/) - PostgreSQL adapter for Python

### Computer Vision and Data Processing
- [**OpenCV**](https://opencv.org/) - Computer vision and video processing
- [**NumPy**](https://numpy.org/) - Numerical processing and array operations

### Development Tools
- [**mypy**](https://mypy-lang.org/) - Static type checker
- [**pre-commit**](https://pre-commit.com/) - Git hooks framework
- [**PyYAML**](https://pyyaml.org/) - YAML parsing and writing

## Setting Up A Development Environment
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

## Database Setup

1. Configure environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your desired database credentials
```

2. Start the PostgreSQL database:
```bash
# Start PostgreSQL using Docker Compose
docker-compose up -d postgres

# Wait for the health check to pass
docker-compose ps
```

3. Initialize your first user:
```bash
# Inside poetry shell
python tools/adduser.py admin@example.com your_secure_password
```

This will create your initial user with the specified email and password. You can use these credentials to authenticate with the API.

## Running the FastAPI Server

1. Start the FastAPI server:

   Development mode (with auto-reload):
   ```bash
   # Inside poetry shell
   fastapi dev main:app
   ```

2. Verify the setup:
   ```bash
   # Test the login endpoint with your created user
   export TOKEN=$(http -f POST http://localhost:8000/auth/login username=email@address password=password | jq -r .access_token)
   echo ${TOKEN}
   ```

## Type Checking

The project uses mypy for static type checking. Type checking is enforced through:
- Pre-commit hooks (runs on git commit)

To run type checking manually:
```bash
poetry run mypy .
```

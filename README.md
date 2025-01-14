# Bridge Security Solutions Backend
This is the Bridge Security Solutions backend.  

This is primarily a
[FastAPI](https://github.com/fastapi/fastapi)
application that does the following:

- Implements API endpoints
- Serves media streams for video players
- Ingests video streams from cameras and live feeds

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
- [**psycopg**](https://www.psycopg.org/psycopg3/) - PostgreSQL adapter for Python

### Computer Vision and Data Processing
- [**OpenCV**](https://opencv.org/) - Computer vision and video processing
- [**NumPy**](https://numpy.org/) - Numerical processing and array operations
- [**bss-lib**](https://github.com/Bridge-Security-Solutions/bss-lib) - Internal library for shared functionality

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
# At minimum, set these variables:
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=bss_dev
DATABASE_URL=postgres://your_username:your_secure_password@localhost:5432/bss_dev
JWT_SECRET=your_secure_jwt_secret
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
   fastapi main.py
   ```

2. Verify the setup:
   ```bash
   # Test the login endpoint with your created user
   export TOKEN=$(http -f POST http://localhost:8000/auth/login username=daniel@corbe.net password=cgpe845Z | jq -r .access_token)
   echo ${TOKEN}
   ```

## Type Checking

The project uses mypy for static type checking. Type checking is enforced through:
- Pre-commit hooks (runs on git commit)

To run type checking manually:
```bash
poetry run mypy .
```

## To Do:
- ~~[Rebuild Rust Backend in Python (CAD-6)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-6)~~
- [Ingest API endpoint (CAD-15)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-15)
- [Motion Detection (CAD-16)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-16)
- [Video Playback API (CAD-17)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-17)
- [Implement Refresh Tokens (CAD-22)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-22)
- [User Management API (CAD-24)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-24)
- [Group Management API (CAD-25)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-25)
- [User management (CAD-24)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-24)
- [Group management (CAD-26)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-26)
- [Org management (CAD-27)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-27)
- [Admin API (CAD-28)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-28)
- [Camera API (CAD-32)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-32)
- [Camera Logging/Audit (CAD-33)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-33)
- [Dockerize Backend (CAD-37)](https://bridgesecuritysolutions.atlassian.net/browse/CAD-37)

# FastAPI Demo
This is primarily a
[FastAPI](https://github.com/fastapi/fastapi) application which is intended to be used as a learning tool and as a 
reference for building API servers with Python.  On top of FastAPI, this project also provides a number of additional
features:

* Automatic handling of oauth2 and API tokens
* Built-in telemetry
* Built-in muti-tenant user management
* A simple but powerful permissions system
* A crash reporting system

## Table of Contents
- [Usage](#usage)
- [Core Dependencies](#core-dependencies)
- [Setting Up A Development Environment (Mac OS)](#setting-up-a-development-environment)
- [Setting Up A Development Environment (Linux)](#setting-up-a-development-environment)
- [Database Setup](#database-setup)
- [Running the FastAPI Server](#running-the-fastapi-server)
- [OpenAPI Debug Console](#openapi-debug-console)
- [Type Checking](#type-checking)

## Usage
### Hello World

### Examples
See the [examples](./examples) directory for a collection of example endpoints that demonstrate various features of 
FastAPI.

### Documentation
Coming Soon!

## Core Dependencies

### Web Framework and API
- [**FastAPI**](https://fastapi.tiangolo.com/) - Modern web framework for building APIs
- [**Pydantic**](https://docs.pydantic.dev/) - Data validation using Python type annotations
- [**OpenTelemetry**](https://opentelemetry.io/) - Observability framework for telemetry and distributed tracing
- [**email-validator**](https://github.com/JoshData/python-email-validator) - Email validation for Pydantic models

### Authentication and Security
- [**PyJWT**](https://pyjwt.readthedocs.io/) - JSON Web Token implementation [with crypto]

### Infrastructure and Database
- [**PostgreSQL**](https://www.postgresql.org/) - Open-source relational database
- [**Redis**](https://redis.io/) - In-memory data structure store
- [**SQLAlchemy**](https://www.sqlalchemy.org/) - FastAPI-compatible integration for database models
- [**Alembic**](https://alembic.sqlalchemy.org/) - Database migrations

### Development Tools
- [**Docker**](https://www.docker.com/) - Containerization
- [**mypy**](https://mypy-lang.org/) - Static type checker
- [**pre-commit**](https://pre-commit.com/) - Git hooks framework
- [**Black**](https://black.readthedocs.io/) - Code formatter
- [**Flake8**](https://flake8.pycqa.org/) - Code linter


## Setting Up A Development Environment (Mac OS)
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

## Setting Up A Development Environment (Linux)

## Database Setup

1. Configure environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your desired database credentials
```

2. Start the PostgreSQL database:
```bash
# Start Postgre and Redis
docker-compose up

# Wait for the health check to pass
docker-compose ps
```

3. Run database migrations (for the first time:
```bash
# Inside poetry shell
alembic upgrade head
```
   This will create all necessary database tables and initialize the database schema.

4. Initialize your first user:
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

## OpenAPI Debug Console
FastAPI automatically generates interactive API documentation using OpenAPI (formerly known as Swagger). The debug 
console provides a convenient way to explore and test API endpoints.

To access the OpenAPI debug console:

1. Start the FastAPI server (if not already running)
2. Open your web browser and navigate to:
   - Swagger UI: http://localhost:8000/docs
   - Alternative ReDoc UI: http://localhost:8000/redoc

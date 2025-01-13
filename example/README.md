# Example Endpoints

This module demonstrates different types of FastAPI endpoints and common patterns.

## Available Endpoints

### 1. Hello World (`/example/hello`)
A protected endpoint that requires authentication. Returns a message and the user's ID.
```json
{
    "message": "This is a protected endpoint",
    "user_id": "150840fe-9251-4a8e-8fd0-ac6b9a6656f2"
}
```

### 2. Ping (`/example/ping`)
A simple unprotected endpoint that returns a ping response.
```json
{
    "ping": "pong"
}
```

### 3. Error Example (`/example/error`)
Demonstrates proper error handling by returning a 403 status code.

## Implementation Examples

Each endpoint demonstrates different FastAPI and Pydantic features:

1. `hello.py` - Shows:
   - Protected routes using Depends(get_current_user)
   - Pydantic models with UUID fields
   - Type hinting and docstrings

2. `ping.py` - Shows:
   - Simple Pydantic model
   - Unprotected endpoint
   - Basic response handling

3. `error.py` - Shows:
   - HTTP exception handling
   - Custom error messages
   - Status code usage

## Testing with HTTPie

### Protected Endpoint (hello)
```bash
# First get a token
export TOKEN=$(http -f POST http://localhost:8000/auth/login \
    username=email@address \
    password=password | jq -r .access_token)

# Then access the endpoint
http http://localhost:8000/example/hello \
    "Authorization: Bearer ${TOKEN}"
```

### Unprotected Endpoint (ping)
```bash
http http://localhost:8000/example/ping
```

### Error Example
```bash
http http://localhost:8000/example/error
```

## Common Issues

1. 401 Unauthorized: Your token has expired. Get a new one using the login command.
2. 403 Forbidden: The error endpoint always returns this by design.
3. 404 Not Found: Ensure the server has been restarted after any code changes.
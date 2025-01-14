# Example Endpoints

This module demonstrates common patterns and best practices for implementing FastAPI endpoints in the Bridge Security Solutions backend.

## Available Endpoints

### 1. Hello World (`/example/hello`)
A protected endpoint that requires authentication. Returns a greeting message and the authenticated user's ID.
```json
{
    "message": "This is a protected endpoint",
    "user_id": "150840fe-9251-4a8e-8fd0-ac6b9a6656f2"
}
```

### 2. Ping (`/example/ping`)
A simple unprotected endpoint that returns a ping response. Useful for health checks and basic connectivity testing.
```json
{
    "ping": "pong"
}
```

### 3. Error Example (`/example/error`)
Demonstrates proper error handling by returning a 403 Forbidden response. Shows how to use FastAPI's HTTPException.
```json
{
    "detail": "You are not authorized to access this resource"
}
```

### 4. Echo (`/example/echo`)
A protected endpoint that echoes back the request details. Useful for debugging and demonstrating request handling.
```json
{
    "headers": {
        "authorization": "Bearer <token>",
        "content-type": "application/json",
        ...
    },
    "method": "POST",
    "url": "http://localhost:8000/example/echo",
    "body": "your request body here"
}
```

### 5. Books CRUD (`/example/books`)
A complete CRUD service demonstration using FastAPI, SQLAlchemy, and Pydantic. Shows proper database integration and REST API patterns.

#### Create a Book (POST `/example/books`)
```json
{
    "title": "Example Book",
    "author": "John Doe",
    "description": "Optional book description"
}
```

#### Get a Book (GET `/example/books/{book_id}`)
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Example Book",
    "author": "John Doe",
    "description": "Optional book description",
    "created_at": "2024-01-14T12:00:00"
}
```

#### List Books (GET `/example/books`)
```json
[
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Example Book 1",
        "author": "John Doe",
        "created_at": "2024-01-14T12:00:00"
    },
    {
        "id": "650e8400-e29b-41d4-a716-446655440000",
        "title": "Example Book 2",
        "author": "Jane Doe",
        "created_at": "2024-01-14T12:30:00"
    }
]
```

## Implementation Patterns

Each endpoint demonstrates different FastAPI features and best practices:

1. `hello.py` - Protected Routes and User Authentication
   - Using `Depends(get_current_user)` for authentication
   - Pydantic models with UUID fields
   - Type hints and comprehensive docstrings
   - Response model validation

2. `ping.py` - Basic Endpoint Structure
   - Simple Pydantic response models
   - Unprotected endpoint implementation
   - Basic response handling
   - Function documentation

3. `error.py` - Error Handling
   - HTTP exception handling with proper status codes
   - Custom error messages
   - Response model for errors
   - Exception documentation

4. `echo.py` - Request Processing
   - Request body and header handling
   - Protected route with user authentication
   - Async request processing
   - JSONResponse usage

5. `books.py` - Complete CRUD Service
   - SQLAlchemy integration with async session handling
   - Pydantic models for request/response validation
   - Proper error handling with database operations
   - Type hints and dependency injection
   - REST API best practices
   - Transaction management and rollbacks

## Testing Examples

### Protected Endpoints (hello, echo, books)
```bash
# Get an authentication token
export TOKEN=$(http -f POST http://localhost:8000/auth/login \
    username=email@address \
    password=password | jq -r .access_token)

# Access hello endpoint
http http://localhost:8000/example/hello \
    "Authorization: Bearer ${TOKEN}"

# Test echo endpoint
http POST http://localhost:8000/example/echo \
    "Authorization: Bearer ${TOKEN}" \
    message="test message"

# Create a book
http POST http://localhost:8000/example/books \
    "Authorization: Bearer ${TOKEN}" \
    title="New Book" \
    author="Author Name" \
    description="Book description"

# Get all books
http GET http://localhost:8000/example/books \
    "Authorization: Bearer ${TOKEN}"

# Get specific book
http GET http://localhost:8000/example/books/{book_id} \
    "Authorization: Bearer ${TOKEN}"

# Update a book
http PUT http://localhost:8000/example/books/{book_id} \
    "Authorization: Bearer ${TOKEN}" \
    title="Updated Title" \
    author="Updated Author" \
    description="Updated description"

# Delete a book
http DELETE http://localhost:8000/example/books/{book_id} \
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

## Common Issues and Solutions

1. Authentication Issues (401 Unauthorized)
   - Token has expired → Get a new token using the login endpoint
   - Missing token → Include Authorization header with Bearer token
   - Invalid token → Ensure token format is correct

2. Permission Issues (403 Forbidden)
   - Error endpoint returns this by design
   - Check user roles and permissions for protected endpoints

3. Request Issues (404 Not Found)
   - Verify server is running
   - Check endpoint URL is correct
   - Ensure server has been restarted after code changes

4. Request Body Issues (422 Unprocessable Entity)
   - Verify request body matches expected schema
   - Check content-type header is set correctly
   - Ensure all required fields are provided

5. Database Issues (400 Bad Request)
   - Check for duplicate entries when creating/updating books
   - Ensure all required fields are provided
   - Verify UUID format for book IDs

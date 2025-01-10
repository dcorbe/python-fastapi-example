# Example Protected Endpoint

This module demonstrates how to implement and use protected endpoints in the BSS backend.

## Testing with HTTPie

### 1. Get an Authentication Token

First, get a token by logging in. Store it in an environment variable for convenience:

```bash
export TOKEN=$(http -f POST http://localhost:8000/auth/login \
    username=email@address \
    password=password | jq -r .access_token)
```

This command:
- Uses HTTPie's form mode (-f)
- POSTs to the login endpoint
- Extracts just the access_token using jq
- Stores it in the TOKEN environment variable

### 2. Access the Protected Endpoint

Once you have a token, you can access the protected endpoint:

```bash
http http://localhost:8000/example/protected \
    "Authorization: Bearer ${TOKEN}"
```

### Expected Response

If successful, you'll receive a JSON response containing:
- A message string
- Your user_id (UUID)

Example:
```json
{
    "message": "This is a protected endpoint",
    "user_id": "150840fe-9251-4a8e-8fd0-ac6b9a6656f2"
}
```

### Common Issues

1. If you receive a 401 Unauthorized error, your token might have expired. Get a new one using the login command.
2. If you receive a 404 Not Found error, make sure the server has been restarted after installing the example module.

## Implementation Details

The endpoint demonstrates:
- FastAPI dependency injection for auth
- Pydantic models for request/response validation
- JWT token authentication
- UUID handling

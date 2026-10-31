# API Reference

## Authentication

The API uses Bearer token authentication. Include your API key in the `Authorization` header:

```
Authorization: Bearer <api_key>
```

## Endpoints

### GET /v1/users

Retrieves a list of all users in the system.

**Query Parameters:**
- `page` (integer): Page number for pagination (default: 1)
- `limit` (integer): Number of items per page (default: 20)

**Response:**
```json
{
  "users": [
    {
      "id": "user_123",
      "email": "john@example.com",
      "role": "admin"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20
}
```

### POST /v1/users

Creates a new user account.

**Request Body:**
```json
{
  "email": "jane@example.com",
  "password": "secure-password",
  "role": "user"
}
```

**Response:**
```json
{
  "id": "user_456",
  "email": "jane@example.com",
  "role": "user",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /v1/users/{user_id}

Retrieves a single user by ID.

**Path Parameters:**
- `user_id` (string): The unique identifier of the user

**Response:**
```json
{
  "id": "user_123",
  "email": "john@example.com",
  "role": "admin"
}
```

## Configuration

The API reads configuration from environment variables:
- `API_HOST`: Host to bind to (default: 0.0.0.0)
- `API_PORT`: Port to listen on (default: 8000)
- `API_WORKERS`: Number of worker processes (default: 4)

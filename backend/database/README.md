# Database Technical Documentation

## Authentication System Architecture

The authentication system is built using FastAPI for the backend and SQLite for the database. Here's a detailed technical overview:

## Database Structure
We use SQLite to store user data and activity logs in two main tables:

1. **Users Table**:
   - `user_id`: Unique identifier for each user (PRIMARY KEY AUTOINCREMENT)
   - `username`: Unique username (UNIQUE NOT NULL)
   - `password_hashed`: SHA-256 hashed password (NOT NULL)
   - `registration_date`: Timestamp of user registration (DEFAULT CURRENT_TIMESTAMP)

2. **Activity Logs Table**:
   - `log_id`: Unique identifier for each activity (PRIMARY KEY AUTOINCREMENT)
   - `user_id`: References the user who performed the action (FOREIGN KEY)
   - `action`: Type of action (e.g., login, registration) (NOT NULL)
   - `timestamp`: When the action occurred (DEFAULT CURRENT_TIMESTAMP)

## API Endpoints

The FastAPI backend provides the following authentication endpoints:

```bash
POST /auth/register
- Register a new user
- Body: {"username": string, "password": string}
- Returns: {"success": bool, "message": string}

POST /auth/login
- Authenticate a user
- Body: {"username": string, "password": string}
- Returns: {"access_token": string, "token_type": string}

GET /auth/me
- Get current user info (requires authentication)
- Headers: {"Authorization": "Bearer {token}"}
- Returns: {"username": string, "user_id": int}
```

## Database Setup

The SQLite database is automatically initialized when you first run the application. It creates:

1. The authentication database at `backend/database/auth.db`
2. Required tables (users and activity_logs)
3. Indexes for optimal query performance

## Frontend-Backend Integration

1. The Streamlit frontend (`frontend/app.py`) communicates with the FastAPI backend through HTTP requests
2. Authentication state is managed using Streamlit's session state
3. JWT tokens are stored securely and included in API requests
4. Activity logs track user interactions for security monitoring

## Security Best Practices

1. Passwords are never stored in plain text
2. All database queries are parameterized to prevent SQL injection
3. Activity logging helps detect suspicious behavior
4. Token-based authentication ensures secure API access

## Database Files
- `auth_db.py`: Main database interface class
- `auth.db`: SQLite database file

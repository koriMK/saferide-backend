# SafeRide Backend

A complete Flask-based ride-sharing backend with JWT authentication, M-Pesa integration, and comprehensive API endpoints.

## Features

- User authentication (JWT)
- Driver registration and management
- Trip booking and management
- M-Pesa payment integration
- Admin dashboard
- RESTful API design

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python3 app.py
```

3. Access the API at: http://localhost:5002

## API Endpoints

- `/api/v1/health` - Health check
- `/api/v1/auth/*` - Authentication
- `/api/v1/users/*` - User management
- `/api/v1/drivers/*` - Driver operations
- `/api/v1/trips/*` - Trip management
- `/api/v1/payments/*` - Payment processing
- `/api/v1/admin/*` - Admin dashboard

## Database

Uses SQLite by default. Database file: `safedrive.db`

## Environment Variables

- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT secret key
- `DATABASE_URL` - Database connection string
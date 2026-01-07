# Aviator Analytics Pro

A professional analytics platform for the Aviator game, providing statistical analysis, pattern detection, and real-time alerts.

## Features

- User registration and authentication with JWT
- Subscription management via Mercado Pago
- Real-time aviator game analytics
- Statistical analysis and pattern detection
- Email notifications via Resend
- RESTful API built with FastAPI

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLite/SQLModel** - Async database with SQLAlchemy ORM
- **JWT** - Authentication tokens
- **Bcrypt** - Password hashing
- **Mercado Pago SDK** - Payment processing
- **Resend** - Email service

### Frontend
- React application (see `frontend/` directory)

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/lordizinn/site.git
cd site
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

4. Configure environment variables:
```bash
cd backend
cp .env.example .env
# Edit .env with your configuration
```

5. Run the backend server:
```bash
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## Environment Variables

The following environment variables are required:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./data/app.db` |
| `JWT_SECRET` | Secret key for JWT token signing | **Must be changed in production** |
| `MERCADO_PAGO_ACCESS_TOKEN` | Mercado Pago API access token | - |
| `MERCADO_PAGO_WEBHOOK_SECRET` | Webhook signature verification secret | - |
| `RESEND_API_KEY` | Resend email service API key | - |
| `SENDER_EMAIL` | Email address for sending notifications | `onboarding@resend.dev` |
| `FRONTEND_URL` | URL of the frontend application | `http://localhost:3000` |
| `CORS_ORIGINS` | Comma-separated list of allowed CORS origins | `*` |

### Database Configuration

By default, the application uses SQLite with `sqlite+aiosqlite:///./data/app.db`. 

**Important Notes:**
- SQLite data is stored locally in the `data/` directory
- On Render's free tier, the filesystem is ephemeral - data will be lost on restart
- For production with persistent data, use an external database (e.g., PostgreSQL):
  ```
  DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
  ```

## Deployment on Render

### Option 1: Using render.yaml (Blueprint)

1. Fork or push this repository to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click "New" → "Blueprint"
4. Connect your GitHub repository
5. Render will automatically detect `render.yaml` and create the service
6. Configure the required environment variables in the Render dashboard:
   - `JWT_SECRET` - Generate a secure random string
   - `MERCADO_PAGO_ACCESS_TOKEN` - Your Mercado Pago access token
   - `RESEND_API_KEY` - Your Resend API key
   - `FRONTEND_URL` - Your frontend URL
   - `CORS_ORIGINS` - Allowed origins (e.g., your frontend domain)

### Option 2: Manual Setup

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name:** aviator-analytics-api
   - **Runtime:** Python
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn backend.server:app --host 0.0.0.0 --port 10000`
   - **Plan:** Free (or your preferred plan)
5. Add environment variables (see table above)
6. Click "Create Web Service"

### Important Render Configuration

- **Port:** The application runs on port 10000 (Render's default)
- **Health Check:** Optional - can use `/api/dashboard/stats` (requires auth) or create a dedicated health endpoint
- **Auto-Deploy:** Enable to automatically deploy on git push

### Post-Deployment

After deployment:
1. Note your Render service URL (e.g., `https://aviator-analytics-api.onrender.com`)
2. Update `FRONTEND_URL` in environment variables if deploying frontend separately
3. Configure Mercado Pago webhook URL to point to: `https://your-service.onrender.com/api/webhooks/mercado-pago`

## API Documentation

Once running, visit:
- API docs (Swagger): `http://localhost:8000/docs`
- Alternative docs (ReDoc): `http://localhost:8000/redoc`

### Main Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/subscription/create-preference` - Create Mercado Pago subscription
- `POST /api/webhooks/mercado-pago` - Mercado Pago webhook handler
- `GET /api/dashboard/stats` - Get dashboard statistics (requires auth)
- `GET /api/aviator/history` - Get aviator game history (requires auth)
- `GET /api/alerts/recent` - Get recent alerts (requires auth)

## Development

### Project Structure

```
.
├── backend/
│   ├── server.py           # Main FastAPI application
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example       # Environment variables template
│   └── data/              # SQLite database (created automatically)
├── frontend/              # React frontend application
├── render.yaml           # Render deployment configuration
└── README.md            # This file
```

### Testing Locally

1. Start the backend server
2. Use the Swagger UI at `http://localhost:8000/docs` to test endpoints
3. For testing payments, mock mode is enabled when `MERCADO_PAGO_ACCESS_TOKEN` is not set

## License

This project is private and proprietary.

## Support

For issues or questions, please contact the development team.

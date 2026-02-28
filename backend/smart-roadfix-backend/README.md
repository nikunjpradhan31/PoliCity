# Smart RoadFix Backend

Production-ready FastAPI backend for municipal pothole optimization platform.

## Features

- **Auth0 JWT Authentication** - RS256 verification using python-jose
- **MongoDB Integration** - Async database operations using Motor
- **Open311 API Integration** - Fetch pothole data from external APIs
- **Budget Management** - Upload and manage budgets via CSV
- **Optimization Engine** - Select potholes for repair based on budget constraints
- **Report Generation** - Generate optimization reports

## Prerequisites

- Python 3.11+
- MongoDB (local or cloud instance)
- Auth0 account (for authentication)

## Quick Start

### 1. Clone and Setup

```bash
cd smart-roadfix-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=smart_roadfix

# Auth0 (required for protected endpoints)
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://api.smartroadfix.com

# Open311 (optional)
OPEN311_BASE_URL=https://api.open311.org
OPEN311_SERVICE_CODE=POTHOLE
```

### 3. Start MongoDB

Using Docker:
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

Or use a local MongoDB installation.

### 4. Run the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Access the API

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

### Potholes
- `GET /api/v1/potholes/sync?city=<city>` - Sync from Open311
- `GET /api/v1/potholes` - Get stored potholes
- `GET /api/v1/potholes/{id}` - Get pothole by ID
- `POST /api/v1/potholes` - Create pothole
- `PATCH /api/v1/potholes/{id}` - Update pothole
- `DELETE /api/v1/potholes/{id}` - Delete pothole

### Budgets
- `GET /api/v1/budget` - Get budgets
- `GET /api/v1/budget/{id}` - Get budget by ID
- `POST /api/v1/budget` - Create budget (requires auth)
- `POST /api/v1/budget/upload-csv` - Upload budget from CSV (requires auth)
- `PATCH /api/v1/budget/{id}` - Update budget (requires auth)
- `DELETE /api/v1/budget/{id}` - Delete budget (requires auth)

### Optimization
- `POST /api/v1/optimize?budget=<amount>&strategy=<strategy>&city=<city>` - Run optimization (requires auth)
- `GET /api/v1/optimize/history` - Get optimization history

### Reports
- `GET /api/v1/report/{run_id}` - Get report by run ID (requires auth)
- `GET /api/v1/report/{run_id}/download` - Download report (requires auth)
- `GET /api/v1/report` - Get all reports (requires auth)

## CSV Budget Upload Format

```csv
category,amount,description
Road Repair,50000,Annual road maintenance
Pothole Fixing,25000,Priority pothole repairs
Emergency Response,10000,Emergency repairs
```

## Project Structure

```
smart-roadfix-backend/
├── app/
│   ├── main.py              # Application entry point
│   ├── api/
│   │   ├── deps.py          # Dependency injection
│   │   └── routes/          # API route handlers
│   ├── core/
│   │   ├── config.py        # Configuration management
│   │   ├── database.py      # MongoDB connection
│   │   ├── security.py      # Auth0 JWT verification
│   │   ├── middleware.py    # CORS and logging middleware
│   │   └── logging.py       # Logging configuration
│   ├── models/             # Pydantic models
│   ├── services/           # Business logic
│   └── utils/              # Utility functions
├── .env.example            # Environment variables template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Lint with ruff
ruff check app/

# Format with ruff
ruff format app/
```

## Authentication

Protected endpoints require a valid Auth0 JWT token. Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer <your_token>" http://localhost:8000/api/v1/budget
```

## License

MIT License

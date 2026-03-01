# PoliCity - Municipal Infrastructure Intelligence Platform

An AI-powered platform for analyzing, reporting, and optimizing municipal infrastructure repairs. PoliCity leverages multi-agent AI systems to provide comprehensive infrastructure analysis including cost estimates, contractor discovery, budget analysis, and grant opportunities.

## Overview

PoliCity is a full-stack application that enables municipalities to:

- **Report infrastructure issues** (potholes, streetlight outages, graffiti, sidewalk damage, traffic signal issues)
- **Generate AI-powered analysis** including repair cost estimates, phased repair plans, and feasibility assessments
- **Discover licensed contractors** in the area with verified credentials
- **Analyze municipal budgets** and identify funding sources
- **Find applicable grants** from federal, state, and local programs
- **Generate professional reports** in multiple formats (JSON, Markdown, PDF)

## Architecture

```
PoliCity/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── agents/            # AI agents (Thinking Agent, Report Generator)
│   │   ├── services/          # External integrations (scraping, geocoding, etc.)
│   │   ├── workflows/         # Pipeline orchestration
│   │   ├── routes.py          # API endpoints
│   │   ├── models.py          # Pydantic models
│   │   ├── gemini_client.py   # Gemini AI integration
│   │   └── main.py            # Application entry point
│   └── requirements.txt
├── frontend/policity/          # React frontend
│   ├── src/
│   │   ├── pages/             # Application pages
│   │   ├── components/        # Reusable components
│   │   └── assets/            # Static assets
│   └── package.json
└── README.md
```

## Features

### Backend Features

- **Multi-Agent AI Pipeline**: Two-agent system powered by Gemini LLM
  - **Thinking Agent**: Gathers data, analyzes costs, discovers contractors, checks budgets
  - **Report Generator**: Synthesizes findings into structured reports
- **MongoDB Persistence**: Caches agent outputs for partial re-runs and recovery
- **Open311 Integration**: Syncs with city 311 systems for issue data
- **Budget Management**: Upload and manage municipal budgets via CSV
- **Optimization Engine**: Selects repairs based on budget constraints
- **PDF Report Generation**: Creates downloadable reports

### Frontend Features

- **City Search**: Find infrastructure data by city
- **Interactive Map**: Visualize infrastructure issues on a map
- **Download Center**: Access generated reports
- **Responsive Design**: Works on desktop and mobile

## Tech Stack

### Backend

- **Framework**: FastAPI (Python 3.11+)
- **AI**: Google Gemini API
- **Database**: MongoDB (with Motor async driver)
- **Authentication**: Auth0 JWT
- **External APIs**: Open311, City Open Data portals

### Frontend

- **Framework**: React 18
- **Routing**: React Router
- **Maps**: Leaflet.js
- **Styling**: CSS

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (local or cloud)
- Google Gemini API key

## Quick Start

### 1. Clone and Setup

```bash
cd PoliCity
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=smart_roadfix

# Auth0 (optional for development)
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://api.policity.com

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Open311 (optional)
OPEN311_BASE_URL=https://api.open311.org
OPEN311_SERVICE_CODE=POTHOLE
```

### 4. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access API docs at: http://localhost:8000/docs

### 5. Frontend Setup

```bash
cd frontend/policity
npm install
npm start
```

Access the app at: http://localhost:3000

## API Endpoints

### Health Check

- `GET /api/v1/health` - Health check
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

### Infrastructure Reports

- `POST /api/v1/workflow/infrastructure-report` - Generate infrastructure report

**Request Example:**
```json
{
  "issue_type": "pothole",
  "location": "Chicago, IL",
  "fiscal_year": 2025,
  "image_url": "https://example.com/pothole.jpg"
}
```

### Potholes

- `GET /api/v1/potholes/sync?city=<city>` - Sync from Open311
- `GET /api/v1/potholes` - Get stored potholes
- `POST /api/v1/potholes` - Create pothole
- `PATCH /api/v1/potholes/{id}` - Update pothole
- `DELETE /api/v1/potholes/{id}` - Delete pothole

### Budgets

- `GET /api/v1/budget` - Get budgets
- `POST /api/v1/budget/upload-csv` - Upload budget from CSV

### Optimization

- `POST /api/v1/optimize?budget=<amount>&strategy=<strategy>&city=<city>` - Run optimization

### Reports

- `GET /api/v1/report/{run_id}` - Get report by run ID
- `GET /api/v1/report/{run_id}/download` - Download report

## AI Agent Workflow

The multi-agent system works as follows:

1. **User Input**: Submit issue type, location, fiscal year, optional image
2. **Thinking Agent**:
   - Parses and analyzes the issue
   - Geocodes the location
   - Researches material and labor costs
   - Generates a phased repair plan
   - Discovers and verifies local contractors
   - Analyzes municipal budget data
   - Identifies applicable grants
3. **Report Generator**:
   - Synthesizes all findings
   - Generates executive summary
   - Creates structured report with source reliability
   - Supports export to JSON, Markdown, PDF

The system caches results in MongoDB, enabling partial re-runs and recovery from interruptions.


## Documentation

- [Backend README](backend/README.md) - Detailed backend documentation
- [Multi-Agent Workflow](multi_agent_infrastructure_workflow.md) - AI agent specifications
- [Integration Plan](plans/integration_plan.md) - Implementation roadmap

## License

MIT License

## Project Structure

```
PoliCity/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── base.py           # Base agent class
│   │   │   ├── thinking.py       # Thinking agent implementation
│   │   │   ├── report_gen.py     # Report generator agent
│   │   │   ├── multi_thinking.py
│   │   │   ├── multi_report_gen.py
│   │   │   └── graph.py
│   │   ├── services/
│   │   │   ├── mongo.py          # MongoDB async client
│   │   │   ├── pdfcreator.py     # PDF generation
│   │   │   ├── web_scraper.py
│   │   │   ├── geocoder.py
│   │   │   ├── license_verify.py
│   │   │   ├── grant_search.py
│   │   │   ├── open_data.py
│   │   │   └── cache.py
│   │   ├── workflows/
│   │   │   ├── infrastructure.py      # Single-agent workflow
│   │   │   └── multi_infrastructure.py # Multi-agent workflow
│   │   ├── main.py
│   │   ├── routes.py
│   │   ├── models.py
│   │   ├── gemini_client.py
│   │   └── db.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/policity/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.js
│   │   │   ├── CityMap.js
│   │   │   ├── Loading.js
│   │   │   └── Download.js
│   │   ├── components/
│   │   │   └── Header.js
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
├── multi_agent_infrastructure_workflow.md
├── plans/
│   └── integration_plan.md
└── README.md
```

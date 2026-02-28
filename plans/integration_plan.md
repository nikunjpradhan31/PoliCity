# Multi-Agent Infrastructure Reporting Workflow Integration Plan

## Overview
This plan outlines the integration of the Multi-Agent Infrastructure Reporting Workflow into the existing `backend/app`. It will cover adding new dependencies, establishing the proposed folder structure, setting up MongoDB interactions with Motor (Async), writing the core services and agents, and connecting it all to the existing FastAPI router and main application configuration.

---

## Step 1: Install Required Dependencies
The existing `backend/requirements.txt` is missing several packages required for this workflow. We need to install the following core and utility packages to support scraping, asynchronous database access, caching, and document generation.

**Action:** Append the following to `backend/requirements.txt` and install via `pip install -r backend/requirements.txt`:
```text
# Multi-Agent Workflow Core
beautifulsoup4==4.12.0
lxml==5.1.0
aiohttp==3.9.0

# Report generation
weasyprint==60.1
jinja2==3.1.3

# Database (Async)
motor==3.3.2

# Caching
redis==5.0.0

# Geospatial
geopy==2.4.0

# Utilities
fake-useragent==1.4.0
tenacity==8.2.3
```

---

## Step 2: Establish Directory Structure
We must create the missing directories required for the workflow within the `backend/app` directory.

**Action:** Execute `mkdir -p backend/app/agents backend/app/services backend/app/workflows` and create the following stub files (`__init__.py` for all folders):
```text
backend/app/
├── agents/
│   ├── __init__.py
│   ├── base.py
│   ├── thinking.py
│   └── report_gen.py
├── services/
│   ├── __init__.py
│   ├── web_scraper.py
│   ├── open_data.py
│   ├── geocoder.py
│   ├── license_verify.py
│   ├── grant_search.py
│   ├── cache.py
│   └── mongo.py
└── workflows/
    ├── __init__.py
    └── infrastructure.py
```

---

## Step 3: Implement Database Services (`app.services.mongo`)
Currently, `backend/app/db.py` uses synchronous PyMongo and `routes.py` and `main.py` expect `app.services.mongo.setup_indexes` and Motor for async workflow persistence. We need to provide the `services/mongo.py` that utilizes `motor.motor_asyncio.AsyncIOMotorClient`.

**Action:**
1. Create `backend/app/services/mongo.py`:
   - Initialize `AsyncIOMotorClient` using `MONGODB_URI` from `.env`.
   - Implement `setup_indexes()` function to create a unique index on `incident_id` for `incidents`, `agent_thinking`, and `agent_report`, and a TTL index on `incidents`.
   - Provide helper functions (e.g., `get_workflow_db()`, `get_incident()`, `save_incident()`, `save_agent_output()`).
2. Optional: Keep `backend/app/db.py` for synchronous PyMongo if legacy routes depend on it, but use `backend/app/services/mongo.py` strictly for the new async workflow.

---

## Step 4: Implement Utility Services (`backend/app/services/`)
We will create individual modules for scraping and external API interactions to keep the code modular and testable.

**Action:**
1. **`cache.py`**: Configure Redis connection via `REDIS_URL` and create `get_cache()` and `set_cache()` helper methods with TTL capabilities.
2. **`web_scraper.py`**: Implement async scraping with `aiohttp` and `beautifulsoup4`. Add `tenacity` decorators for exponential backoff, and rotate User-Agents via `fake-useragent`. Enforce the 2-second rate limit using `asyncio.sleep()`.
3. **`open_data.py`**: Connect to City Open Data/311 APIs (using `aiohttp` to fetch JSON) and format budget allocations.
4. **`geocoder.py`**: Wrap the Census Geocoder REST API or use `geopy` for fallback Google Maps implementation.
5. **`license_verify.py` & `grant_search.py`**: Write async functions to query state/federal APIs or scrape appropriate portals for contractor licenses and grants.

---

## Step 5: Implement Agents (`backend/app/agents/`)
Each agent inherits from a common base class and invokes the `gemini-3-flash-preview` model.

**Action:**
1. **`base.py`**: Define an abstract `AgentBase` class with a `run(inputs: dict)` async method. Include logic for structuring the output into the standard metadata envelope (tracking `duration_ms`, `tokens_used`, `confidence`, etc.).
2. **`thinking.py`**: Implement the `ThinkingAgent`. 
   - Combine prompts for planning, geocoding, scraping.
   - Inject the external service outputs into the LLM context.
   - Format the response as defined in the `Agent 1: Thinking Agent` JSON schema.
3. **`report_gen.py`**: Implement the `ReportGeneratorAgent`.
   - Consume the outputs of the Thinking Agent.
   - Use Jinja2 to render the final JSON and `weasyprint` if PDF output is triggered.
   - Format the output matching the `Agent 2: Report Generator Agent` JSON schema.

---

## Step 6: Implement Workflow Orchestrator (`backend/app/workflows/infrastructure.py`)
This is the core manager that interacts with FastAPI routes, Database, and Agents.

**Action:** Write the orchestrator class or module (`workflow`) exposing `start_pipeline`, `get_status`, and `get_incident`.
1. **`start_pipeline(request)`**: 
   - Create or fetch `incident_id`.
   - Check the MongoDB collections for saved agent outputs to support partial execution/resuming.
   - Manage the sequence: invoke `ThinkingAgent`, save to DB, invoke `ReportGeneratorAgent`, save to DB.
   - Implement `force_refresh` logic to wipe saved data if requested.
   - Track progress and status in the `incidents` collection.
2. **`get_status(report_id)`**: Poll MongoDB `incidents` to return the current progress.
3. **`get_incident(incident_id)`**: Fetch all associated pipeline records.

---

## Step 7: Update FastAPI Routes (`backend/app/routes.py`)
The `routes.py` already includes stubbed routes (GET/POST for reports and incidents), but it lacks the WebSocket implementation mentioned in the specification.

**Action:**
1. Import `WebSocket` and `WebSocketDisconnect` from `fastapi`.
2. Add a new endpoint `@router.websocket("/workflow/infrastructure-report/{report_id}")`.
3. Connect the WebSocket to a generic pub/sub mechanism (could use `asyncio.Queue` or Redis pub/sub) that broadcasts `"agent_complete"` events when the orchestrator updates progress.

---

## Step 8: Update Configuration (`backend/.env` & `backend/app/main.py`)
The workflow introduces several new environment variables.

**Action:**
1. Create a `backend/.env.example` file reflecting:
   ```env
   GEMINI_API_KEY=your_api_key
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DB_NAME=infrastructure_reports
   GOOGLE_MAPS_API_KEY=
   REDIS_URL=redis://localhost:6379
   CACHE_DEFAULT_TTL_DAYS=7
   SCRAPING_PROXY_URL=
   SCRAPING_USER_AGENT_POOL=
   REPORT_BASE_URL=http://localhost:8000
   REPORT_STORAGE_PATH=./reports
   ```
2. Verify `backend/app/main.py` properly initiates the `lifespan` event. Currently, it tries to call `await setup_indexes()`, which is perfectly aligned with the newly created `services/mongo.py`.

---

## Next Steps
Once approved, we will switch to **Code Mode** to incrementally build this out: starting with dependency installation and folder structuring, followed by the Database/Service layer, and finally the Agents and Workflow integration.

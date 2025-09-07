# Fathom Backend

FastAPI backend for LUSID Workflow Task Investigation.

## Setup

1. **Install Python 3.8+** (if not already installed)

2. **Start the backend:**
   ```bash
   cd backend
   ./start.sh
   ```

3. **Manual setup (alternative):**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```

## Configuration

- **LUSID Secrets**: Place `secrets.json` in project root
- **CORS**: Configure allowed origins in `.env`

## API Endpoints

- `GET /fathom/tasks` - Fetch filtered workflow tasks
  - Query params: `dateFrom`, `dateTo`, `searchQuery`, `states`, `correlationIds`
- `GET /fathom/tasks/{task_id}` - Get specific task details
- `GET /health` - Health check

## Development

Backend runs on `http://localhost:8000` by default.
Frontend should connect to this endpoint for task data.

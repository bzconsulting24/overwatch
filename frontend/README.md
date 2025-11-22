# Overwatch React Frontend

React + TypeScript UI for the Python analysis engine. Designed for running video analyses, showing live progress, and reviewing transcripts plus behavioral signals.

## Quick start
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
npm run build # production build in dist/
```

Backend (from repository root):
```bash
cd behaviorAnalysis
uvicorn api_server:app --reload --port 8000
```
If you run the backend on another host/port, set `VITE_API_URL` (e.g., `VITE_API_URL=http://localhost:8000`).

Docker (full stack)
```bash
docker-compose up --build
# frontend: http://localhost:5173
# backend:  http://localhost:8000
```
The Nginx front proxy forwards `/api` to the backend container.

## API contract (Python backend)
- `POST /api/analyze` → `{ jobId }`
  - Body: `{ "videoUrl": string, "outputDir"?: string, "modelHint"?: "fast" | "default" | "accurate" }`
- `GET /api/analyze/{jobId}` → `{ status: "running" | "completed" | "error", progress: number, result?: {...} }`
  - `result` shape should match `AnalysisResult` in `src/types.ts`.

### Example FastAPI shim
```python
from fastapi import FastAPI
from pydantic import BaseModel
from behaviorAnalysis.hitl_runner import HITLRunner
import asyncio, uuid

app = FastAPI()
jobs = {}

class AnalyzeRequest(BaseModel):
    videoUrl: str
    outputDir: str | None = None
    modelHint: str | None = None

@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running", "progress": 5}
    async def run_job():
        runner = HITLRunner(req.outputDir or "./out")
        transcript = runner.run_analysis(req.videoUrl)
        jobs[job_id] = {"status": "completed", "progress": 100, "result": {"transcript": transcript}}
    asyncio.create_task(run_job())
    return {"jobId": job_id}

@app.get("/api/analyze/{job_id}")
async def status(job_id: str):
    return jobs.get(job_id, {"status": "error", "progress": 0})
```

Point `VITE_API_URL` to the backend origin if not using the Vite dev proxy.

## Files to touch
- UI entry: `src/App.tsx`
- API/polling: `src/hooks/useAnalysisClient.ts`
- Types shared with backend: `src/types.ts`
- Styling: `src/styles.css`

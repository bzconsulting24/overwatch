import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from hitl_runner import HITLRunner

app = FastAPI(title="Overwatch Analysis API")


class AnalyzeRequest(BaseModel):
    videoUrl: str
    outputDir: Optional[str] = None
    modelHint: Optional[str] = None  # reserved for future selection


class JobState(BaseModel):
    status: str
    progress: int
    transcript: Optional[str] = None
    error: Optional[str] = None


# In-memory job store; replace with Redis/DB for production
jobs: Dict[str, JobState] = {}
executor = ThreadPoolExecutor(max_workers=2)


def _update_job(job_id: str, status: Optional[str] = None, progress: Optional[int] = None):
    current = jobs.get(job_id)
    if not current:
        return
    jobs[job_id] = JobState(
        status=status or current.status,
        progress=progress if progress is not None else current.progress,
        transcript=current.transcript,
        error=current.error,
    )


def _run_analysis(job_id: str, req: AnalyzeRequest):
    try:
        output_dir = req.outputDir or "./out"
        runner = HITLRunner(output_dir)

        def progress_callback(pct: int):
            _update_job(job_id, progress=min(max(int(pct), 0), 100))

        def status_callback(msg: str):
            _update_job(job_id, status=msg)

        transcript = runner.run_analysis(
            req.videoUrl,
            progress_callback=progress_callback,
            status_callback=status_callback,
        )
        jobs[job_id] = JobState(status="completed", progress=100, transcript=transcript)
    except Exception as exc:  # noqa: BLE001
        jobs[job_id] = JobState(
            status="error",
            progress=100,
            error=str(exc),
            transcript=None,
        )


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    if not req.videoUrl:
        raise HTTPException(status_code=400, detail="videoUrl is required")

    job_id = str(uuid.uuid4())
    jobs[job_id] = JobState(status="running", progress=5)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, _run_analysis, job_id, req)
    return {"jobId": job_id}


@app.get("/api/analyze/{job_id}")
async def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    payload = job.model_dump()
    if job.status == "completed" and job.transcript:
        payload["result"] = {
            "transcript": job.transcript,
            "cheatingIndicators": [],
            "keyboardFindings": [],
            "behaviorSummary": [],
            "openfaceInsights": [],
            "log": [],
        }
    return payload


@app.get("/health")
async def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

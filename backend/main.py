import asyncio
import json
import uuid
import os
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agent import fill_contact_form
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store
# Structure: { batch_id: { job_id: {url, status, message} } }
jobs: dict = {}

# Max 3 parallel browsers at a time
semaphore = asyncio.Semaphore(3)


class FormRequest(BaseModel):
    urls: list[str]
    name: str
    email: str
    phone: str
    message: str


async def process_single_url(batch_id: str, job_id: str, url: str, info: dict):
    async with semaphore:
        # Status: running
        jobs[batch_id][job_id]["status"] = "running"

        # Agent ko call karo
        result = await fill_contact_form(url, info)

        # Result save karo
        jobs[batch_id][job_id]["status"] = result["status"]
        jobs[batch_id][job_id]["message"] = result["message"]


async def run_all_jobs(batch_id: str, urls: list[str], info: dict):
    tasks = [
        process_single_url(batch_id, str(i), url, info)
        for i, url in enumerate(urls)
    ]
    await asyncio.gather(*tasks)


@app.post("/api/submit")
async def submit_forms(req: FormRequest, background_tasks: BackgroundTasks):

    # Max 50 links allow karo
    urls = req.urls[:50]

    # Batch ID generate karo
    batch_id = str(uuid.uuid4())

    # Saare jobs queued mein daal do
    jobs[batch_id] = {
        str(i): {
            "id": str(i),
            "url": url,
            "status": "queued",
            "message": ""
        }
        for i, url in enumerate(urls)
    }

    # Info dict banao
    info = {
        "name": req.name,
        "email": req.email,
        "phone": req.phone,
        "message": req.message,
    }

    # Background mein run karo — user wait nahi karega
    background_tasks.add_task(run_all_jobs, batch_id, urls, info)

    return {
        "batch_id": batch_id,
        "total": len(urls),
        "message": "Jobs started!"
    }


@app.get("/api/status/{batch_id}")
async def stream_status(batch_id: str):
    """SSE endpoint — frontend ko real-time updates milenge"""

    async def event_generator():
        while True:
            if batch_id not in jobs:
                yield f"data: {json.dumps([])}\n\n"
                break

            current_jobs = list(jobs[batch_id].values())
            yield f"data: {json.dumps(current_jobs)}\n\n"

            # Check karo sab complete hue ya nahi
            all_done = all(
                j["status"] in ["success", "failed", "skipped"]
                for j in current_jobs
            )

            if all_done:
                yield f"data: {json.dumps(current_jobs)}\n\n"
                break

            await asyncio.sleep(1)  # Har 1 second mein update

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx buffering band karo
        }
    )


@app.get("/")
async def root():
    return {"message": "Contact Form Agent API is running 🚀"}

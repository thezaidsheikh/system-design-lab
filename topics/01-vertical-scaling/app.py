"""SD-01 Vertical Scaling lab — real FastAPI API to load-test with k6.

Run with 1 worker, then with 4 workers, and compare.
No database, no Docker needed. Python 3.12+, FastAPI + Uvicorn.

Install once (in a venv):
    pip install fastapi uvicorn

Run with 1 worker (single process, single core for CPU work):
    uvicorn app:app --host 127.0.0.1 --port 8000 --workers 1

Run with 4 workers (4 processes, 4 cores — Python's Node-cluster equivalent):
    uvicorn app:app --host 127.0.0.1 --port 8000 --workers 4
"""
import hashlib
import time

from fastapi import FastAPI

app = FastAPI(title="SD-01 Vertical Scaling Lab")


@app.get("/health")
def health():
    """Liveness check. Always cheap — used by k6 to confirm the API is up."""
    return {"status": "ok"}


@app.get("/fast")
def fast():
    """I/O-style endpoint: almost no CPU work.

    With many virtual users this endpoint scales well even with 1 worker,
    because the work is tiny. It is the control case: if /fast also gets
    slow, the bottleneck is not CPU, it is connections / the test itself.
    """
    return {"endpoint": "fast", "message": "ok"}


def cpu_work(n: int = 200_000) -> str:
    """Deliberately CPU-bound work: hash in a tight loop.

    This is the point of the lab. One Python process can only run this
    on one core at a time (GIL), so 1 worker saturates at ~1 core.
    4 workers run 4 copies in parallel on 4 cores.
    """
    data = b"opspilot-vertical-scaling"
    for _ in range(n):
        data = hashlib.sha256(data).digest()
    return data.hex()[:16]


@app.get("/cpu")
def cpu():
    """CPU-bound endpoint. This is where 1 worker vs 4 workers shows up."""
    started = time.perf_counter()
    result = cpu_work()
    took_ms = round((time.perf_counter() - started) * 1000, 1)
    return {"endpoint": "cpu", "result": result, "took_ms": took_ms}

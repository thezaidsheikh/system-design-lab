"""SD-01 Vertical Scaling lab — runnable simulation (stdlib only).

No FastAPI, no k6, no Docker. Just Python.

What it shows:
1. Load below capacity -> everything smooth, queue stays 0.
2. Load at capacity -> on the edge, queue stays 0 but no headroom.
3. Load above capacity -> queue grows every second, latency blows up.
4. Same load on a bigger machine (scale up) -> queue gone.

Run:  python demo.py
Real API version (FastAPI + k6): see app.py and loadtest.js in this folder.
"""
from __future__ import annotations


def queue_after_seconds(arriving: int, capacity: int, seconds: int) -> int:
    """Queue length after `seconds` at a steady arriving rate.

    Every second, (arriving - capacity) extra requests join the queue
    when arriving > capacity. Queue never goes below 0.
    """
    return max(0, (arriving - capacity) * seconds)


def status(load: int, capacity: int) -> str:
    """One-line verdict for a load level."""
    return "sambhal gaya" if capacity >= load else "line lagegi"


def simulate(arriving: int, capacity: int, seconds: int = 5) -> list[tuple[int, int]]:
    """Second-by-second queue growth. Returns [(second, queue), ...]."""
    rows = []
    queue = 0
    for second in range(1, seconds + 1):
        queue = max(0, queue + arriving - capacity)
        rows.append((second, queue))
    return rows


def show(title: str, arriving: int, capacity: int) -> None:
    print(f"\n{title} — load {arriving} RPS, capacity {capacity} RPS: {status(arriving, capacity)}")
    print(f"{'second':>6} | {'queue':>5}")
    print("-" * 16)
    for second, queue in simulate(arriving, capacity):
        print(f"{second:>6} | {queue:>5}")


def main() -> None:
    print("SD-01 Vertical Scaling — queue simulation")
    print("Server capacity = 100 RPS (chhoti machine)")

    show("1. Load capacity se neeche", arriving=50, capacity=100)
    show("2. Load capacity ke barabar", arriving=100, capacity=100)
    show("3. Load capacity se upar", arriving=250, capacity=100)

    print("\n--- Scale up: wahi load 250 RPS, badi machine (capacity 380 RPS) ---")
    show("4. Scale up ke baad", arriving=250, capacity=380)

    print("\nTakeaway: load capacity se upar gaya to queue har second badhti hai.")
    print("Vertical scaling = capacity badhao, queue gayab. Par ek hadd hai (SD-02).")


if __name__ == "__main__":
    main()

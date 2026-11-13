"""SD-01 · Vertical scaling — runnable simulation.

Ek server jiski capacity (RPS) badha sakte ho. Teen load levels par chalega:

1. capacity ke neeche  — sab smooth, queue zero.
2. capacity ke barabar — kinare par, queue zero par system full.
3. capacity se upar   — queue second-by-second badhti hai, latency phat ti hai.
4. phir wahi load ek "badi machine" (scale up) par — queue gayab.

Sirf Python standard library. Chalana:

    python topics/01-vertical-scaling/demo.py

Apne numbers se khelna ho to:

    python topics/01-vertical-scaling/demo.py --capacity 100 --load 250 --seconds 5
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class SecondRow:
    """Ek second ka snapshot: queue me kitni requests khadi hain."""

    second: int
    arriving: int
    served: int
    queue: int
    # Queue me khadi aakhiri request ko serve hone me kitna wait karna padega.
    wait_seconds: float


def queue_after_seconds(
    capacity_rps: int, load_rps: int, seconds: int, initial_queue: int = 0
) -> int:
    """`seconds` ke baad queue me kitni requests khadi hongi.

    Har second `load - capacity` requests bach jati hain (agar load zyada hai),
    aur load kam ho to queue utni hi khaali hoti hai — zero se neeche nahi jati.
    `initial_queue` se pehle se lagi line se shuru kar sakte ho.
    """
    if capacity_rps <= 0:
        raise ValueError("capacity_rps 0 se bada hona chahiye")
    if seconds < 0:
        raise ValueError("seconds negative nahi ho sakta")
    if initial_queue < 0:
        raise ValueError("initial_queue negative nahi ho sakta")
    queue = initial_queue
    for _ in range(seconds):
        queue = max(0, queue + load_rps - capacity_rps)
    return queue


def is_overloaded(capacity_rps: int, load_rps: int) -> bool:
    """Load capacity se upar hai to queue kabhi khaali nahi hogi."""
    return load_rps > capacity_rps


def simulate(capacity_rps: int, load_rps: int, seconds: int = 5) -> list[SecondRow]:
    """Second-by-second simulation; har second ek row."""
    if capacity_rps <= 0:
        raise ValueError("capacity_rps 0 se bada hona chahiye")
    if seconds < 0:
        raise ValueError("seconds negative nahi ho sakta")
    queue = 0
    rows: list[SecondRow] = []
    for second in range(1, seconds + 1):
        served = min(capacity_rps, queue + load_rps)
        queue = max(0, queue + load_rps - capacity_rps)
        # Aakhiri request ko apne se pehle khadi queue drain hone ka wait hai.
        wait = queue / capacity_rps
        rows.append(
            SecondRow(
                second=second,
                arriving=load_rps,
                served=served,
                queue=queue,
                wait_seconds=round(wait, 2),
            )
        )
    return rows


def _print_scenario(title: str, capacity_rps: int, load_rps: int, seconds: int = 5) -> None:
    print(f"\n{title}")
    print(f"Capacity: {capacity_rps} RPS | Load: {load_rps} RPS")
    print(f"{'sec':>3} | {'aayi':>5} | {'serve':>5} | {'queue':>5} | {'wait (s)':>8}")
    print("-" * 38)
    for row in simulate(capacity_rps, load_rps, seconds):
        print(
            f"{row.second:>3} | {row.arriving:>5} | {row.served:>5} | "
            f"{row.queue:>5} | {row.wait_seconds:>8.2f}"
        )
    final_queue = queue_after_seconds(capacity_rps, load_rps, seconds)
    if is_overloaded(capacity_rps, load_rps):
        print(f"=> {seconds} sec baad queue: {final_queue} — badhti hi ja rahi hai, latency phat rahi hai.")
    elif load_rps == capacity_rps:
        print("=> Kinare par: queue zero hai, par ek bhi extra request aayi to line lag jayegi.")
    else:
        print("=> Sab smooth: queue zero, har request turant serve ho rahi hai.")


def main() -> None:
    parser = argparse.ArgumentParser(description="SD-01 vertical scaling simulation")
    parser.add_argument("--capacity", type=int, default=100, help="chhoti machine ki capacity (RPS)")
    parser.add_argument("--load", type=int, default=250, help="aane wala load (RPS)")
    parser.add_argument("--seconds", type=int, default=5, help="kitne seconds simulate karein")
    parser.add_argument(
        "--scaled-capacity",
        type=int,
        default=380,
        help="scale-up ke baad badi machine ki capacity (RPS)",
    )
    args = parser.parse_args()

    print("SD-01 · Vertical scaling — queue kaise jamti hai, scale up kya karta hai")

    # 1. Capacity ke neeche — aadha load.
    _print_scenario("1) Load capacity ke neeche", args.capacity, args.capacity // 2, args.seconds)
    # 2. Capacity ke barabar — kinare par.
    _print_scenario("2) Load capacity ke barabar", args.capacity, args.capacity, args.seconds)
    # 3. Capacity se upar — queue jamti hai.
    _print_scenario("3) Load capacity se upar", args.capacity, args.load, args.seconds)
    # 4. Wahi load, badi machine (scale up) — queue gayab.
    _print_scenario(
        "4) Wahi load, badi machine par (scale up)",
        args.scaled_capacity,
        args.load,
        args.seconds,
    )
    print(
        "\nSeekh: capacity 100 se 380 karne par wahi 250 RPS ka load sambhal gaya — "
        "par CPU 4 guna karne par capacity 4 guna nahi badhi (100 -> 380). "
        "Scaling linear nahi hoti."
    )


if __name__ == "__main__":
    main()

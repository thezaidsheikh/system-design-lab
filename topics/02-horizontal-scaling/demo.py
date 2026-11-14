"""SD-02 Horizontal Scaling lab — runnable simulation (stdlib only).

No install, no Docker. Just Python.

What it shows:
1. Stateful servers: the same 6 requests, round-robin across 2 servers.
   Each server remembers only what IT saw, so each reports 3 — neither
   knows the real total (6).
2. Stateless servers + shared store: the same 6 requests, but every
   server reads and writes one shared store, so both report the true
   total (6).

The shared store stands in for Redis (sessions, counters) or Postgres
(data) in a real system. The servers stay dumb and replaceable: kill
either one and nothing is lost, because the state was never in it.

Run:  python demo.py
"""
from __future__ import annotations


class StatefulServer:
    """Keeps the user's request count in its own memory. The stateful trap."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.request_count = 0  # lives in THIS server's RAM only

    def handle(self, user: str) -> str:
        self.request_count += 1
        return f"{self.name}: {user} has made {self.request_count} request(s) (as far as I know)"

    def count_for(self, user: str) -> int:
        """What this server believes the user's total request count is."""
        return self.request_count


class StatelessServer:
    """Keeps nothing. Reads/writes the count in a shared store every time."""

    def __init__(self, name: str, shared_store: dict[str, int]) -> None:
        self.name = name
        self.store = shared_store  # e.g. Redis in real life

    def handle(self, user: str) -> str:
        self.store[user] = self.store.get(user, 0) + 1
        return f"{self.name}: {user} has made {self.store[user]} request(s) (shared truth)"

    def count_for(self, user: str) -> int:
        """What this server believes the user's total request count is."""
        return self.store.get(user, 0)


def round_robin(servers, user: str, n: int = 6) -> dict[str, int]:
    """Send `n` requests from one user across the servers, round-robin.

    Returns what each server believes the user's total request count is
    after all `n` requests.
    """
    print(f"  {n} requests from {user}, round-robin across {[s.name for s in servers]}:")
    for i in range(n):
        server = servers[i % len(servers)]
        print(f"    request {i + 1} -> {server.handle(user)}")
    return {server.name: server.count_for(user) for server in servers}


def main() -> None:
    print("SD-02 Horizontal Scaling — 2 servers, 1 user, 6 requests")
    print("Load balancer: round-robin (request 1 -> A, 2 -> B, 3 -> A, ...)")

    print("\n1) STATEFUL — each server remembers only what IT saw:")
    seen = round_robin([StatefulServer("server-A"), StatefulServer("server-B")], "zaid")
    print(f"   Problem: server-A says {seen['server-A']} requests, server-B says {seen['server-B']} requests.")
    print("   Neither knows the real total (6). A session stored here is lost")
    print("   the moment the load balancer sends you to the other server.")

    print("\n2) STATELESS + SHARED STATE — servers remember nothing, store knows all:")
    shared_store: dict[str, int] = {}  # stands in for Redis
    seen = round_robin(
        [StatelessServer("server-A", shared_store), StatelessServer("server-B", shared_store)],
        "zaid",
    )
    print(f"   Both servers report the true total ({seen['server-A']}). Kill either server and")
    print("   nothing is lost — the state was never in the server.")

    print("\nTakeaway: horizontal scaling only works if the servers are stateless.")
    print("State lives OUTSIDE the servers — sessions and counters in Redis, data in Postgres.")
    print("Scale up first while it is simpler (SD-01); scale out when one machine")
    print("hits its ceiling or becomes a single point of failure.")


if __name__ == "__main__":
    main()

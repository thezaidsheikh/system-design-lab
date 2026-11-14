# SD-01 — Vertical Scaling lab

**Question this lab answers:** vertical scaling sach me ho raha hai ya nahi — aur Python me use kaise dikhaye?

## 0. Is folder me do demos hain

- **`demo.py` (stdlib only, no install)** — queue simulation: load capacity se neeche, barabar, upar, phir badi machine par. Chalao: `python demo.py`. Tests: `python -m unittest test_demo -v` (6 tests).
- **`app.py` + `loadtest.js` (real API + k6)** — asli FastAPI API aur k6 load test, 1 worker vs 4 workers. Yehi asli proof hai. Neeche section 2 se padho.

## 1. Node.js se mapping — tumhara sawaal, seedha jawab

Node.js by default single-threaded hota hai — ek process, ek core. `cluster` module se tum ek hi app ke multiple processes chalate ho, har process ek core use karta hai. Isi ko vertical scaling ke andar multi-process kehte hain.

Python me wahi kaam **multiple worker processes** se hota hai. CPython me GIL hota hai — ek process ke andar threads CPU-bound kaam ko parallel nahi kar sakte. Isliye:

- **Threads se fark nahi padega** CPU-bound endpoint par. Thread badhane se ek hi core use hota rahega.
- **Workers/processes se fark padega.** `uvicorn --workers 4` matlab 4 alag Python processes, har ek apne core par. Yehi Python ka Node `cluster` ke barabar hai.
- Gunicorn me wahi cheez `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app` hoti hai.

Vertical scaling ke do hisse hain, dono alag hain:
1. **Bigger machine** — ek process ko zyada RAM/CPU dena. Isse CPU-bound kaam ki speed ek core tak badhti hai, uske baad nahi.
2. **More processes on the same machine** — workers badhana. Isse multiple cores use hote hain. Yehi is lab me test karte hain.

## 2. Lab — real API + k6 virtual users

**API (`app.py`):** FastAPI, 3 endpoints.
- `GET /health` — hamesha cheap, API up hai ya nahi check karne ke liye.
- `GET /fast` — lagbhag zero CPU kaam. Control case: agar ye bhi slow ho, to bottleneck CPU nahi hai.
- `GET /cpu` — jaan-bujh kar CPU-bound kaam (`hashlib.sha256` loop, 200,000 baar). Isi par 1 worker vs 4 workers ka fark dikhega.

**Load test (`loadtest.js`):** k6, 50 virtual users, 10s ramp-up, 30s hold, 5s ramp-down. Virtual user matlab ek concurrent client jo baar-baar request karta hai — real browser nahi, par load ke liye wahi kaafi hai.

## 3. Apne MacBook (M3, 8 GB RAM) par kaise chalaye

Pehle check karo k6 hai ya nahi:
```bash
k6 version
# nahi hai to: brew install k6
```

Ek venv me install karo:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn
```

**Round 1 — 1 worker:**
```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --workers 1
# dusre terminal me:
k6 run loadtest.js
```

**Round 2 — 4 workers:** pehle wali API band karo (Ctrl+C), phir:
```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --workers 4
k6 run loadtest.js
```

Activity Monitor khula rakho — Round 1 me 1 Python process ~100% CPU (1 core) dikhega, Round 2 me 4 processes dikhenge.

## 4. Kya fark dikhna chahiye (expected result)

| | 1 worker | 4 workers |
|---|---|---|
| `/cpu` requests/sec | low — 1 core saturate | ~3–4x zyada |
| p95 latency | zyada, VUs badhne par aur badhega | clearly kam |
| CPU use | 1 core ~100% | 4 cores use hote hain |
| `/fast` | dono me fast | dono me fast (control case) |

Ye approximate hai — M3 me 8 cores hain (4 performance + 4 efficiency), isliye 4 workers ke liye jagah hai. 8 workers mat lagana — 8 GB RAM par fayda nahi, context switching badhega.

Agar 1 worker aur 4 workers me koi fark na dikhe, to samjho endpoint CPU-bound nahi hai — phir `/cpu` ka loop badhana padega, ya phir test galat endpoint par chal raha hai. Yehi debugging hai.

## 5. Interview me kaise bolna hai (30–40 sec)

> "Vertical scaling matlab ek hi machine ko powerful banana — zyada CPU, zyada RAM. Python me ek process GIL ki wajah se CPU-bound kaam ke liye ek core tak limited hai, isliye maine Uvicorn ke 4 workers chalaye, har worker ek alag process hai aur ek alag core use karta hai, bilkul Node ke cluster jaisa. Maine k6 se 50 virtual users se load test kiya — 1 worker par RPS low aur p95 high tha, 4 workers par RPS lagbhag 3–4x aur p95 clearly kam tha. Iska trade-off hai memory — har worker apni memory leta hai — aur iski limit hai, uske baad horizontal scaling chahiye hota hai."

## 6. Trade-offs

- Workers badhana free nahi hai — har worker apni RAM leta hai, 8 GB par 4 workers theek hain, 16 nahi.
- Vertical scaling ki limit hoti hai — ek machine kitni bhi badi ho, ek point ke baad cost aur single point of failure badh jata hai. Tab horizontal scaling (SD-03) aata hai.
- Threads I/O-bound kaam ke liye theek hain, CPU-bound ke liye nahi — yehi GIL ka practical matlab hai.

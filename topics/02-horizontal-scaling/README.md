# SD-02 — Horizontal Scaling lab

**Question this lab answers:** ek server se kaam na chale to kya kare — badi machine lo, ya aur machines jodo? Aur machines jodne par session/counter kyun toot jata hai?

## 0. Is folder me kya hai

- **`demo.py` (stdlib only, no install)** — simulation: 2 servers behind a round-robin load balancer, same 6 requests. Pehle stateful servers (har server apni memory me count rakhta hai — dono 3/3 bolte hain, asli total 6 kisi ko nahi pata), phir stateless servers + shared store (dono asli total 6 bolte hain). Chalao: `python demo.py`. No install, no Docker.

## 1. Horizontal scaling (scale out) kya hai

Load zyada ho gaya to ek machine ko powerful banana (vertical scaling, SD-01) ki jagah **aur machines jodna** — horizontal scaling. Example: OpsPilot API par 10x traffic aa gaya, to ek badi machine lene ki jagah same API ki 4 copies chalao, load balancer ke peeche, aur har request kisi bhi copy par ja sakti hai.

**Sirf scale up kyun nahi karte?** SD-01 ki do problems hain:

1. **Ceiling hoti hai** — ek machine kitni bhi badi ho, ek point ke baad aur badi nahi ho sakti, aur har unit power ke liye cost badhti jati hai.
2. **Single point of failure (SPOF)** — ek hi badi machine hai, wo mar gayi to sab kuch mar gaya.

Horizontal scaling dono problems hatata hai: sasti machines jodo, aur ek mar jaye to baaki serve karte rehte hain.

## 2. Stateless vs stateful — ek idea jo decide karta hai scale out chalega ya nahi

- **Stateless server** — requests ke beech apni memory me koi per-user data nahi rakhta. Har request me jo chahiye wo ya to request ke saath aata hai, ya server shared store se fetch karta hai. Example: API request me incident ID padhti hai, Postgres se lookup karti hai, result deti hai — 4 servers me se koi bhi koi bhi request handle kar sakta hai, kyunki koi kuch yaad nahi rakhta.
- **Stateful server** — per-user data apni memory me rakhta hai, jaise login session ya ek variable me counter. Example: server A ko yaad hai "user Zaid logged in hai", server B ko nahi. Load balancer Zaid ki agli request server B par bhej de, to wo logged out dikhega.

Demo me wahi dikhta hai: stateful servers 6 requests ke baad bhi 3/3 bolte hain — asli total 6 kisi ko nahi pata. Stateless servers + shared store dono 6 bolte hain.

## 3. Shared state — asli fix

Saara state servers ke **bahar** rakho, ek jagah jahan har server pahunch sake:

| State | Kahan rehta hai | Kyun |
|---|---|---|
| Logged-in user ka session | Redis (ya token me) | Server mar jaye to session na mare |
| Incident record | Postgres | Data ka ek source of truth |
| Rate-limit counter | Redis | Har server ko same count dikhe |
| Uploaded files | Object storage (S3 jaisi) | Kisi ek server ki disk par nahi |

Servers dumb aur replaceable rehte hain; state shared store me rehta hai. Yehi OpsPilot ka shape hai: FastAPI servers stateless, Postgres + Redis state sambhalte hain.

## 4. Sticky sessions — workaround, fix nahi

Stateful servers ke saath ek jugaad hota hai: **sticky session** — load balancer hamesha ek hi user ko ek hi server par bhejta hai. Kaam to karta hai, par:

- Jis server par session hai, wo mar gaya to session uske saath mar gaya.
- Load evenly distribute nahi hota — ek server par zyada users atak sakte hain.
- Server add/remove karna mushkil ho jata hai.

Interview me ye line yaad rakho: *"sticky sessions are a workaround, not a fix — the session dies with the server."*

## 5. Trade-offs (senior-level, interview me ye bolna hai)

- Horizontal scaling free nahi hai: ab load balancer chahiye, shared state chahiye, aur deployment aisa ho jo identical copies start/stop kar sake. Debugging mushkil hoti hai — ek request kisi bhi server par ja sakti hai, isliye logs centralised hone chahiye (yehi wajah hai Day 6 structured logging matter karta hai).
- Har cheez horizontally scale nahi hoti: ek Postgres database ab bhi ek writer hai. Database ko scale karna alag problem hai — replication, sharding (SD-06).
- Load balancer khud SPOF ban sakta hai — isliye real systems me load balancer bhi redundant hota hai.

## 6. Kab horizontal scaling NAHI karna hai

Jab ek machine me abhi headroom hai aur system chhota hai. Horizontal scaling load balancer, shared state, centralised logging aur mushkil debugging ka cost jodta hai. Pehle scale up karo (SD-01) — simpler hai, koi load balancer nahi, koi shared-state ka kaam nahi. Scale out tab karo jab ek machine ceiling ban jaye ya single point of failure ban jaye, usse pehle nahi.

## 7. Interview me kaise bolna hai (30–40 sec)

> "Horizontal scaling matlab load badhne par aur servers jodna, ek badi machine lene ki jagah. Lekin ye sirf tab kaam karta hai jab servers stateless hon — agar server apni memory me session ya counter rakhta hai, to load balancer ki agli request dusre server par ja sakti hai aur user logged out dikhega. Isliye state servers ke bahar rakho: sessions aur counters Redis me, data Postgres me. Maine is lab me demo kiya — 2 stateful servers 6 requests ke baad 3/3 bolte hain, stateless servers shared store ke saath asli total 6 bolte hain. Trade-off ye hai ki load balancer, shared state aur centralised logging ka cost aata hai, isliye pehle scale up karna chahiye, scale out tab jab ek machine ceiling ya single point of failure ban jaye."

## 8. Interview Q&A

1. **Q: Stateful server horizontal scaling kyun todta hai?**
   A: Kyunki per-user data ek server ki memory me rehta hai — load balancer agli request kisi dusre server par bhej sakta hai jo us user ke baare me kuch nahi janta. Ya to users ko servers se chipkao (sticky sessions), ya state ko bahar nikalo.
2. **Q: Kab horizontally scale NAHI karna chahiye?**
   A: Jab tak ek machine me headroom hai. Horizontal scaling load balancer, shared state, centralised logging aur mushkil debugging jodta hai — ye cost tabhi pay karo jab vertical scaling kaafi na rahe.
3. **Q: OpsPilot me state kahan rehta hai?**
   A: Kabhi bhi FastAPI server ki memory me nahi. Sessions aur rate-limit counters Redis me, incident data Postgres me — servers stateless aur replaceable rehte hain.
4. **Q: Sticky session kya hai, aur uski problem kya hai?**
   A: Load balancer hamesha ek user ko ek hi server par bhejta hai — stateful servers ka workaround. Problem: wo server mar gaya to session mar gaya, aur load evenly distribute nahi hota.
5. **Q: Load balancer khud fail ho jaye to?**
   A: Wo khud single point of failure ban jata hai — isliye real systems me load balancer redundant hota hai (active-passive ya DNS-based), aur health checks se dead servers ko rotation se bahar nikala jata hai.

## 9. Try it yourself (5–10 min)

1. Demo chalao (`python demo.py`), phir `round_robin` me servers ki sankhya 2 se 4 karo aur requests 6 se 12 — stateful case me har server kya bolega? Stateless case me kya badlega?
2. Paper par likho: OpsPilot ke FastAPI servers stateless hain — (a) logged-in user ka session, (b) incident record, (c) rate-limit counter — ye teeno kahan rehte hain? (Answers: (a) Redis / token, server memory me nahi; (b) Postgres; (c) Redis — teeno shared, kabhi server ki RAM me nahi.)
3. Bina notes ke 2 minute me samjhao: stateful server horizontal scaling kyun todta hai, aur sticky sessions ki kya keemat hai?

## New terms (2–3 lines each)

- **Horizontal scaling (scale out)** — load badhne par aur machines jodna. Example: 1 API server → 4 identical API servers, load balancer ke peeche.
- **Stateless** — server requests ke beech kuch store nahi karta. Example: 4 copies me se koi bhi koi bhi request handle kar sakta hai, kyunki har request me jo chahiye wo hota hai.
- **Stateful** — server per-user data apni memory me rakhta hai. Example: login session ek server ki RAM me — sirf wahi server janta hai user logged in hai.
- **Sticky session** — load balancer hamesha ek user ko ek hi server par bhejta hai. Example: stateful servers ka workaround; us server ke marne par session mar jata hai.
- **Single point of failure (SPOF)** — ek component jiske fail hone par poora system fail ho jaye. Example: ek badi server, ya bina replica wali single database.
- **Shared state** — data servers ke bahar, jahan sab pahunch sake. Example: sessions Redis me, incidents Postgres me.
- **Round-robin** — load balancer requests ko servers me baari-baari bhejta hai. Example: request 1 → server A, 2 → B, 3 → A, 4 → B.

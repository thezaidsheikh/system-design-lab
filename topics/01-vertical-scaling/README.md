# SD-01 · Vertical scaling (scale up)

System Design track ka pehla topic. Isse pehle ki hum load balancing, caching ya
sharding padhein, ek sawaal ka jawab pakka hona chahiye: **scaling hota kya hai,
aur system load badhne par achanak kyun girta hai?**

## Scaling matlab kya — ek chai ki dukaan se samjho

Ek chai ki dukaan hai. Ek banda (ek server) ek ghante me 60 cup bana sakta hai.
Subah 9 baje 50 log aate hain — kaam chal raha hai. Phir dukaan famous ho gayi,
200 log aane lage. Ab kya hoga? Line lagegi, log intezaar karenge, kuch bina chai
piye chale jayenge, aur woh ek banda thak ke galtiyaan karega.

System Design me isey kehte hain: **load (aane wali requests) tumhari capacity
(ek time par handle karne ki taakat) se zyada ho gayi.** Scaling matlab capacity
badhana taaki load sambhal jaye.

## Queue kaise jamti hai — code se dekho

```python
CAPACITY = 100          # requests per second (RPS)
arriving = 250          # asal me aa rahi requests per second

queue = 0
for second in range(1, 6):
    queue += arriving - CAPACITY     # har second 150 line me khade
    print(f"second {second}: line me khade = {queue}")
```

Output:

```text
second 1: line me khade = 150
second 2: line me khade = 300
second 3: line me khade = 450
second 4: line me khade = 600
second 5: line me khade = 750
```

Line = requests jo wait kar rahi hain. Line badhti hai to har nayi request ka
intezaar badhta hai (latency), memory bharne lagti hai, timeouts aane lagte hain,
aur users ko error dikhta hai. Dhyaan do — load badhne par system "thoda slow"
nahi hota, woh ek point ke baad **achanak girta hai**.

**Bottleneck** — system ka woh hissa jo sabse pehle full ho jata hai aur poore
system ki speed tay karta hai. Yahan woh ek server ki CPU hai. Load badhne ki
khabar user ki shikayat se nahi milni chahiye: CPU %, request latency aur queue
length — ye metrics dekhna hi observability ki shuruaat hai.

## Vertical scaling — wohi dukaan, ab bada aur tez banda

Vertical scaling (scale up) matlab: **usi ek machine ko aur powerful bana do.**
Zyada CPU cores, zyada RAM, tez SSD. Chai wali misaal me: wohi ek banda, par ab
uske paas badi ketli, do burner wala stove, aur tez haath — ab woh 150 cup per
ghanta bana sakta hai.

```python
server_v1 = {"cpu_cores": 2, "ram_gb": 8,  "capacity_rps": 100}
server_v2 = {"cpu_cores": 8, "ram_gb": 32, "capacity_rps": 380}
# load 250 RPS: v1 par "line lagegi", v2 par "sambhal gaya"
```

Dhyaan do: capacity 4 guna CPU par 4 guna nahi badhi (100 → 380). Hamesha aisa
hi hota hai — har cheez CPU par hi nahi atki hoti; memory, disk, network bhi
apni limit rakhte hain. Interview me ye line bolna: **"scaling linear nahi hoti."**

## Fayde — ye pehla kadam kyun hota hai

- **Code me zero change.** Wahi app, badi machine par. Na architecture badla, na
  nayi complexity aayi.
- **Data ka koi jhanjhat nahi.** Ek hi database, ek hi jagah — consistency apne
  aap bani rehti hai.
- **Solo/small team ke liye sahi shuruaat.** OpsPilot abhi ek modular monolith
  hai — uske liye vertical hi sahi pehla jawab hai.

## Deewaar — vertical scaling khatm kahan hota hai

- **Ek hadd hai.** Duniya ki sabse badi machine bhi ek din chhoti padegi. Uske
  aage koi "aur badi machine" hai hi nahi.
- **Paise ki return ghat ti hai.** 2 se 4 core sasta padta hai; 64 se 128 core
  behad mehenga — capacity utni nahi badhti jitna bill badhta hai.
- **Single point of failure.** Ek hi machine hai — woh giri to sab gaya. Badi
  machine bhi gir sakti hai.
- **Upgrade ke time downtime.** Machine badalna matlab aksar app band karke
  shift karna.

Isi deewaar se agla topic paida hota hai: jab ek machine aur badi nahi ho sakti,
to machines ki taadad badha do — woh hai **SD-02, horizontal scaling**.

## Trade-offs — ek nazar me

| | Vertical (scale up) | Horizontal (scale out, SD-02 preview) |
|---|---|---|
| Code change | Zero | Design badalna padta hai |
| Data | Ek jagah, simple | Distribute karna padta hai |
| Hadd | Ek machine ki limit | Bohot aage |
| Failure | Ek machine giri = sab gaya | Ek giri to baaki chalti hain |
| Cost | Bade sizes par mehenga hota jata hai | Chhoti machines, gradual |

**Senior rule: pehle measure karo (bottleneck kahan hai?), phir sabse simple
scaling jo kaam kare.** Bina measure kiye architecture badalna guess hai,
engineering nahi.

## OpsPilot par iska matlab — aaj ka decision

OpsPilot aaj ek modular monolith hai, ek machine par chal sakta hai. Sahi order:

- Pehle vertical: jab users badhein, machine badi karo. Simple, sasta, code
  waisa ka waisa.
- Saath me metrics rakho: CPU, latency, queue — taaki deewaar dikhe, takraye nahi.
- Jab vertical ki limit paas aaye, tab SD-02/SD-03 wale faisle: kaunsa hissa alag
  machine par jayega (pehla candidate: background ingestion worker, kyunki woh
  stateless hai — ye shabd SD-04 me khulega).

**ADR line (interview me bolne layak):** "We scale vertically first because the
system is a modular monolith run by a small team; horizontal scaling is deferred
until metrics show a specific bottleneck, and module boundaries keep that split
possible later."

## Demo chalana

Koi package install nahi — sirf Python standard library. MacBook Air par halka
chalega.

```bash
python topics/01-vertical-scaling/demo.py
```

Demo chaar scenario dikhata hai: load capacity ke neeche (smooth), capacity ke
barabar (kinare par), capacity se upar (queue second-by-second badhti hui,
latency phat ti hui), aur phir wahi load badi machine par (queue gayab). Har
step ki table print hoti hai taaki fark aankhon se dikhe.

Apne numbers se khelna ho to:

```bash
python topics/01-vertical-scaling/demo.py --capacity 100 --load 250 --seconds 5
```

Tests:

```bash
python -m unittest discover -s topics/01-vertical-scaling -v
```

## Interview Q&A — short version

**Q: Scaling kya hoti hai, aur system load badhne par achanak kyun girta hai?**
A: Scaling = capacity ko load ke hisaab se badhana. Capacity ke neeche system
theek chalta hai; jaise hi arriving requests capacity se upar gayi, har second
ek queue jama hoti hai, latency badhti hai, timeouts shuru hote hain — isiliye
girawat achanak lagti hai. Queue khud khaali nahi hoti jab tak load capacity se
neeche na aaye.

**Q: Vertical scaling kya hai, aur uski limits kya hain?**
A: Usi ek machine ko powerful banana — zyada CPU, RAM, tez disk — bina code
badle. Limits: ek physical hadd hai, bade sizes par cost tez badhta hai par
capacity utni nahi, machine single point of failure rehti hai, aur upgrade me
aksar downtime aata hai.

**Q: Tum vertical pehle kyun karoge, seedha horizontal kyun nahi?**
A: Vertical me zero code change aur zero data complexity hai — chhoti team ke
liye operational cost sabse kam. Horizontal tab justify hota hai jab metrics
dikhayein ki vertical ki hadd paas hai ya availability chahiye. Pehle se
distributed bana dena = bina wajah ki complexity.

**Q: Bottleneck kaise pehchanoge ki scale karna hi padega?**
A: Metrics se, andaze se nahi: CPU/memory saturation, p95 latency ka badhna,
queue length ka jama hona, error/timeout rate. Jo resource sabse pehle full ho
raha hai wahi bottleneck hai.

**Q: CPU 4 guna kiya to capacity 4 guna kyun nahi badhi?**
A: Request sirf CPU par nahi rukti — memory bandwidth, disk I/O, network, locks
aur single-threaded hisse bhi limit rakhte hain. Scaling kabhi perfectly linear
nahi hoti; isiliye load test karke asal capacity napte hain, spec sheet se
andaza nahi lagate.

**Q: OpsPilot ke liye tumhara scaling plan kya hai?**
A: Abhi modular monolith ek machine par; pehla step vertical scaling + metrics.
Jab bottleneck dikhe, sabse pehle stateless background worker (ingestion) ko
alag karna horizontal ki taraf pehla kadam hoga — module boundaries isiliye
saaf rakhi hain taaki ye split bina rewrite ke ho jaye.

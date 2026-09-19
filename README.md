# Lengnick (2013) — Baseline Agent-Based Macroeconomic Model

A Python implementation of the baseline ACE macroeconomic model from:

> Lengnick, M. (2013). *Agent-based macroeconomics: A baseline model.*
> Journal of Economic Behavior & Organization, 86, 102–120.

Built on [Mesa](https://github.com/projectmesa/mesa) 3.x with a Streamlit dashboard.

The model contains two agent types — households and firms — connected by a
dynamic bipartite network of trading relationships. There is no central
market-clearing mechanism: all transactions happen between named individuals,
and aggregate regularities emerge from local interaction.

---

## Running it

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

| Command | What it does |
|---|---|
| `python run.py` | Launches the Streamlit dashboard (default mode) |
| `python run.py diagnostic` | Headless run, prints a summary every 5 months |
| `python run.py 500` | Headless run of 500 months |
| `python diagnose.py` | Instrumented run — firm decision counters, branch runs, zombie counts |
| `streamlit run server.py` | Dashboard directly |

`run.py` has a `MODE` constant at the top so it can be launched from an IDE
Run button without touching the terminal.

---

## Project structure

```
agents.py     Household and Firm classes
model.py      LengnickModel — scheduling, networks, markets, data collection
server.py     Streamlit dashboard
run.py        Entry point (UI or headless diagnostic)
diagnose.py   Instrumented diagnostic run
```

### Schedule

The fundamental time unit is a **day**; 21 days make a **month**.

**Beginning of month**
1. Process last month's firing queue (see divergence 15)
2. Per firm: adjust wage, recompute inventory and price bounds, decide
   hiring/firing and price changes, reset demand counter
3. Labour market search and rewiring (type B connections)
4. Goods market rewiring — price-based and quantity-based (type A connections)
5. Households recompute their average price and plan monthly consumption

**Each day**
6. Goods market: households visit type A firms in random order and buy
7. Production: each firm adds `λ × workers` to inventory

**End of month (day 21)**
8. Firms pay wages, drawing from liquidity then buffer
9. Firms top up their liquidity buffer toward `χ · w · l`
10. Remaining firm liquidity distributed as profit, proportional to household wealth
11. Households update reservation wages

---

## Principal finding: the paper's headline result is not reproducible from its stated equations

The paper reports employment between 95.7% and 100% (Section 3, Fig. 4) and
describes consumption as following equation (12):

```
c = min( (m/P)^α , m/P )
```

**The original Java source never calls `updateConsumption()`.** The method is
defined on the `Household` class but no event in `Model.scheduleEvents()`
invokes it, so each household's planned consumption remains fixed at its
random initialisation value (drawn uniformly from 21–105 units) for the entire
simulation. Equation (12) is never executed in the code that produced the
published results.

This matters because the two behaviours generate very different levels of
aggregate demand:

| Consumption rule | Equilibrium employment |
|---|---|
| Paper's `(m/P)^α` | ~62% |
| Java's `(m/P) · exp(α)` | ~85–93% |
| Java's actual behaviour (never updated, `c ≈ 60`) | matches λ = 3 production |

A further observation: the Java formula is `min((m/P)·exp(α), m/P)`. Since
`exp(0.9) ≈ 2.46 > 1`, the first term always exceeds the second and the `min`
**always selects `m/P`**. The parameter α has no effect whatsoever. The Java
version does not implement a consumption function — it implements "spend all
available liquidity".

This implementation uses the Java formula by default, since it reproduces the
paper's reported behaviour. Switching to the paper's stated equation is a
one-line change in `Household.update_consumption()` and yields a stable but
materially lower-employment equilibrium.

---

## Implementation notes — divergences from the original

Each change below is deliberate. Those marked **bug** correct behaviour in the
Java source that is inconsistent with the paper's text; those marked
**calibration** adjust parameters that do not work with the corrected code;
those marked **extension** address cases the paper does not cover.

| # | Change | Type |
|---|---|---|
| 1 | `mc` set to the firm's wage in `update_price_range` | bug |
| 2 | Wage falls only if previously-open positions were filled | bug |
| 3 | `firm.d` reset at the start of each month | bug |
| 4 | `firm.to_fire` reset after the firing queue is processed | bug |
| 5 | `open_position` decremented when a vacancy is filled | bug |
| 6 | All quantities held as floats | design |
| 7 | Price bounds widened to `φ = 0.01`, `ϕ̄ = 2.0` | calibration |
| 8 | Labour productivity `λ = 1` | calibration |
| 9 | Initial prices drawn from `N(0.05, 0.01)` | calibration |
| 10 | `update_consumption()` is actually called each month | bug |
| 11 | Java's consumption formula retained over the paper's | choice |
| 12 | Household liquidity clamped at zero | bug |
| 13 | Negative aggregate profit is not redistributed | bug |
| 14 | Liquidity buffer topped up per eq. (15), `χ = 0.1` | bug |
| 15 | Firing implemented with a one-month lag | bug |
| 16 | Hiring and firing scale with the inventory gap, capped at 3/month | extension |
| 17 | A firm with no workers always hires and never adjusts price | extension |
| 18 | Off-by-one in `updateTypeA_Quantity`'s selection loop corrected | bug |

### The substantive ones

**2 — wage adjustment.** The Java cuts a firm's wage by 10% whenever
`open_position == 0`, which is also true of a firm that never opened a vacancy.
Stable firms therefore cut wages every month indefinitely, dragging the mean
wage toward zero. The paper (Section 2.2) says wages fall when positions "have
been filled with workers throughout the last γ months", which presupposes
positions existed. Corrected to require that the firm had open positions in the
previous month.

**3 — demand accumulation.** `firm.d` is never reset in the Java, so
`inv_max = Φ̄ · d` grows without bound. The paper defines `d_old` as "the demand
for consumption goods of the most recent month". Reset after each month's
decisions are taken.

**7, 8, 9 — calibration.** Table 1 gives `φ = 0.25`, `ϕ̄ = 1`, `λ = 3`. With
`mc` correctly set to the wage (≈ 1.0), the price floor `φ · mc ≈ 0.25` sits
*above* the initial price of 0.1, so the condition `p > p_min` is never
satisfied and firms can never lower prices. The Java escapes this only because
its uninitialised `mc` defaults to 0.0, making both bounds zero. Widening the
bounds restores the price-decrease mechanism. `λ = 3` produces roughly five
times more output than equation-(12) demand can absorb and collapses the
economy within 50 months; `λ = 1` balances. Initial prices were lowered to sit
nearer the reachable equilibrium.

**15 — firing lag.** Paper Section 2.2: *"hiring decisions lead to an immediate
offering of a new position, while firing decisions are implemented with a lag
of one month."* The Java fires in the same month the decision is taken.
Implemented by draining the firing queue at the start of the following month.

**16 — adjustment speed.** The paper restricts firms to hiring or firing at
most one worker per month (Section 2.2, footnote 18, where the author notes the
assumption "seems restrictive"). The firm's target is a *stock* — inventory
between `1.025·d` and `1.15·d` — but its control variable is a *flow*. One
worker contributes `λ × 21` units of output per month, which is roughly 12% of
a small firm's throughput but only 2% of a large one's.

Large firms consequently cannot reach their inventory target at all. Instrumented
runs showed individual firms below `inv_min` and hiring for **79 consecutive
months**, and in one case 179. Since price increases occur only on the hiring
branch, these firms ratcheted prices upward every month, producing a persistent
economy-wide price drift and a slow decline in employment (98% → 73% over 200
months).

Hiring and firing now scale with the gap, capped at three workers per month in
both directions. Small firms are unaffected (the `max(1, …)` floor preserves the
paper's behaviour); only firms with a gap larger than three workers' output see
any change.

> **On footnote 18.** Lengnick presents the one-worker limit apologetically, as
> a simplification. It is in fact load-bearing. An earlier attempt here used a
> cap *proportional* to firm size (10% of headcount), which interacts with the
> size-weighted customer selection in Section 2.2 to produce an unchecked
> feedback loop: more workers → more customers → higher demand → higher
> inventory target → more hiring. Single firms reached 127 workers, roughly a
> quarter of the workforce, before collapsing and dumping 100+ households into
> unemployment at once. The absolute cap keeps growth linear and bounded.

**17 — zero-worker firms.** A firm that loses all its workers produces nothing,
so its inventory is frozen and it is trapped on whichever side of the band it
landed. Below `inv_min` it hires and raises its price every month forever —
observed reaching 0.2163 against a market price of 0.054. Above `inv_max` it is
worse: the firing branch sets no vacancies, so it never advertises, the labour
market cannot reach it, and it cuts price every month. One such firm held 5,297
units of inventory with no staff.

Around a third of all firms were in this state at any time, with up to 1,600 of
the 7,000 type A links attached to them — demand silently destroyed each month.
Because these firms sat far out in the right tail, they also inflated the mean
price well above the median.

Firms with no workers now always hire and skip price adjustment entirely. The
zombie population fell from ~33 to ~12 and became self-clearing, and mean,
median and live-firm prices converged to within 1%.

The paper does not anticipate this case. Section 2.1 assumes firms are "fixed
in number and infinitely lived", and the emergency wage-cut mechanism in
Section 2.4 exists specifically so that firm entry and exit can be neglected —
but it guards against bankruptcy, not against a firm simply emptying out.

---

## What the model reproduces

| Paper result | Status |
|---|---|
| Endogenous business cycles (Fig. 4) | Yes — employment oscillates with no imposed shock |
| Sawtooth household/firm liquidity (Fig. 7) | Yes — clean mirror-image cycle, money conserved |
| Right-skewed firm size distribution (Fig. 6) | Yes — skewness ~1.5–1.8 (paper: 1.88) |
| Phillips curve (Fig. 5, left) | Yes — clear downward slope |
| Beveridge curve (Fig. 5, right) | Yes, with a visible matching-friction cluster |
| Price competition compressing dispersion | Yes — std dev falls ~45% over 200 months |
| Employment 95.7–100% | Partially — settles ~87–91% |

Price dispersion across firms falls steadily as households rewire toward cheaper
suppliers, which is the mechanism Section 3 describes: *"competition drives the
economy to a point where prices are set in such a way that they reflect the true
relative scarcity of commodities."*

---

## Known limitations

**Equilibrium employment sits below the paper's range.** Roughly 87–91% against
95.7–100%. The remaining gap is not explained.

**Residual overstock.** Firms that lose customers faster than they can shed
workers accumulate large inventories — one observed at 9,655 units against
monthly demand of 296. The three-per-month firing cap means unwinding takes
years. Same stock-versus-flow shape as divergence 16, smaller in magnitude.

**Single-seed results.** The figures quoted above come from individual runs at
`seed = 1`. Nothing here has been validated across seeds, and the model is
demonstrably sensitive to initial conditions — which is, after all, one of the
paper's own findings (Section 5).

**Not yet implemented.** Section 4 (monetary policy: helicopter drops, long-run
neutrality, impulse responses) and Section 5 (the butterfly-effect experiments).

---

## Calibration

| Parameter | Symbol | Value | Source |
|---|---|---|---|
| Households | H | 1000 | paper |
| Firms | F | 100 | paper |
| Type A connections | n | 7 | paper |
| Consumption parameter | α | 0.9 | paper |
| Wage adjustment | δ | 0.019 | paper |
| Inventory bounds | Φ, Φ̄ | 1.025, 1.15 | paper |
| Price bounds | φ, ϕ̄ | 0.01, 2.0 | **changed** (paper: 0.25, 1) |
| Price adjustment | ϑ | 0.02 | paper |
| Price change probability | θ | 0.75 | paper |
| Productivity | λ | 1 | **changed** (paper: 3) |
| Buffer ratio | χ | 0.1 | paper |
| Months before wage rise | γ | 24 | paper |
| Search intensity (unemployed) | β | 5 | paper |
| Search probability (employed) | π | 0.1 | paper |
| Price search threshold | ξ | 0.01 | paper |
| Rewiring probabilities | Ψ_price, Ψ_quant | 0.25, 0.25 | paper |

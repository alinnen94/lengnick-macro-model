"""Instrumented run — shows what firms are actually deciding each month."""

from model import LengnickModel
import statistics

N_MONTHS = 200
LOG_EVERY = 10

model = LengnickModel()

print(f"Running {N_MONTHS} months with instrumentation…\n")
print("HIRE/FIRE/NONE = firms per branch   UP/DOWN = price changes executed")
print("BLK = blocked by price bound   VAC = created/filled   inv/d = inventory vs monthly demand\n")

for month in range(1, N_MONTHS + 1):
    for _ in range(21):
        model.step()

    if month % LOG_EVERY != 0:
        continue

    d = model.diag
    employed = sum(1 for hh in model.households if hh.employed)

    prices = [f.p for f in model.firms]
    mean_p = sum(prices) / len(prices)
    med_p = statistics.median(prices)

    runs = [f.branch_run for f in model.firms]
    hire_runs = [r for r in runs if r > 0]
    fire_runs = [-r for r in runs if r < 0]
    mean_hire = sum(hire_runs) / len(hire_runs) if hire_runs else 0
    mean_fire = sum(fire_runs) / len(fire_runs) if fire_runs else 0
    max_hire = max(hire_runs) if hire_runs else 0
    max_fire = max(fire_runs) if fire_runs else 0

    # zombies: no workers at all
    zombies = [f for f in model.firms if len(f.typeB) == 0]
    zombie_customers = sum(len(f.typeA) for f in zombies)

    # price level excluding zombies — the "working economy" price
    live_prices = [f.p for f in model.firms if len(f.typeB) > 0]
    live_mean_p = sum(live_prices) / len(live_prices) if live_prices else float("nan")

    below = sum(1 for f in model.firms if f.d > 0 and f.inv < 1.025 * f.d)
    above = sum(1 for f in model.firms if f.d > 0 and f.inv > 1.15 * f.d)

    print(
        f"M{month:>4} | Emp {employed:>4} | "
        f"P mean {mean_p:.4f} med {med_p:.4f} live {live_mean_p:.4f} | "
        f"HIRE {d['hire_branch']:>3} FIRE {d['fire_branch']:>3} NONE {d['no_branch']:>3} | "
        f"runs H {mean_hire:>5.1f}/{max_hire:>3} F {mean_fire:>5.1f}/{max_fire:>3} | "
        f"below {below:>3} above {above:>3} | "
        f"zombies {len(zombies):>3} (cust {zombie_customers:>4})"
    )

    # worst offenders in each direction
    worst_hire = max(model.firms, key=lambda f: f.branch_run)
    worst_fire = min(model.firms, key=lambda f: f.branch_run)
    for label, f in (("H", worst_hire), ("F", worst_fire)):
        if f.branch_run == 0:
            continue
        ratio = f.inv / f.d if f.d > 0 else float("nan")
        print(f"       {label} run {abs(f.branch_run):>3} | workers {len(f.typeB):>3} "
              f"| customers {len(f.typeA):>4} | d {f.d:>7.0f} | inv {f.inv:>8.0f} "
              f"| inv/d {ratio:>6.2f} | p {f.p:.4f} | open {f.open_position:>3}")
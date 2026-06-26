from model import LengnickModel

model = LengnickModel()

for month in range(1, 6):
    for _ in range(21):
        model.step()

    # diagnostic: what's actually going on inside the firms?
    total_d = sum(f.d for f in model.firms)
    total_inv = sum(f.inv for f in model.firms)
    total_open = sum(f.open_position for f in model.firms)
    total_to_fire = sum(f.to_fire for f in model.firms)
    firms_with_workers = sum(1 for f in model.firms if len(f.typeB) > 0)
    firms_with_zero_workers = sum(1 for f in model.firms if len(f.typeB) == 0)
    total_hh_liquidity = sum(hh.m for hh in model.households)
    mean_household_c = sum(hh.c for hh in model.households) / model.H
    employed_hh = sum(1 for hh in model.households if hh.employed)

    print(f"\n=== Month {month} ===")
    print(f"Employed households:        {employed_hh}/{model.H}")
    print(f"Firms with workers:         {firms_with_workers}")
    print(f"Firms with zero workers:    {firms_with_zero_workers}")
    print(f"Total demand (sum of f.d):  {total_d}")
    print(f"Total inventory:            {total_inv}")
    print(f"Total open positions:       {total_open}")
    print(f"Total queued firings:       {total_to_fire}")
    print(f"Total household liquidity:  {total_hh_liquidity:.2f}")
    print(f"Mean household c (planned): {mean_household_c:.2f}")

from model import LengnickModel

model = LengnickModel()

for month in range(1, 101):
    for _ in range(21):
        model.step()

    # only log every 5 months
    if month % 5 == 0:
        employed_hh = sum(1 for hh in model.households if hh.employed)
        mean_p = sum(f.p for f in model.firms) / model.F
        mean_w = sum(f.w for f in model.firms) / model.F
        total_inv = sum(f.inv for f in model.firms)
        total_open = sum(f.open_position for f in model.firms)
        mean_c = sum(hh.c for hh in model.households) / model.H

        print(f"Month {month:>3} | "
              f"Emp: {employed_hh:>4}/1000 | "
              f"Wage: {mean_w:>6.4f} | "
              f"Price: {mean_p:>6.4f} | "
              f"Inv: {total_inv:>9.0f} | "
              f"Open: {total_open:>3} | "
              f"c̄: {mean_c:>5.2f}")

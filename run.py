from model import LengnickModel

model = LengnickModel()

# print basic initialisation stats
total_employed = sum(1 for hh in model.households if hh.employed)
total_typeA = sum(len(f.typeA) for f in model.firms)
total_typeB = sum(len(f.typeB) for f in model.firms)

print(f"Households:      {model.H}")
print(f"Firms:           {model.F}")
print(f"Employed HH:     {total_employed}")
print(f"TypeA links:     {total_typeA}  (expect {model.H * model.num_typeA})")
print(f"TypeB links:     {total_typeB}  (expect ~{model.H})")
print(f"Employment rate: {model._get_employment_rate():.1f}%")
print(f"Mean price:      {model._get_mean_price():.4f}")
print(f"Mean wage:       {model._get_mean_wage():.4f}")
print("\nInitialisation successful.")

"""
Entry point for the Lengnick (2013) ABM.

Set MODE below, then press the Run button in VS Code (or F5).

    MODE = "ui"          -> launches the Streamlit dashboard in your browser
    MODE = "diagnostic"  -> runs headless and prints a summary every 5 months

Command-line arguments still work if you prefer the terminal:
    python run.py ui
    python run.py 500        (500-month diagnostic)
"""

import sys
import subprocess

# ----------------------------------------------------------------------
# Configuration — edit these, then hit Run
# ----------------------------------------------------------------------
MODE = "ui"          # "ui" or "diagnostic"
N_MONTHS = 100       # only used in diagnostic mode
LOG_EVERY = 5        # print a line every N months


# ----------------------------------------------------------------------
# Command-line overrides (optional)
# ----------------------------------------------------------------------
if len(sys.argv) > 1:
    arg = sys.argv[1].lower()
    if arg == "ui":
        MODE = "ui"
    elif arg == "diagnostic":
        MODE = "diagnostic"
    elif arg.isdigit():
        MODE = "diagnostic"
        N_MONTHS = int(arg)


# ----------------------------------------------------------------------
# UI mode — launch Streamlit
# ----------------------------------------------------------------------
if MODE == "ui":
    print("Launching Streamlit dashboard… (Ctrl+C in this terminal to stop)")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "server.py"])
    sys.exit()


# ----------------------------------------------------------------------
# Diagnostic mode — headless run with periodic printouts
# ----------------------------------------------------------------------
from model import LengnickModel

model = LengnickModel()

print(f"Running {N_MONTHS} months ({N_MONTHS * 21} steps)…\n")

for month in range(1, N_MONTHS + 1):
    for _ in range(21):
        model.step()

    if month % LOG_EVERY == 0:
        employed_hh = sum(1 for hh in model.households if hh.employed)
        mean_p = sum(f.p for f in model.firms) / model.F
        mean_w = sum(f.w for f in model.firms) / model.F
        total_inv = sum(f.inv for f in model.firms)
        total_open = sum(f.open_position for f in model.firms)
        mean_c = sum(hh.c for hh in model.households) / model.H

        print(f"Month {month:>4} | "
              f"Emp: {employed_hh:>4}/{model.H} | "
              f"Wage: {mean_w:>6.4f} | "
              f"Price: {mean_p:>6.4f} | "
              f"Inv: {total_inv:>9.0f} | "
              f"Open: {total_open:>4} | "
              f"c̄: {mean_c:>5.2f}")

print("\nDone.")
# test.py - Provjera da Python + pandas rade

import pandas as pd
import matplotlib
import tabulate

print("=" * 50)
print("Python okruženje radi!")
print("=" * 50)
print(f"Pandas verzija:     {pd.__version__}")
print(f"Matplotlib verzija: {matplotlib.__version__}")
print(f"Tabulate verzija:   {tabulate.__version__}")
print("=" * 50)
print()
print("Sve je spremno za analizu CSV-a.")
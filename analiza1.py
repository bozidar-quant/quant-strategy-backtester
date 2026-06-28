# analiza1.py - prvi pogled na podatke

import pandas as pd

# Učitaj H1 signale
df = pd.read_csv('BreakoutScanner_log.csv')

print("=" * 60)
print(f"Ukupno signala: {len(df)}")
print("=" * 60)
print()

# Pokaži prvih 5 redova
print("Prvih 5 signala:")
print(df.head())
print()

# Pokaži kolone
print("Kolone u CSV-u:")
print(df.columns.tolist())
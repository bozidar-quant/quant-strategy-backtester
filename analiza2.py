# analiza2.py - osnovna statistika signala

import pandas as pd

df = pd.read_csv('BreakoutScanner_log.csv')

print("=" * 60)
print(f"UKUPNO SIGNALA: {len(df)}")
print("=" * 60)
print()

# 1. Smjer signala
print("RASPODJELA PO SMJERU:")
print(df['Direction'].value_counts())
print()

# 2. Po paru
print("BROJ SIGNALA PO PARU:")
print(df['Instrument'].value_counts())
print()

# 3. Score statistika
print("STATISTIKA SCORE-A:")
print(df['Score'].describe())
print()

# 4. Strike statistika
print("STATISTIKA STRIKE PIPS-a:")
print(df['Strike'].describe())
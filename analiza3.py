# analiza3.py - cross-tabulacija

import pandas as pd

df = pd.read_csv('BreakoutScanner_log.csv')

# Pretvori Timestamp u datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Izvuci sat iz timestamp-a
df['Hour'] = df['Timestamp'].dt.hour

print("=" * 60)
print("SIGNALI PO SATU DANA (UTC):")
print("=" * 60)
print(df['Hour'].value_counts().sort_index())
print()

print("=" * 60)
print("SCORE PO SMJERU:")
print("=" * 60)
print(df.groupby('Direction')['Score'].describe())
print()

print("=" * 60)
print("STRIKE PIPS PO PARU (prosjek):")
print("=" * 60)
print(df.groupby('Instrument')['Strike'].mean().sort_values(ascending=False))
print()

print("=" * 60)
print("STRIKE PO SCORE BUCKETU:")
print("=" * 60)
df['ScoreBucket'] = pd.cut(df['Score'].abs(), 
                           bins=[0, 6, 7, 8, 9, 10, 100], 
                           labels=['<6', '6', '7', '8', '9', '10+'])
print(df.groupby('ScoreBucket', observed=True)['Strike'].agg(['mean', 'count']))
# analiza4.py - filter konkretnog signala

import pandas as pd

df = pd.read_csv('BreakoutScanner_log.csv')

# Filter samo GBPNZD
gbpnzd = df[df['Instrument'] == 'GBPNZD']
print("=" * 60)
print("GBPNZD SIGNALI:")
print("=" * 60)
print(gbpnzd.to_string())
print()

# Najveće strike signali (top 5)
print("=" * 60)
print("TOP 5 PO STRIKE-U:")
print("=" * 60)
top_strike = df.nlargest(5, 'Strike')
print(top_strike[['Timestamp', 'Instrument', 'Direction', 'Score', 'ADX', 'ATR_Percentile', 'Strike']].to_string())
print()

# Najmanje strike signali (top 5)
print("=" * 60)
print("TOP 5 PO NAJMANJEM STRIKE-U:")
print("=" * 60)
small_strike = df.nsmallest(5, 'Strike')
print(small_strike[['Timestamp', 'Instrument', 'Direction', 'Score', 'ADX', 'ATR_Percentile', 'Strike']].to_string())
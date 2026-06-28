# analiza5.py - vremenska analiza signala

import pandas as pd

df = pd.read_csv('BreakoutScanner_log.csv')

# Pretvori Timestamp u datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Izračunaj settlement vrijeme za svaki signal
# Settlement je u 21:00 GMT ISTI dan ako signal prije 21:00, INAČE sljedeći dan
def calculate_settlement(ts):
    settlement = ts.replace(hour=21, minute=0, second=0, microsecond=0)
    if ts >= settlement:
        settlement += pd.Timedelta(days=1)
    # Preskoči vikend (subota=5, nedjelja=6)
    while settlement.weekday() >= 5:
        settlement += pd.Timedelta(days=1)
    return settlement

df['Settlement'] = df['Timestamp'].apply(calculate_settlement)
df['HoursToSettlement'] = (df['Settlement'] - df['Timestamp']).dt.total_seconds() / 3600
df['PipsPerHour'] = df['Strike'] / df['HoursToSettlement']

# Pokazuj zaobljeno
pd.set_option('display.float_format', '{:.2f}'.format)

print("=" * 70)
print("PIPS-PER-HOUR ANALIZA (manji = lakše za touch):")
print("=" * 70)

# Top 5 najtežih (najveći pips/hour zahtjev)
print("\nTOP 5 NAJTEŽIH (najviše pipsa po satu):")
top_hard = df.nlargest(5, 'PipsPerHour')
print(top_hard[['Timestamp', 'Instrument', 'Direction', 'Score', 'Strike', 'HoursToSettlement', 'PipsPerHour']].to_string())

# Top 5 najlakših
print("\nTOP 5 NAJLAKŠIH (najmanje pipsa po satu):")
top_easy = df.nsmallest(5, 'PipsPerHour')
print(top_easy[['Timestamp', 'Instrument', 'Direction', 'Score', 'Strike', 'HoursToSettlement', 'PipsPerHour']].to_string())

# Statistika
print("\n" + "=" * 70)
print("PIPS/HOUR STATISTIKA:")
print("=" * 70)
print(df['PipsPerHour'].describe())

# Po paru
print("\n" + "=" * 70)
print("PROSJEČAN PIPS/HOUR PO PARU:")
print("=" * 70)
print(df.groupby('Instrument')['PipsPerHour'].mean().sort_values(ascending=False))
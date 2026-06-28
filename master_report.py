"""
master_report.py — Krvna slika Breakout Trading System-a
VERZIJA 2: sa win rate analizom, MAE/MFE, strike bucket analizom
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, 
                                  PageBreak, Table, TableStyle, KeepTogether)

OUTPUT_DIR = '.'
TODAY = datetime.now().strftime('%Y-%m-%d_%H%M')
PDF_FILENAME = f'BreakoutReport_{TODAY}.pdf'

COLOR_PRIMARY = HexColor('#1a5490')
COLOR_ACCENT = HexColor('#26c6da')
COLOR_GOOD = HexColor('#43a047')
COLOR_BAD = HexColor('#e53935')
COLOR_WARN = HexColor('#fb8c00')
COLOR_NEUTRAL = HexColor('#757575')

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 100

# ═══════════════════════════════════════════════════
def load_data():
    data = {}
    files = {
        'h1_log': 'BreakoutScanner_log.csv',
        'h1_out': 'BreakoutScanner_outcomes.csv',
        'm15_log': 'BreakoutScanner_M15_log.csv',
        'm15_out': 'BreakoutScanner_M15_outcomes.csv'
    }
    for key, fname in files.items():
        if os.path.exists(fname):
            try:
                df = pd.read_csv(fname)
                if len(df) > 0:
                    if 'Timestamp' in df.columns:
                        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                    if 'SignalTime' in df.columns:
                        df['SignalTime'] = pd.to_datetime(df['SignalTime'])
                data[key] = df
                print(f"OK Učitan {fname}: {len(df)} redaka")
            except Exception as e:
                print(f"X Greška kod {fname}: {e}")
                data[key] = pd.DataFrame()
        else:
            data[key] = pd.DataFrame()
            print(f"X Ne postoji: {fname}")
    return data

def enrich_log(df):
    if df.empty: return df
    df = df.copy()
    df['Hour'] = df['Timestamp'].dt.hour
    df['Date'] = df['Timestamp'].dt.date
    
    def calc_settlement(ts):
        s = ts.replace(hour=21, minute=0, second=0, microsecond=0)
        if ts >= s:
            s += pd.Timedelta(days=1)
        while s.weekday() >= 5:
            s += pd.Timedelta(days=1)
        return s
    
    df['Settlement'] = df['Timestamp'].apply(calc_settlement)
    df['HoursToSettlement'] = (df['Settlement'] - df['Timestamp']).dt.total_seconds() / 3600
    df['PipsPerHour'] = df['Strike'] / df['HoursToSettlement']
    df['AbsScore'] = df['Score'].abs()
    return df

def enrich_outcomes(df):
    if df.empty: return df
    df = df.copy()
    df['Hour'] = df['SignalTime'].dt.hour
    df['AbsScore'] = df['Score'].abs()
    return df

# ═══════════════════════════════════════════════════
# GRAFOVI - LOG ANALIZA
# ═══════════════════════════════════════════════════
def chart_signals_per_hour(df, filename):
    if df.empty: return
    plt.figure(figsize=(8, 4))
    counts = df['Hour'].value_counts().sort_index()
    colors = ['#26c6da' if 8 <= h <= 17 else '#757575' for h in counts.index]
    plt.bar(counts.index, counts.values, color=colors)
    plt.xlabel('Sat (UTC)')
    plt.ylabel('Broj signala')
    plt.title('Distribucija signala po satu dana')
    plt.xticks(range(0, 24))
    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()

def chart_score_distribution(df, filename):
    if df.empty: return
    plt.figure(figsize=(8, 4))
    plt.hist(df['Score'], bins=range(-12, 13), color='#1a5490', edgecolor='white')
    plt.axvline(x=6, color='#43a047', linestyle='--', label='Threshold +6')
    plt.axvline(x=-6, color='#e53935', linestyle='--', label='Threshold -6')
    plt.xlabel('Score')
    plt.ylabel('Broj signala')
    plt.title('Distribucija Score-a')
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()

def chart_pipsperhour_distribution(df, filename):
    if df.empty: return
    plt.figure(figsize=(8, 4))
    plt.hist(df['PipsPerHour'], bins=20, color='#26c6da', edgecolor='white')
    plt.axvline(x=1.5, color='#43a047', linestyle='--', label='Lako (<1.5)')
    plt.axvline(x=3.5, color='#e53935', linestyle='--', label='Teško (>3.5)')
    plt.xlabel('Pips per Hour (zahtjev)')
    plt.ylabel('Broj signala')
    plt.title('Distribucija težine signala (pip/h)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()

def chart_signals_by_pair(df, filename):
    if df.empty: return
    plt.figure(figsize=(8, 5))
    counts = df['Instrument'].value_counts().sort_values()
    plt.barh(counts.index, counts.values, color='#1a5490')
    plt.xlabel('Broj signala')
    plt.title('Signali po valutnom paru')
    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()

# ═══════════════════════════════════════════════════
# GRAFOVI - OUTCOMES
# ═══════════════════════════════════════════════════
def chart_outcome_pie(df, filename, title):
    if df.empty: return
    counts = df['Result'].value_counts()
    colors_map = {'WIN': '#43a047', 'LOSS': '#e53935', 'REFUND': '#fb8c00'}
    colors = [colors_map.get(r, '#757575') for r in counts.index]
    plt.figure(figsize=(6, 6))
    plt.pie(counts.values, labels=[f'{r}\n({c} - {c/len(df)*100:.1f}%)' for r, c in counts.items()],
            colors=colors, startangle=90, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
    plt.title(title)
    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()

def chart_winrate_by_pair(df, filename):
    if df.empty: return
    pair_results = df.groupby('Instrument')['Result'].value_counts().unstack(fill_value=0)
    for col in ['WIN', 'LOSS', 'REFUND']:
        if col not in pair_results.columns: pair_results[col] = 0
    pair_results['Total'] = pair_results['WIN'] + pair_results['LOSS'] + pair_results['REFUND']
    pair_results = pair_results[pair_results['Total'] >= 2]
    if len(pair_results) == 0: return
    pair_results['WinRate'] = (pair_results['WIN'] / pair_results['Total'] * 100)
    pair_results = pair_results.sort_values('WinRate')
    
    plt.figure(figsize=(8, max(4, len(pair_results)*0.35)))
    colors = ['#e53935' if wr < 52.6 else '#43a047' for wr in pair_results['WinRate']]
    plt.barh(pair_results.index, pair_results['WinRate'], color=colors)
    plt.axvline(x=52.6, color='black', linestyle='--', label='Breakeven (52.6%)')
    plt.xlabel('Win Rate (%)')
    plt.title('Win Rate po paru (samo >= 2 outcome)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()

def chart_winrate_by_strike(df, filename):
    if df.empty: return
    df_c = df.copy()
    df_c['StrikeBucket'] = pd.cut(df_c['Strike'], 
                                    bins=[0, 12, 18, 25, 100], 
                                    labels=['<=12p', '13-18p', '19-25p', '>25p'])
    by_strike = df_c.groupby('StrikeBucket', observed=True)['Result'].value_counts().unstack(fill_value=0)
    for col in ['WIN', 'LOSS', 'REFUND']:
        if col not in by_strike.columns: by_strike[col] = 0
    by_strike['Total'] = by_strike['WIN'] + by_strike['LOSS'] + by_strike['REFUND']
    by_strike['WR%'] = (by_strike['WIN'] / by_strike['Total'] * 100)
    by_strike['Refund%'] = (by_strike['REFUND'] / by_strike['Total'] * 100)
    
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(by_strike))
    width = 0.35
    ax.bar(x - width/2, by_strike['WR%'], width, label='Win Rate %', color='#43a047')
    ax.bar(x + width/2, by_strike['Refund%'], width, label='Refund Rate %', color='#fb8c00')
    ax.axhline(y=52.6, color='black', linestyle='--', alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(by_strike.index)
    ax.set_xlabel('Strike bucket')
    ax.set_ylabel('%')
    ax.set_title('Win Rate i Refund Rate po Strike bucketu')
    ax.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()

def chart_mae_mfe(df, filename):
    if df.empty: return
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for i, result in enumerate(['WIN', 'LOSS', 'REFUND']):
        subset = df[df['Result']==result]
        if len(subset) == 0:
            axes[i].text(0.5, 0.5, 'Nema podataka', ha='center', va='center')
            axes[i].set_title(result)
            continue
        axes[i].scatter(subset['MAE_pips'], subset['MFE_pips'], 
                       color={'WIN':'#43a047','LOSS':'#e53935','REFUND':'#fb8c00'}[result],
                       s=60, alpha=0.7, edgecolors='white')
        axes[i].set_xlabel('MAE (pips)')
        axes[i].set_ylabel('MFE (pips)')
        axes[i].set_title(f'{result} (n={len(subset)})')
        axes[i].plot([0, max(subset['MAE_pips'].max(), subset['MFE_pips'].max())],
                    [0, max(subset['MAE_pips'].max(), subset['MFE_pips'].max())],
                    'k--', alpha=0.3, label='MAE=MFE')
        axes[i].legend()
    plt.suptitle('MAE vs MFE po outcome-u (kako se cijena ponašala)')
    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()

# ═══════════════════════════════════════════════════
def make_paragraph_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Title2', parent=styles['Heading1'],
        fontSize=20, textColor=COLOR_PRIMARY,
        spaceAfter=12, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        name='Section', parent=styles['Heading1'],
        fontSize=14, textColor=COLOR_PRIMARY,
        spaceBefore=18, spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name='Subsection', parent=styles['Heading2'],
        fontSize=11, textColor=COLOR_ACCENT,
        spaceBefore=10, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name='BodyTxt', parent=styles['BodyText'],
        fontSize=10, leading=14, alignment=TA_JUSTIFY
    ))
    styles.add(ParagraphStyle(
        name='Finding', parent=styles['BodyText'],
        fontSize=10, leading=14,
        leftIndent=20, bulletIndent=10, spaceAfter=6
    ))
    return styles

def df_to_table(df, max_rows=10):
    df = df.head(max_rows).copy()
    df = df.round(2)
    data = [df.columns.tolist()] + df.values.tolist()
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_NEUTRAL),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f5f5f5'), white]),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t

def winrate_table(df):
    """Build win rate per pair table."""
    pair_results = df.groupby('Instrument')['Result'].value_counts().unstack(fill_value=0)
    for col in ['WIN', 'LOSS', 'REFUND']:
        if col not in pair_results.columns: pair_results[col] = 0
    pair_results['Total'] = pair_results['WIN'] + pair_results['LOSS'] + pair_results['REFUND']
    pair_results['WR%'] = (pair_results['WIN'] / pair_results['Total'] * 100).round(1)
    pair_results = pair_results.sort_values('Total', ascending=False).reset_index()
    return pair_results[['Instrument', 'WIN', 'LOSS', 'REFUND', 'Total', 'WR%']]

def generate_pdf(data):
    h1 = enrich_log(data['h1_log'])
    m15 = enrich_log(data['m15_log'])
    h1_out = enrich_outcomes(data['h1_out'])
    m15_out = enrich_outcomes(data['m15_out'])
    combined_out = pd.concat([h1_out, m15_out], ignore_index=True) if not h1_out.empty or not m15_out.empty else pd.DataFrame()
    
    styles = make_paragraph_styles()
    
    # Generiraj grafove
    if not h1.empty:
        chart_signals_per_hour(h1, 'tmp_h1_hours.png')
        chart_score_distribution(h1, 'tmp_h1_score.png')
        chart_pipsperhour_distribution(h1, 'tmp_h1_pph.png')
        chart_signals_by_pair(h1, 'tmp_h1_pairs.png')
    if not m15.empty:
        chart_signals_per_hour(m15, 'tmp_m15_hours.png')
    if not combined_out.empty:
        chart_outcome_pie(combined_out, 'tmp_pie_combined.png', 'Kombinirano (H1+M15)')
        chart_winrate_by_pair(combined_out, 'tmp_wr_pair.png')
        chart_winrate_by_strike(combined_out, 'tmp_wr_strike.png')
        chart_mae_mfe(combined_out, 'tmp_mae_mfe.png')
    if not h1_out.empty:
        chart_outcome_pie(h1_out, 'tmp_pie_h1.png', 'H1 Scanner outcomes')
    if not m15_out.empty:
        chart_outcome_pie(m15_out, 'tmp_pie_m15.png', 'M15 Scanner outcomes')
    
    doc = SimpleDocTemplate(PDF_FILENAME, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    story = []
    
    # ═══ NASLOV ═══
    story.append(Paragraph("BREAKOUT TRADING SYSTEM", styles['Title2']))
    story.append(Paragraph("Krvna slika sustava", styles['Heading3']))
    story.append(Paragraph(f"Generirano: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['BodyTxt']))
    story.append(Spacer(1, 0.5*cm))
    
    # ═══ §1 EXECUTIVE SUMMARY ═══
    story.append(Paragraph("§1. Executive Summary", styles['Section']))
    
    total_h1 = len(h1)
    total_m15 = len(m15)
    total_out_h1 = len(h1_out)
    total_out_m15 = len(m15_out)
    
    period_start = h1['Timestamp'].min().strftime('%d.%m.%Y') if not h1.empty else 'N/A'
    period_end = h1['Timestamp'].max().strftime('%d.%m.%Y') if not h1.empty else 'N/A'
    
    summary = f"""
    <b>Period prikupljanja:</b> {period_start} – {period_end}<br/>
    <b>Ukupno signala:</b> {total_h1 + total_m15} ({total_h1} H1 + {total_m15} M15)<br/>
    <b>Evaluiranih outcomes:</b> {total_out_h1 + total_out_m15} ({total_out_h1} H1 + {total_out_m15} M15)<br/>
    """
    story.append(Paragraph(summary, styles['BodyTxt']))
    
    if not combined_out.empty:
        wr = (combined_out['Result']=='WIN').sum() / len(combined_out) * 100
        lr = (combined_out['Result']=='LOSS').sum() / len(combined_out) * 100
        rr = (combined_out['Result']=='REFUND').sum() / len(combined_out) * 100
        
        wr_color = '#43a047' if wr >= 52.6 else '#e53935'
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"""
        <b>WIN RATE (kombinirano):</b> <font color='{wr_color}'><b>{wr:.1f}%</b></font>
         (breakeven target: 52.6%)<br/>
        <b>LOSS RATE:</b> {lr:.1f}% | <b>REFUND RATE:</b> {rr:.1f}%<br/>
        """, styles['BodyTxt']))
        
        # Note on sample size
        if len(combined_out) < 50:
            story.append(Paragraph(f"""
            <i>⚠ Sample size od {len(combined_out)} outcomes je premali za čvrste zaključke. 
            Treba 50+ za pouzdanu statistiku.</i>
            """, styles['BodyTxt']))
    
    if not h1.empty:
        avg_pph = h1['PipsPerHour'].mean()
        median_pph = h1['PipsPerHour'].median()
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"""
        <b>H1 Scanner brojke:</b><br/>
        • Prosječan score: {h1['Score'].mean():+.2f} (abs: {h1['AbsScore'].mean():.2f})<br/>
        • Prosječan strike: {h1['Strike'].mean():.1f} pips<br/>
        • Prosječan pips/hour: {avg_pph:.2f} (median: {median_pph:.2f})<br/>
        • BUY: {(h1['Direction']=='BUY').sum()} | SELL: {(h1['Direction']=='SELL').sum()}<br/>
        """, styles['BodyTxt']))
    
    if not m15.empty:
        story.append(Paragraph(f"""
        <b>M15 Scanner brojke:</b><br/>
        • Prosječan score: {m15['Score'].mean():+.2f}<br/>
        • Prosječan strike: {m15['Strike'].mean():.1f} pips<br/>
        • Prosječan pips/hour: {m15['PipsPerHour'].mean():.2f}<br/>
        • BUY: {(m15['Direction']=='BUY').sum()} | SELL: {(m15['Direction']=='SELL').sum()}<br/>
        """, styles['BodyTxt']))
    
    story.append(PageBreak())
    
    # ═══ §2 OUTCOMES OVERVIEW ═══
    if not combined_out.empty:
        story.append(Paragraph("§2. Outcomes Pregled", styles['Section']))
        
        story.append(Paragraph("2.1 Kombinirana raspodjela", styles['Subsection']))
        story.append(Image('tmp_pie_combined.png', width=10*cm, height=10*cm))
        
        if not h1_out.empty and not m15_out.empty:
            story.append(PageBreak())
            story.append(Paragraph("2.2 H1 vs M15 raspodjela", styles['Subsection']))
            
            # Side-by-side approach: stack images
            story.append(Paragraph("<b>H1 Scanner:</b>", styles['BodyTxt']))
            story.append(Image('tmp_pie_h1.png', width=8*cm, height=8*cm))
            story.append(Paragraph("<b>M15 Scanner:</b>", styles['BodyTxt']))
            story.append(Image('tmp_pie_m15.png', width=8*cm, height=8*cm))
        
        story.append(PageBreak())
        
        # Win Rate po paru
        story.append(Paragraph("2.3 Win Rate po paru", styles['Subsection']))
        story.append(Paragraph("""
        Zelena = iznad breakeven-a (52.6%). Crvena = ispod. Prikazani samo parovi 
        s 2+ outcomes.
        """, styles['BodyTxt']))
        if os.path.exists('tmp_wr_pair.png'):
            story.append(Image('tmp_wr_pair.png', width=15*cm, height=10*cm))
        
        story.append(PageBreak())
        
        # Win Rate tablica
        story.append(Paragraph("2.4 Tablica win rate po paru", styles['Subsection']))
        wr_table_data = winrate_table(combined_out)
        story.append(df_to_table(wr_table_data, max_rows=20))
        
        story.append(PageBreak())
        
        # Strike bucket analiza
        story.append(Paragraph("2.5 Strike bucket analiza", styles['Subsection']))
        story.append(Paragraph("""
        Kritično: <b>što veći strike, to veći refund rate.</b> Cijena se ne pomakne 
        dovoljno da hit-uje barijeru ni s jedne strane.
        """, styles['BodyTxt']))
        if os.path.exists('tmp_wr_strike.png'):
            story.append(Image('tmp_wr_strike.png', width=15*cm, height=7.5*cm))
        
        story.append(PageBreak())
        
        # MAE vs MFE
        story.append(Paragraph("2.6 MAE vs MFE analiza", styles['Subsection']))
        story.append(Paragraph("""
        <b>MAE</b> (Maximum Adverse Excursion) = najveći gubitak prije settlement-a.<br/>
        <b>MFE</b> (Maximum Favorable Excursion) = najveći dobitak prije settlement-a.<br/>
        Kod WIN signala MFE mora biti >= strike. Kod LOSS signala MAE >= strike.<br/>
        REFUND znači da ni jedan ni drugi nije bio dosegnut.
        """, styles['BodyTxt']))
        if os.path.exists('tmp_mae_mfe.png'):
            story.append(Image('tmp_mae_mfe.png', width=16*cm, height=5.5*cm))
        
        # MAE/MFE summary
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("<b>MAE/MFE prosjeci:</b>", styles['BodyTxt']))
        for result in ['WIN', 'LOSS', 'REFUND']:
            subset = combined_out[combined_out['Result']==result]
            if len(subset) > 0:
                story.append(Paragraph(
                    f"• <b>{result}</b>: MAE prosjek = {subset['MAE_pips'].mean():.1f}p | "
                    f"MFE prosjek = {subset['MFE_pips'].mean():.1f}p | n = {len(subset)}",
                    styles['BodyTxt']
                ))
        
        story.append(PageBreak())
    
    # ═══ §3 H1 SCANNER ═══
    if not h1.empty:
        story.append(Paragraph("§3. H1 Scanner - Signal Analiza", styles['Section']))
        
        story.append(Paragraph("3.1 Distribucija po satu", styles['Subsection']))
        story.append(Image('tmp_h1_hours.png', width=15*cm, height=7.5*cm))
        
        story.append(Paragraph("3.2 Distribucija Score-a", styles['Subsection']))
        story.append(Image('tmp_h1_score.png', width=15*cm, height=7.5*cm))
        
        story.append(PageBreak())
        story.append(Paragraph("3.3 Pips per Hour distribucija", styles['Subsection']))
        story.append(Image('tmp_h1_pph.png', width=15*cm, height=7.5*cm))
        
        story.append(Paragraph("3.4 Signali po paru", styles['Subsection']))
        story.append(Image('tmp_h1_pairs.png', width=15*cm, height=8*cm))
        
        story.append(PageBreak())
    
    # ═══ §4 M15 ═══
    if not m15.empty:
        story.append(Paragraph("§4. M15 Scanner - Signal Analiza", styles['Section']))
        story.append(Paragraph("4.1 Distribucija po satu", styles['Subsection']))
        story.append(Image('tmp_m15_hours.png', width=15*cm, height=7.5*cm))
        story.append(PageBreak())
    
    # ═══ §5 KEY FINDINGS ═══
    story.append(Paragraph("§5. Ključni nalazi i preporuke", styles['Section']))
    
    findings = []
    
    if not combined_out.empty:
        wr = (combined_out['Result']=='WIN').sum() / len(combined_out) * 100
        rr = (combined_out['Result']=='REFUND').sum() / len(combined_out) * 100
        
        if wr < 30:
            findings.append(f"<b>X NIZAK WIN RATE:</b> {wr:.1f}% (premalo, treba ≥52.6%)")
        elif wr < 52.6:
            findings.append(f"<b>! Win rate ispod breakeven-a:</b> {wr:.1f}%")
        else:
            findings.append(f"<b>✓ Win rate iznad breakeven-a:</b> {wr:.1f}%")
        
        if rr > 30:
            findings.append(f"<b>! VISOK REFUND RATE:</b> {rr:.1f}% — strike-ovi su preveliki za stvarno tržišno kretanje")
        
        # Strike bucket insights
        combined_out_c = combined_out.copy()
        combined_out_c['StrikeBucket'] = pd.cut(combined_out_c['Strike'], 
                                                  bins=[0, 12, 18, 25, 100], 
                                                  labels=['<=12p', '13-18p', '19-25p', '>25p'])
        for bucket in ['<=12p', '13-18p', '19-25p', '>25p']:
            subset = combined_out_c[combined_out_c['StrikeBucket']==bucket]
            if len(subset) >= 3:
                bucket_wr = (subset['Result']=='WIN').sum() / len(subset) * 100
                bucket_rr = (subset['Result']=='REFUND').sum() / len(subset) * 100
                if bucket_rr > 50:
                    findings.append(f"! <b>Strike {bucket}</b>: refund rate {bucket_rr:.0f}% (n={len(subset)}) — preveliki strike")
                elif bucket_wr > 40:
                    findings.append(f"✓ <b>Strike {bucket}</b>: win rate {bucket_wr:.0f}% (n={len(subset)})")
        
        # Direction bias
        buy_count = (combined_out['Direction']=='BUY').sum()
        sell_count = (combined_out['Direction']=='SELL').sum()
        buy_wr = (combined_out[combined_out['Direction']=='BUY']['Result']=='WIN').sum() / max(buy_count, 1) * 100
        sell_wr = (combined_out[combined_out['Direction']=='SELL']['Result']=='WIN').sum() / max(sell_count, 1) * 100
        findings.append(f"BUY WR: {buy_wr:.0f}% (n={buy_count}) | SELL WR: {sell_wr:.0f}% (n={sell_count})")
        
        # MAE/MFE insight
        win_subset = combined_out[combined_out['Result']=='WIN']
        loss_subset = combined_out[combined_out['Result']=='LOSS']
        if len(win_subset) > 0 and len(loss_subset) > 0:
            findings.append(f"WIN trades: MAE = {win_subset['MAE_pips'].mean():.1f}p (mala adverzija = clean entries)")
            findings.append(f"LOSS trades: MFE = {loss_subset['MFE_pips'].mean():.1f}p (puno predala se prije nego trend)")
    
    if not h1.empty:
        peak_hour = h1['Hour'].value_counts().idxmax()
        findings.append(f"Najaktivniji sat za H1: <b>{peak_hour}:00 UTC</b>")
    
    if len(combined_out) < 50:
        findings.append(f"<i>Sample {len(combined_out)} outcomes - treba 50+ za pouzdane zaključke</i>")
    
    findings.append("<b>PREPORUKE:</b>")
    if not combined_out.empty:
        rr = (combined_out['Result']=='REFUND').sum() / len(combined_out) * 100
        if rr > 30:
            findings.append("1. Smanjiti ATR multiplikator (1.2→1.0, 1.5→1.3, 1.8→1.5) - manji strike-ovi")
        wr = (combined_out['Result']=='WIN').sum() / len(combined_out) * 100
        if wr < 40:
            findings.append("2. Razmotriti SMA200 hard filter i u H1 scanner-u (sad je samo M15)")
            findings.append("3. Filter signala s pips/hour > 3.5 - vjerojatno netočni")
    findings.append("4. Sačekati još 7-14 dana podataka prije velikih promjena")
    
    for f in findings:
        story.append(Paragraph(f"• {f}", styles['Finding']))
    
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        f"<i>Generirao master_report.py v2 | {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>",
        styles['BodyTxt']
    ))
    
    doc.build(story)
    
    # Cleanup
    for f in ['tmp_h1_hours.png', 'tmp_h1_score.png', 'tmp_h1_pph.png', 
              'tmp_h1_pairs.png', 'tmp_m15_hours.png', 'tmp_pie_combined.png',
              'tmp_pie_h1.png', 'tmp_pie_m15.png', 'tmp_wr_pair.png',
              'tmp_wr_strike.png', 'tmp_mae_mfe.png']:
        if os.path.exists(f):
            os.remove(f)
    
    print(f"\nOK PDF generiran: {PDF_FILENAME}")
    print(f"   Lokacija: {os.path.abspath(PDF_FILENAME)}")

if __name__ == '__main__':
    print("="*60)
    print("BREAKOUT TRADING SYSTEM — Master Report Generator v2")
    print("="*60)
    data = load_data()
    print()
    generate_pdf(data)
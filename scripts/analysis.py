"""
Finance Analysis Utilities
Helper functions for analyzing spending data.
"""

import pandas as pd
import os
from datetime import datetime
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
BUDGETS_DIR = PROJECT_ROOT / "budgets"


def load_transactions(filename=None):
    """Load transaction data from CSV files in data directory.
    
    IMPORTANT: This function ensures Amount is properly parsed as numeric,
    handling quoted strings and negative values (refunds/credits).
    """
    if filename:
        filepath = DATA_DIR / filename
        df = pd.read_csv(filepath)
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        return df
    
    # Load all CSV files in data directory
    all_data = []
    for f in DATA_DIR.glob("*.csv"):
        df = pd.read_csv(f)
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df['Source'] = f.stem
        all_data.append(df)
    
    if not all_data:
        raise FileNotFoundError("No CSV files found in data directory")
    
    return pd.concat(all_data, ignore_index=True)


def get_summary_stats(df):
    """Calculate basic summary statistics.
    
    Returns both gross (purchases only) and net (purchases - refunds) totals.
    """
    purchases = df[df['Amount'] > 0]
    refunds = df[df['Amount'] < 0]
    
    return {
        'gross_spent': purchases['Amount'].sum(),  # Total purchases (positive only)
        'refunds': refunds['Amount'].sum(),  # Total refunds (negative)
        'net_spent': df['Amount'].sum(),  # Net = gross + refunds
        'purchase_count': len(purchases),
        'refund_count': len(refunds),
        'transaction_count': len(df),
        'avg_transaction': purchases['Amount'].mean() if len(purchases) > 0 else 0,
        'median_transaction': purchases['Amount'].median() if len(purchases) > 0 else 0,
        'date_range': (df['Date'].min(), df['Date'].max()),
        'days_covered': (df['Date'].max() - df['Date'].min()).days,
    }


def category_breakdown(df, purchases_only=True):
    """Break down spending by category.
    
    Args:
        df: Transaction DataFrame
        purchases_only: If True, only count positive amounts (default True)
    """
    if purchases_only:
        df = df[df['Amount'] > 0].copy()
    
    breakdown = df.groupby('Category').agg({
        'Amount': ['sum', 'count', 'mean']
    }).round(2)
    breakdown.columns = ['Total', 'Count', 'Average']
    
    # Calculate percent of positive total only
    total_positive = breakdown[breakdown['Total'] > 0]['Total'].sum()
    breakdown['Percent'] = (breakdown['Total'] / total_positive * 100).round(1)
    return breakdown.sort_values('Total', ascending=False)


def monthly_totals(df, purchases_only=True):
    """Calculate spending totals by month.
    
    Args:
        df: Transaction DataFrame
        purchases_only: If True, only count positive amounts (default True)
    """
    df = df.copy()
    if purchases_only:
        df = df[df['Amount'] > 0]
    
    df['Month'] = df['Date'].dt.to_period('M')
    monthly = df.groupby('Month').agg({
        'Amount': ['sum', 'count', 'mean']
    }).round(2)
    monthly.columns = ['Total', 'Count', 'Average']
    monthly['Change'] = monthly['Total'].diff()
    monthly['Change_Pct'] = monthly['Total'].pct_change() * 100
    return monthly


def top_merchants(df, n=10):
    """Get top N merchants by total spend."""
    return df.groupby('Description')['Amount'].agg(['sum', 'count', 'mean']).round(2)\
        .rename(columns={'sum': 'Total', 'count': 'Transactions', 'mean': 'Average'})\
        .sort_values('Total', ascending=False).head(n)


def day_of_week_analysis(df):
    """Analyze spending patterns by day of week."""
    df = df.copy()
    df['DayOfWeek'] = df['Date'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow = df.groupby('DayOfWeek')['Amount'].agg(['sum', 'count', 'mean']).round(2)
    dow = dow.reindex(day_order)
    dow.columns = ['Total', 'Count', 'Average']
    return dow


def find_recurring_charges(df, threshold_months=2):
    """Identify potentially recurring charges."""
    df = df.copy()
    df['Month'] = df['Date'].dt.to_period('M')
    
    # Group by merchant and month
    monthly_merchant = df.groupby(['Description', 'Month'])['Amount'].sum().reset_index()
    
    # Count how many months each merchant appears
    merchant_frequency = monthly_merchant.groupby('Description').agg({
        'Month': 'count',
        'Amount': ['mean', 'std']
    })
    merchant_frequency.columns = ['Months_Present', 'Avg_Amount', 'Std_Amount']
    
    # Filter to those appearing multiple months with consistent amounts
    recurring = merchant_frequency[
        (merchant_frequency['Months_Present'] >= threshold_months) &
        (merchant_frequency['Std_Amount'].fillna(0) < merchant_frequency['Avg_Amount'] * 0.2)
    ].sort_values('Avg_Amount', ascending=False)
    
    return recurring.round(2)


def spending_velocity(df):
    """Calculate spending velocity metrics."""
    stats = get_summary_stats(df)
    days = max(stats['days_covered'], 1)
    
    return {
        'daily_average': stats['total_spent'] / days,
        'weekly_average': (stats['total_spent'] / days) * 7,
        'monthly_projection': (stats['total_spent'] / days) * 30.44,
        'annual_projection': (stats['total_spent'] / days) * 365,
    }


def detect_impulse_spending(df):
    """Flag potential impulse purchases."""
    df = df.copy()
    
    # Multiple small purchases same day
    df['DateOnly'] = df['Date'].dt.date
    daily_counts = df.groupby(['DateOnly', 'Category']).size()
    high_frequency_days = daily_counts[daily_counts >= 3]
    
    # Small transactions that add up
    small_trans = df[df['Amount'] < 20]
    small_total = small_trans['Amount'].sum()
    small_percent = (small_total / df['Amount'].sum()) * 100
    
    return {
        'high_frequency_days': len(high_frequency_days),
        'small_transactions_total': small_total,
        'small_transactions_percent': small_percent,
        'small_transaction_count': len(small_trans),
    }


def generate_markdown_table(df, title=None):
    """Convert DataFrame to markdown table string."""
    lines = []
    if title:
        lines.append(f"### {title}\n")
    
    # Header
    lines.append("| " + " | ".join(str(c) for c in df.columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(df.columns)) + " |")
    
    # Rows
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in row.values) + " |")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Comprehensive verification test
    try:
        df = load_transactions()
        stats = get_summary_stats(df)
        
        print("="*50)
        print("DATA VERIFICATION REPORT")
        print("="*50)
        print(f"\nData loaded successfully!")
        print(f"Date range: {stats['date_range'][0].strftime('%m/%d/%Y')} to {stats['date_range'][1].strftime('%m/%d/%Y')}")
        print(f"Days covered: {stats['days_covered']}")
        print(f"\n--- TRANSACTION COUNTS ---")
        print(f"Total transactions: {stats['transaction_count']}")
        print(f"Purchases: {stats['purchase_count']}")
        print(f"Refunds/Credits: {stats['refund_count']}")
        print(f"\n--- AMOUNTS ---")
        print(f"Gross Spending (purchases only): ${stats['gross_spent']:,.2f}")
        print(f"Refunds/Credits: ${stats['refunds']:,.2f}")
        print(f"Net Spending (gross + refunds): ${stats['net_spent']:,.2f}")
        print(f"\n--- AVERAGES (purchases only) ---")
        print(f"Average transaction: ${stats['avg_transaction']:,.2f}")
        print(f"Median transaction: ${stats['median_transaction']:,.2f}")
        print(f"Daily average: ${stats['gross_spent'] / max(stats['days_covered'], 1):,.2f}")
        
        # Show refund details
        refunds_df = df[df['Amount'] < 0]
        if len(refunds_df) > 0:
            print(f"\n--- REFUNDS/CREDITS DETAIL ---")
            for _, row in refunds_df.iterrows():
                print(f"  {row['Date'].strftime('%m/%d')}: ${row['Amount']:,.2f} - {row['Description']}")
        
        print("\n" + "="*50)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

"""
Finance Visualization Utilities
Generate charts and visual reports for spending data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import sys

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from analysis import load_transactions, category_breakdown, monthly_totals, day_of_week_analysis

PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


def plot_category_pie(df, save_path=None):
    """Create pie chart of spending by category."""
    breakdown = category_breakdown(df)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    colors = plt.cm.Set3(range(len(breakdown)))
    
    wedges, texts, autotexts = ax.pie(
        breakdown['Total'],
        labels=breakdown.index,
        autopct='%1.1f%%',
        colors=colors,
        startangle=90
    )
    ax.set_title('Spending by Category', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return save_path
    else:
        plt.show()


def plot_monthly_trend(df, save_path=None):
    """Create line chart of monthly spending trend."""
    monthly = monthly_totals(df)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    months = [str(m) for m in monthly.index]
    ax.plot(months, monthly['Total'], marker='o', linewidth=2, markersize=8)
    ax.fill_between(months, monthly['Total'], alpha=0.3)
    
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Total Spending ($)', fontsize=12)
    ax.set_title('Monthly Spending Trend', fontsize=14, fontweight='bold')
    
    # Add average line
    avg = monthly['Total'].mean()
    ax.axhline(y=avg, color='r', linestyle='--', alpha=0.7, label=f'Average: ${avg:,.0f}')
    ax.legend()
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return save_path
    else:
        plt.show()


def plot_category_bars(df, save_path=None):
    """Create horizontal bar chart of spending by category."""
    breakdown = category_breakdown(df)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = plt.cm.viridis(breakdown['Total'] / breakdown['Total'].max())
    bars = ax.barh(breakdown.index, breakdown['Total'], color=colors)
    
    ax.set_xlabel('Total Spending ($)', fontsize=12)
    ax.set_title('Spending by Category', fontsize=14, fontweight='bold')
    
    # Add value labels
    for bar, val in zip(bars, breakdown['Total']):
        ax.text(val + 50, bar.get_y() + bar.get_height()/2, 
                f'${val:,.0f}', va='center', fontsize=9)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return save_path
    else:
        plt.show()


def plot_day_of_week(df, save_path=None):
    """Create bar chart of spending by day of week."""
    dow = day_of_week_analysis(df)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = ['#ff9999' if d in ['Saturday', 'Sunday'] else '#66b3ff' for d in dow.index]
    ax.bar(dow.index, dow['Average'], color=colors)
    
    ax.set_xlabel('Day of Week', fontsize=12)
    ax.set_ylabel('Average Daily Spending ($)', fontsize=12)
    ax.set_title('Spending by Day of Week', fontsize=14, fontweight='bold')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return save_path
    else:
        plt.show()


def plot_daily_spending(df, save_path=None):
    """Create daily spending chart."""
    df = df.copy()
    daily = df.groupby(df['Date'].dt.date)['Amount'].sum()
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.bar(daily.index, daily.values, width=0.8, alpha=0.7)
    
    # Add 7-day rolling average
    rolling = pd.Series(daily.values, index=daily.index).rolling(7).mean()
    ax.plot(daily.index, rolling, color='red', linewidth=2, label='7-day avg')
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Daily Spending ($)', fontsize=12)
    ax.set_title('Daily Spending Pattern', fontsize=14, fontweight='bold')
    ax.legend()
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return save_path
    else:
        plt.show()


def generate_all_charts(df, output_dir=None):
    """Generate all standard charts and save to output directory."""
    if output_dir is None:
        output_dir = REPORTS_DIR / "charts"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    charts = []
    
    charts.append(plot_category_pie(df, output_dir / "category_pie.png"))
    charts.append(plot_monthly_trend(df, output_dir / "monthly_trend.png"))
    charts.append(plot_category_bars(df, output_dir / "category_bars.png"))
    charts.append(plot_day_of_week(df, output_dir / "day_of_week.png"))
    charts.append(plot_daily_spending(df, output_dir / "daily_spending.png"))
    
    return charts


if __name__ == "__main__":
    # Generate all charts
    df = load_transactions()
    charts = generate_all_charts(df)
    print(f"Generated {len(charts)} charts")
    for c in charts:
        print(f"  - {c}")

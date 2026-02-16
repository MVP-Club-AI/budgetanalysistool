# /quick-summary

Get a fast overview of your financial situation without detailed analysis.

## MANDATORY: No Guessing Allowed

**You MUST calculate every number from the actual CSV data. Never estimate.**

- Do NOT output any financial figures without first running Python/pandas calculations
- Do NOT use words like "approximately", "roughly", "around", "about"
- Do NOT rely on memory of what the data might contain
- If you cannot calculate it, say "calculation required" instead of guessing

## Step 1: Load and Calculate (REQUIRED)

You MUST run this code FIRST before outputting anything:

```python
import pandas as pd
from pathlib import Path

# Load all CSV files in data directory
data_dir = Path('data')
csv_files = list(data_dir.glob('*.csv'))

all_data = []
for f in csv_files:
    df = pd.read_csv(f)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    all_data.append(df)

df = pd.concat(all_data, ignore_index=True)

# Separate purchases from refunds
purchases = df[df['Amount'] > 0]
refunds = df[df['Amount'] < 0]

# Calculate EXACT figures
gross_total = purchases['Amount'].sum()
refund_total = refunds['Amount'].sum()
net_total = df['Amount'].sum()
purchase_count = len(purchases)
refund_count = len(refunds)
days = (df['Date'].max() - df['Date'].min()).days
daily_avg = gross_total / days if days > 0 else 0

# Category breakdown (purchases only)
cat_breakdown = purchases.groupby('Category')['Amount'].sum().sort_values(ascending=False)
cat_pct = (cat_breakdown / gross_total * 100).round(1)

# Top merchants (purchases only)
top_merchants = purchases.groupby('Description')['Amount'].sum().sort_values(ascending=False).head(5)

# Print for verification
print(f"Gross: ${gross_total:,.2f}")
print(f"Refunds: ${refund_total:,.2f}")
print(f"Net: ${net_total:,.2f}")
```

## Step 2: Verify Before Output

Before writing your response, confirm:
- Category percentages should sum to 100%
- All numbers came from the code above, not from memory

## Step 3: Output Format

Only AFTER calculations are complete, format as:

```
QUICK FINANCIAL SUMMARY
==========================
Period: [EXACT DATE RANGE FROM DATA]

TOTALS
---------
Gross Spending: $[CALCULATED] ([X] purchases)
Refunds/Credits: $[CALCULATED] ([X] refunds)
Net Spending: $[CALCULATED]
Daily Average: $[CALCULATED]

TOP 5 CATEGORIES
-------------------
1. [Category] - $[CALCULATED] ([X]%)
2. [Category] - $[CALCULATED] ([X]%)
3. [Category] - $[CALCULATED] ([X]%)
4. [Category] - $[CALCULATED] ([X]%)
5. [Category] - $[CALCULATED] ([X]%)

TOP 5 MERCHANTS
------------------
1. [Merchant] - $[CALCULATED]
2. [Merchant] - $[CALCULATED]
3. [Merchant] - $[CALCULATED]
4. [Merchant] - $[CALCULATED]
5. [Merchant] - $[CALCULATED]

QUICK INSIGHTS
-----------------
- [Insight based on calculated data]
- [Insight based on calculated data]
- [Insight based on calculated data]
```

## Forbidden

- Outputting ANY dollar amount without first calculating it
- Using "approximately", "about", "around", "roughly"
- Filling in numbers from memory or assumption
- Skipping the data loading step

## Arguments
None - this is a quick view only.

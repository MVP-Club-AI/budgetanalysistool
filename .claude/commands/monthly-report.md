# /monthly-report

Generate a detailed monthly spending report.

## MANDATORY: Read DATA_RULES.md First
See `.claude/DATA_RULES.md` - Every number must be calculated, never estimated.

## Step 1: Load and Parse Data (REQUIRED)

```python
import pandas as pd
from pathlib import Path

# Load all CSV files in data directory
data_dir = Path('data')
all_data = []
for f in data_dir.glob('*.csv'):
    df = pd.read_csv(f)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    all_data.append(df)
df = pd.concat(all_data, ignore_index=True)
purchases = df[df['Amount'] > 0]
```

## Step 2: Determine Month

Use `$MONTH` argument if provided, otherwise use the most recent complete month:
```python
# Get most recent complete month
latest_date = df['Date'].max()
if latest_date.day < 28:  # Incomplete month
    report_month = latest_date - pd.DateOffset(months=1)
else:
    report_month = latest_date
report_period = report_month.to_period('M')
```

## Step 3: Filter to Month

```python
purchases['Month'] = purchases['Date'].dt.to_period('M')
this_month = purchases[purchases['Month'] == report_period]
prev_month = purchases[purchases['Month'] == report_period - 1]
```

## Step 4: Calculate All Metrics

```python
# This month totals
this_total = this_month['Amount'].sum()
this_count = len(this_month)
this_avg = this_month['Amount'].mean()

# Previous month totals
prev_total = prev_month['Amount'].sum()
prev_count = len(prev_month)

# Change
change_dollars = this_total - prev_total
change_pct = ((this_total - prev_total) / prev_total * 100) if prev_total > 0 else 0

# Category breakdown for this month
this_cats = this_month.groupby('Category')['Amount'].agg(['sum', 'count', 'mean']).round(2)
prev_cats = prev_month.groupby('Category')['Amount'].sum()

# Top merchants this month
top_merchants = this_month.groupby('Description')['Amount'].sum().sort_values(ascending=False).head(5)

# Largest transactions
largest = this_month.nlargest(5, 'Amount')[['Date', 'Description', 'Amount', 'Category']]
```

## Step 5: Generate Report

All numbers must come from Step 4 calculations:

```markdown
# Monthly Report: [MONTH YEAR]

## Executive Summary
- Total Spent: $[this_total] ([this_count] transactions)
- vs Last Month: $[change_dollars] ([change_pct]%)
- Biggest Category: [from this_cats]

## Category Breakdown
| Category | This Month | Last Month | Change |
[Generate from this_cats and prev_cats DataFrames]

## Top 5 Merchants
[From top_merchants calculation]

## Largest Transactions
[From largest DataFrame]

## Daily Spending
[Calculate from this_month grouped by date]
```

## Step 6: Save Report

Save to `reports/monthly-[MONTH]-[YEAR].md`

## Verification Checklist

- [ ] Loaded CSV fresh
- [ ] Converted Amount to numeric
- [ ] All figures from pandas calculations
- [ ] No "approximately" or "around" in output
- [ ] Category totals sum to month total

## Arguments
- `$MONTH` - Month to report on (name or number). Default: most recent complete month.

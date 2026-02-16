# /analyze-spending

Perform a comprehensive spending analysis on the transaction data.

## MANDATORY: Calculate Everything From Real Data

**Every single number in your response MUST come from a pandas calculation.**

- NO guessing, NO estimating, NO "approximately"
- If you haven't run the calculation, don't report the number
- Load the CSV fresh every time - never rely on cached/remembered values

## Step 1: Data Loading (REQUIRED FIRST)

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
purchases = df[df['Amount'] > 0]
refunds = df[df['Amount'] < 0]

# VERIFY: Print totals immediately
print(f"Loaded {len(df)} transactions")
print(f"Gross spending: ${purchases['Amount'].sum():,.2f}")
print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
```

## Step 2: Generate These Analyses (all from calculated data)

### Overall Summary
Calculate these exact values:
- `gross_total = purchases['Amount'].sum()`
- `transaction_count = len(purchases)`
- `avg_transaction = purchases['Amount'].mean()`
- `days = (df['Date'].max() - df['Date'].min()).days`
- `daily_rate = gross_total / days`

### Category Breakdown
```python
cat_stats = purchases.groupby('Category').agg({
    'Amount': ['sum', 'count', 'mean']
}).round(2)
cat_stats.columns = ['Total', 'Count', 'Average']
cat_stats['Percent'] = (cat_stats['Total'] / cat_stats['Total'].sum() * 100).round(1)
cat_stats = cat_stats.sort_values('Total', ascending=False)
```

Output as table - every number from the DataFrame above.

### Monthly Trends
```python
purchases_copy = purchases.copy()
purchases_copy['Month'] = purchases_copy['Date'].dt.to_period('M')
monthly = purchases_copy.groupby('Month')['Amount'].agg(['sum', 'count']).round(2)
monthly['Change'] = monthly['sum'].diff()
monthly['Change_Pct'] = (monthly['sum'].pct_change() * 100).round(1)
```

### Top 10 Merchants
```python
top_merchants = purchases.groupby('Description')['Amount'].sum().sort_values(ascending=False).head(10)
```

### Day of Week Analysis
```python
purchases_copy = purchases.copy()
purchases_copy['DayOfWeek'] = purchases_copy['Date'].dt.day_name()
dow = purchases_copy.groupby('DayOfWeek')['Amount'].agg(['sum', 'mean', 'count']).round(2)
```

### Spending Velocity
```python
days = (df['Date'].max() - df['Date'].min()).days
gross = purchases['Amount'].sum()
daily = gross / days
weekly = daily * 7
monthly_proj = daily * 30.44
annual_proj = daily * 365
```

## Step 3: Save Output

Save report to `reports/spending-analysis-[DATE].md`

## Step 4: Key Insights

Provide 3-5 insights - but only observations supported by the calculated data. No speculation.

## Verification Checklist

Before finalizing response:
- [ ] Every dollar amount came from a pandas calculation
- [ ] Category percentages sum to 100%
- [ ] I did not use "approximately", "roughly", "about", or "around"
- [ ] I loaded the CSV fresh (not from memory)

## Arguments
- `$MONTH` - Optional: Limit analysis to specific month (e.g., "December" or "12")
- `$CATEGORY` - Optional: Focus on specific category

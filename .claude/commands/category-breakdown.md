# /category-breakdown

Deep dive analysis into a specific spending category.

## MANDATORY: Read DATA_RULES.md First
See `.claude/DATA_RULES.md` - Every number must be calculated, never estimated.

## Step 1: Load Data (REQUIRED)

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

# List available categories
print("Available categories:", purchases['Category'].unique())
```

If no `$CATEGORY` specified, list categories and ask user to choose.

## Step 2: Filter to Category

```python
category_name = "$CATEGORY"  # From argument
cat_data = purchases[purchases['Category'] == category_name]

if len(cat_data) == 0:
    print(f"No transactions found for category: {category_name}")
    # Stop here
```

## Step 3: Calculate All Metrics

```python
# Overview
cat_total = cat_data['Amount'].sum()
cat_count = len(cat_data)
cat_avg = cat_data['Amount'].mean()
cat_median = cat_data['Amount'].median()
cat_pct = (cat_total / purchases['Amount'].sum() * 100)

# Merchant breakdown
merchants = cat_data.groupby('Description').agg({
    'Amount': ['sum', 'count', 'mean'],
    'Date': ['min', 'max']
}).round(2)
merchants.columns = ['Total', 'Count', 'Average', 'First', 'Last']
merchants = merchants.sort_values('Total', ascending=False)

# Monthly trend
cat_data_copy = cat_data.copy()
cat_data_copy['Month'] = cat_data_copy['Date'].dt.to_period('M')
monthly = cat_data_copy.groupby('Month')['Amount'].agg(['sum', 'count']).round(2)
monthly_avg = monthly['sum'].mean()
monthly_std = monthly['sum'].std()

# Transaction size distribution
size_buckets = pd.cut(cat_data['Amount'], bins=[0, 10, 25, 50, 100, float('inf')],
                      labels=['<$10', '$10-25', '$25-50', '$50-100', '$100+'])
size_dist = cat_data.groupby(size_buckets)['Amount'].agg(['count', 'sum']).round(2)

# Day of week
cat_data_copy['DayOfWeek'] = cat_data_copy['Date'].dt.day_name()
dow = cat_data_copy.groupby('DayOfWeek')['Amount'].agg(['count', 'sum', 'mean']).round(2)
```

## Step 4: Generate Report

**All numbers from Step 3 calculations:**

```markdown
# Category Analysis: [CATEGORY]

## Overview
- Total Spent: $[cat_total]
- Percentage of All Spending: [cat_pct]%
- Transaction Count: [cat_count]
- Average Transaction: $[cat_avg]
- Median Transaction: $[cat_median]

## Merchant Breakdown
| Merchant | Total | Transactions | Average | First | Last |
[From merchants DataFrame]

## Monthly Trend
| Month | Spent | Count |
[From monthly DataFrame]

Monthly Average: $[monthly_avg]
Variance (Std Dev): $[monthly_std]

## Transaction Size Distribution
| Range | Count | Total |
[From size_dist DataFrame]

## Day of Week Patterns
| Day | Count | Total | Average |
[From dow DataFrame]

## Optimization Opportunities
[Based ONLY on calculated data above]
```

## Step 5: Save Report

Save to `reports/category-[CATEGORY]-[DATE].md`

## Arguments
- `$CATEGORY` - Required: Category to analyze (e.g., "Dining", "Grocery")

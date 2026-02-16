# /compare-periods

Compare spending between two time periods.

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
purchases['Month'] = purchases['Date'].dt.to_period('M')
```

## Step 2: Determine Periods

Parse `$PERIOD_A` and `$PERIOD_B` arguments. If not provided, default to current vs previous month.

```python
# Example: comparing two months
period_a = pd.Period('2025-11', freq='M')
period_b = pd.Period('2025-12', freq='M')

data_a = purchases[purchases['Month'] == period_a]
data_b = purchases[purchases['Month'] == period_b]
```

## Step 3: Calculate Comparison Metrics

```python
# Overall metrics
total_a = data_a['Amount'].sum()
total_b = data_b['Amount'].sum()
count_a = len(data_a)
count_b = len(data_b)
avg_a = data_a['Amount'].mean() if len(data_a) > 0 else 0
avg_b = data_b['Amount'].mean() if len(data_b) > 0 else 0

change_dollars = total_b - total_a
change_pct = ((total_b - total_a) / total_a * 100) if total_a > 0 else 0

# Category comparison
cats_a = data_a.groupby('Category')['Amount'].sum()
cats_b = data_b.groupby('Category')['Amount'].sum()
cat_comparison = pd.DataFrame({
    'Period_A': cats_a,
    'Period_B': cats_b
}).fillna(0)
cat_comparison['Change'] = cat_comparison['Period_B'] - cat_comparison['Period_A']
cat_comparison['Change_Pct'] = (cat_comparison['Change'] / cat_comparison['Period_A'].replace(0, 1) * 100).round(1)

# Merchant comparison
merchants_a = set(data_a['Description'].unique())
merchants_b = set(data_b['Description'].unique())
new_merchants = merchants_b - merchants_a
dropped_merchants = merchants_a - merchants_b
```

## Step 4: Identify Wins and Concerns

```python
# Categories that decreased (wins)
wins = cat_comparison[cat_comparison['Change'] < 0].sort_values('Change')
total_savings = wins['Change'].sum() * -1  # Convert to positive

# Categories that increased (concerns)
concerns = cat_comparison[cat_comparison['Change'] > 0].sort_values('Change', ascending=False)
total_increase = concerns['Change'].sum()
```

## Step 5: Generate Report

**All numbers from calculations above:**

```markdown
# Period Comparison: [PERIOD_A] vs [PERIOD_B]

## Overall Summary
| Metric | [PERIOD_A] | [PERIOD_B] | Change ($) | Change (%) |
|--------|------------|------------|------------|------------|
| Total Spent | $[total_a] | $[total_b] | $[change_dollars] | [change_pct]% |
| Transactions | [count_a] | [count_b] | [count_b - count_a] | |
| Avg Transaction | $[avg_a] | $[avg_b] | | |

## Category Comparison
| Category | [PERIOD_A] | [PERIOD_B] | Change | Change % |
[From cat_comparison DataFrame]

## Behavioral Changes
New Merchants in [PERIOD_B]: [list from new_merchants]
Dropped from [PERIOD_A]: [list from dropped_merchants]

## Improvements (Lower Spending)
[From wins DataFrame]
Total Saved: $[total_savings]

## Areas of Concern (Higher Spending)
[From concerns DataFrame]
Total Increase: $[total_increase]

## Trend Direction
[State based on change_pct - calculated, not guessed]
```

## Forbidden

- Describing trends without showing the calculated change
- Saying "spending increased significantly" without the exact percentage
- Estimating which categories changed without calculating

## Arguments
- `$PERIOD_A` - First period (e.g., "November" or "Nov 2025")
- `$PERIOD_B` - Second period (e.g., "December" or "Dec 2025")

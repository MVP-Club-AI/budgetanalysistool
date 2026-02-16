# /find-savings

Analyze spending data to identify concrete opportunities to save money.

## MANDATORY: Read DATA_RULES.md First
See `.claude/DATA_RULES.md` - Every number must be calculated, never estimated.

**All savings opportunities must be based on CALCULATED data, not assumptions.**

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

## Step 2: Subscription & Recurring Analysis

```python
# Find merchants appearing in 3+ months with consistent amounts
monthly_merchant = purchases.groupby(['Description', 'Month'])['Amount'].sum().reset_index()
merchant_freq = monthly_merchant.groupby('Description').agg({
    'Month': 'count',
    'Amount': ['mean', 'std']
})
merchant_freq.columns = ['Months', 'AvgAmount', 'StdAmount']

# Recurring = appears 3+ months with low variance
recurring = merchant_freq[
    (merchant_freq['Months'] >= 3) &
    (merchant_freq['StdAmount'].fillna(0) < merchant_freq['AvgAmount'] * 0.3)
].sort_values('AvgAmount', ascending=False)

annual_recurring = (recurring['AvgAmount'] * 12).sum()
```

## Step 3: Dining Analysis

```python
dining = purchases[purchases['Category'] == 'Dining']
dining_total = dining['Amount'].sum()
dining_monthly_avg = dining.groupby('Month')['Amount'].sum().mean()
dining_count = len(dining)

# Identify delivery vs restaurant (by merchant name patterns)
delivery_keywords = ['grubhub', 'doordash', 'uber eats', 'postmates']
dining['IsDelivery'] = dining['Description'].str.lower().str.contains('|'.join(delivery_keywords), na=False)
delivery_total = dining[dining['IsDelivery']]['Amount'].sum()
restaurant_total = dining[~dining['IsDelivery']]['Amount'].sum()
```

## Step 4: Small Transaction Analysis

```python
small_purchases = purchases[purchases['Amount'] < 20]
small_total = small_purchases['Amount'].sum()
small_count = len(small_purchases)
small_pct = (small_total / purchases['Amount'].sum() * 100)

# Under $10
micro_purchases = purchases[purchases['Amount'] < 10]
micro_total = micro_purchases['Amount'].sum()
```

## Step 5: Category Reduction Calculations

```python
# For each category, calculate reduction scenarios
cat_totals = purchases.groupby('Category')['Amount'].sum().sort_values(ascending=False)

savings_10pct = cat_totals * 0.10
savings_20pct = cat_totals * 0.20
```

## Step 6: Generate Savings Report

**Only report numbers you calculated above:**

```markdown
# Savings Opportunities Report

## Recurring/Subscription Charges
| Merchant | Monthly | Annual |
[From recurring DataFrame - EXACT numbers only]

Total Annual Recurring: $[annual_recurring]

## Dining Breakdown
- Total Dining: $[dining_total]
- Delivery Orders: $[delivery_total]
- Restaurants: $[restaurant_total]
- Monthly Average: $[dining_monthly_avg]

Potential Savings:
- Reduce delivery by 50%: $[delivery_total * 0.5 / 12]/month
- Cut 2 restaurant meals/month: ~$[calculate from avg transaction]

## Small Purchase Impact
- Transactions under $20: [small_count] totaling $[small_total] ([small_pct]%)
- Transactions under $10: totaling $[micro_total]

## Category Reduction Targets
| Category | Current | 10% Reduction | 20% Reduction |
[From cat_totals and savings calculations]

## Total Potential Savings
- Conservative (easy): $[sum of realistic targets]/month
- Moderate: $[sum of moderate targets]/month
- Aggressive: $[sum of aggressive targets]/month
```

## Prohibited in This Command

- Estimating savings without calculating from actual spending
- Suggesting "you could save around $X" without showing the math
- Making assumptions about spending habits not supported by data

## Arguments
- `$TARGET` - Optional savings goal (e.g., "$500/month")

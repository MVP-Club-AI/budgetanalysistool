# /budget-plan

Create or update a budget plan based on spending history and goals.

## MANDATORY: Read DATA_RULES.md First
See `.claude/DATA_RULES.md` - Every number must be calculated from actual data.

**Budget targets must be based on REAL historical spending, not guesses.**

## Step 1: Load Historical Data (REQUIRED)

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

## Step 2: Calculate Historical Baseline (ALL from data)

```python
# Monthly averages by category
monthly_cat = purchases.groupby(['Month', 'Category'])['Amount'].sum().unstack(fill_value=0)
cat_monthly_avg = monthly_cat.mean()
cat_monthly_min = monthly_cat.min()
cat_monthly_max = monthly_cat.max()
cat_monthly_std = monthly_cat.std()

# Overall monthly average
monthly_totals = purchases.groupby('Month')['Amount'].sum()
overall_monthly_avg = monthly_totals.mean()
overall_monthly_std = monthly_totals.std()

# Trend direction per category
def calc_trend(series):
    if len(series) < 3:
        return 'insufficient data'
    recent = series.iloc[-3:].mean()
    earlier = series.iloc[:3].mean()
    pct_change = (recent - earlier) / earlier * 100 if earlier > 0 else 0
    if pct_change > 10:
        return 'increasing'
    elif pct_change < -10:
        return 'decreasing'
    return 'stable'

cat_trends = {cat: calc_trend(monthly_cat[cat]) for cat in monthly_cat.columns}
```

## Step 3: Gather User Input (if needed)

Ask user for (if not previously provided):
- Monthly take-home income
- Savings goals (dollar amount or percentage)
- Specific constraints or priorities

**Do not assume income or goals - ask explicitly.**

## Step 4: Create Realistic Budget

```python
# Start with historical averages
budget = pd.DataFrame({
    'Historical_Avg': cat_monthly_avg,
    'Min_Month': cat_monthly_min,
    'Max_Month': cat_monthly_max,
    'Trend': pd.Series(cat_trends)
})

# Calculate proposed budgets
# Rule: Don't propose more than 20% below historical without good reason
budget['Proposed'] = cat_monthly_avg  # Start with average
budget['Change'] = 0

# Classify needs vs wants (adjust based on your actual categories)
needs_categories = ['Grocery', 'Gas/Automotive', 'Phone/Cable', 'Healthcare']
wants_categories = ['Dining', 'Entertainment', 'Merchandise']

budget['Type'] = budget.index.map(
    lambda x: 'Need' if x in needs_categories else 'Want'
)

# Calculate totals
needs_total = budget[budget['Type'] == 'Need']['Proposed'].sum()
wants_total = budget[budget['Type'] == 'Want']['Proposed'].sum()
total_budget = budget['Proposed'].sum()
```

## Step 5: Apply 50/30/20 Framework (if income provided)

```python
if income:
    target_needs = income * 0.50
    target_wants = income * 0.30
    target_savings = income * 0.20

    # Compare to actual
    needs_vs_target = needs_total - target_needs
    wants_vs_target = wants_total - target_wants
```

## Step 6: Generate Budget Document

**All numbers from calculations:**

```markdown
# Budget Plan: [YEAR/MONTH]

## Historical Baseline (from actual data)
| Category | Monthly Avg | Min | Max | Trend |
[From budget DataFrame]

Total Monthly Average: $[overall_monthly_avg]

## Proposed Budget
| Category | Historical | Proposed | Change | Notes |
[From budget DataFrame with adjustments]

### Summary
- Total Budget: $[total_budget]
- Needs: $[needs_total] ([needs_pct]%)
- Wants: $[wants_total] ([wants_pct]%)
- Target Savings: $[if income provided]

## vs 50/30/20 Framework
[Only if income was provided]
| Category | Target | Actual | Gap |
| Needs (50%) | $[target] | $[actual] | $[gap] |
| Wants (30%) | $[target] | $[actual] | $[gap] |
| Savings (20%) | $[target] | - | - |

## Monthly Checkpoints
- Track: [key metrics based on high-variance categories]
- Warning signs: [categories with increasing trends]

## Stretch Goals
- 10% more savings: Requires reducing [highest category] by $[calculated amount]
```

## Step 7: Save Budget

Save to `budgets/budget-[YEAR]-[MONTH].md`

## Forbidden in This Command

- Proposing budget amounts not based on historical data
- Assuming income without asking
- Suggesting savings targets without calculating what's realistic
- Using "you should budget around $X" without showing the basis

## Arguments
- `$MONTH` - Starting month for budget (default: next month)
- `$INCOME` - Monthly take-home income (will ask if not provided)
- `$GOAL` - Savings goal (e.g., "$1000/month" or "20%")

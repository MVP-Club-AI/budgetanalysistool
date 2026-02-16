# Personal Finance & Budget Tracker

## Data Integrity Rules

**NEVER guess, estimate, or approximate. ALWAYS calculate from real data.**

1. **Every number must come from a calculation** - No ballpark figures, no "approximately", no rounding for convenience
2. **Always load and parse the actual CSV** - Never rely on memory or assumptions about what the data contains
3. **Verify before reporting** - Run calculations twice if needed; totals must match the source data exactly
4. **Show your work** - When asked for totals, be prepared to show the code/formula used
5. **If data is missing, say so** - Never fill gaps with estimates; report "data not available"
6. **No mental math** - Use pandas/Python for ALL calculations, even simple ones
7. **Refuse to guess** - If you cannot calculate something from the data, explicitly state that rather than estimating

### Prohibited Phrases
Do NOT use these when reporting financial data:
- "approximately" / "roughly" / "about"
- "I estimate" / "I think" / "probably"
- "around $X" / "somewhere between"
- "based on my understanding"

### Required Approach
```python
# ALWAYS do this:
df = pd.read_csv('file.csv')
df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
actual_total = df[df['Amount'] > 0]['Amount'].sum()
print(f"Total: ${actual_total:,.2f}")  # Report this exact number

# NEVER do this:
# "The total is approximately $24,000" (guessing)
# "Based on the categories, spending is around $25k" (estimating)
```

---

## Project Overview
This is a personal finance management system for analyzing spending patterns, optimizing budgets, and planning savings/investment strategies. The primary data source is credit card transaction exports.

## Directory Structure
- `data/` - Raw transaction CSV files from financial institutions
- `reports/` - Generated analysis reports (markdown, charts)
- `budgets/` - Monthly and yearly budget plans
- `scripts/` - Python analysis scripts for complex calculations
- `.claude/commands/` - Custom slash commands for quick analysis

## Data Schema (Credit Card CSV)
The primary data file uses this schema:
| Column | Type | Description |
|--------|------|-------------|
| Date | MM/DD/YYYY | Transaction date |
| Amount | Decimal | Transaction amount (positive = purchase, **negative = refund/credit**) |
| Card | String | Last 4 digits of card |
| Category | String | Spending category |
| Description | String | Merchant name/details |

### CRITICAL: Data Parsing Rules
1. **Always convert Amount to float** - CSV has quoted strings like `"51.17"`
2. **Handle negative amounts** - Refunds appear as negative (e.g., `-29.99`)
3. **For spending totals**: Sum only positive amounts OR sum all (including negatives for net)
4. **Always verify totals** by checking: `df['Amount'].sum()` for net, `df[df['Amount'] > 0]['Amount'].sum()` for gross spending
5. **Watch for credits** - Look for "CREDIT" in Description or negative amounts

### Example Verification Code
```python
import pandas as pd
df = pd.read_csv('file.csv')
df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')  # Force numeric
gross_spending = df[df['Amount'] > 0]['Amount'].sum()
refunds = df[df['Amount'] < 0]['Amount'].sum()
net_spending = df['Amount'].sum()
print(f"Gross: ${gross_spending:,.2f}, Refunds: ${refunds:,.2f}, Net: ${net_spending:,.2f}")
```

### Example Refunds/Credits Pattern
The data may contain negative amounts representing:
- Retail returns: e.g., -$150.00
- Merchandise refunds: e.g., -$75.50
- CREDIT-TRAVEL REWARD entries: varies (look for "CREDIT" in description)
- Subscription cancellations: e.g., -$12.99
- Service refunds: e.g., -$25.00

**When analyzing, always calculate:**
- Gross spending = sum of positive amounts only
- Total refunds = sum of negative amounts
- Net spending = gross - |refunds| (or just sum all amounts)

### Known Categories
- Dining, Grocery, Gas/Automotive, Entertainment
- Merchandise, Other Services, Phone/Cable, Other

## Analysis Priorities
1. **Track Monthly Spending** - Break down by category, identify trends
2. **Find Savings Opportunities** - Recurring charges, subscription bloat, lifestyle creep
3. **Optimize Spending** - Pattern analysis, timing optimization, category reduction targets
4. **Investment Planning** - Calculate savings potential, recommend allocation

## Key Metrics to Calculate
- Total monthly/yearly spending
- Category breakdown ($ and %)
- Month-over-month changes
- Top merchants by spend
- Average transaction size by category
- Spending velocity (daily/weekly averages)
- Subscription/recurring charge totals
- Discretionary vs. essential spending ratio

## Behavior Pattern Analysis
Look for these patterns:
- **Day of week trends** - Weekend vs weekday spending
- **Time clustering** - Multiple small purchases same day
- **Category spikes** - Unusual months for specific categories
- **Lifestyle inflation** - YoY category increases
- **Impulse indicators** - Late night orders, small frequent purchases

## Budget Planning Framework
When creating budgets, use the 50/30/20 framework as a baseline:
- 50% Needs (groceries, gas, utilities, subscriptions)
- 30% Wants (dining, entertainment, merchandise)
- 20% Savings/Investing

Adjust percentages based on user's actual spending patterns and goals.

## Output Preferences
- Use markdown for reports
- Include charts when helpful (use Python matplotlib/seaborn)
- Round currency to 2 decimal places (but calculate from exact values first)
- Use tables for category breakdowns
- Provide actionable recommendations, not just data
- **ALL numbers must be calculated, never estimated**

## Verification Requirements

Before presenting ANY financial summary or report:

1. **Load the actual data file(s)** - Do not skip this step
2. **Parse amounts correctly** - `pd.to_numeric(df['Amount'], errors='coerce')`
3. **Calculate the specific metric requested** - Use pandas, not mental math
4. **Cross-check totals** - Category totals should sum to overall total
5. **State the exact figures** - No rounding unless explicitly formatting for display

### Verification Checklist (run mentally before every response)
- [ ] Did I load the CSV file?
- [ ] Did I convert Amount to numeric?
- [ ] Did I filter for purchases (Amount > 0) vs refunds (Amount < 0)?
- [ ] Does my category breakdown sum to my total?
- [ ] Am I reporting calculated values, not estimates?

If ANY answer is "no" or "unsure", reload the data and recalculate.

## Commands Reference
- `/analyze-spending` - Full spending analysis
- `/monthly-report` - Generate monthly summary
- `/find-savings` - Identify saving opportunities
- `/category-breakdown` - Deep dive into specific category
- `/budget-plan` - Create/update budget for upcoming period
- `/compare-periods` - Compare two time periods
- `/quick-summary` - Fast financial overview

## Privacy Note
This data is personal financial information. All analysis should remain local. Do not reference specific merchant names or amounts in any external communications.

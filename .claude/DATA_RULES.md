# Data Integrity Rules

**This file defines mandatory rules for ALL financial analysis commands.**

## Core Principle

**NEVER guess. ALWAYS calculate.**

Every number reported to the user must come from an actual pandas/Python calculation on the loaded CSV data.

## Mandatory Steps (Every Command)

### 1. Load Fresh Data
```python
import pandas as pd
from pathlib import Path

data_dir = Path('data')
all_data = []
for f in data_dir.glob('*.csv'):
    df = pd.read_csv(f)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    all_data.append(df)
df = pd.concat(all_data, ignore_index=True)
purchases = df[df['Amount'] > 0]
refunds = df[df['Amount'] < 0]
```

### 2. Verify Parsing
```python
gross = purchases['Amount'].sum()
print(f"Gross spending: ${gross:,.2f}")
# Verify this looks reasonable for the data loaded
```

### 3. Calculate, Don't Estimate
Use pandas for ALL math. No mental arithmetic.

### 4. Report Exact Values
Format to 2 decimal places, but calculate from precise values.

## Prohibited

| Prohibited | Use Instead |
|------------|-------------|
| "approximately $X" | "$X.XX" (exact) |
| "around $X" | "$X.XX" (exact) |
| "roughly $X" | "$X.XX" (exact) |
| "about X%" | "X.X%" (exact) |
| "I estimate" | "The data shows" |
| "probably" | "The calculation shows" |
| "I think" | "Based on the data" |
| Numbers from memory | Calculated values |

## If You Cannot Calculate

Say: "I cannot determine this from the available data"

Do NOT say: "I estimate it's around $X"

## Verification Before Every Response

Ask yourself:
1. Did I load the CSV in this session?
2. Did I run the actual calculation?
3. Is every number traceable to a line of code?
4. Would I get the same number if I ran it again?

If any answer is "no", recalculate before responding.

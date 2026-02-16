# BudgetTracker

A personal finance management system powered by [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Analyze spending patterns, optimize budgets, and plan savings using credit card transaction exports and AI-assisted analysis.

## What This Is

This is a working example of using Claude Code's custom slash commands and project instructions (`CLAUDE.md`) to build a domain-specific AI assistant. Drop in your credit card CSV exports and use natural language or slash commands to get instant financial analysis.

The project demonstrates:
- **Custom slash commands** (`.claude/commands/`) for repeatable financial analysis workflows
- **Strict data integrity rules** that prevent the AI from guessing or estimating - every number must be calculated from real data
- **Interactive HTML dashboards** generated from transaction data with D3.js
- **Python analysis scripts** for visualization and data processing

## Quick Start

1. **Clone this repo** into your working directory
2. **Add your data**: Export transactions from your credit card provider as CSV and place in `data/`. The expected format:
   ```
   Date,Amount,Card,Category,Description
   "01/15/2026","42.50","...1234","Dining","CHIPOTLE MEXICAN GRILL"
   ```
3. **Open with Claude Code**: `cd BudgetTracker && claude`
4. **Run a command**: Try `/quick-summary` or `/analyze-spending`

A sample CSV with fake transactions is included in `data/` so you can try the commands immediately.

## Slash Commands

| Command | Description |
|---------|-------------|
| `/quick-summary` | Fast overview of totals, top categories, top merchants |
| `/analyze-spending` | Comprehensive spending analysis with trends |
| `/monthly-report` | Detailed monthly breakdown with month-over-month comparison |
| `/find-savings` | Identify recurring charges, subscription bloat, reduction targets |
| `/category-breakdown` | Deep dive into a specific category (e.g., Dining, Grocery) |
| `/compare-periods` | Side-by-side comparison of two months |
| `/budget-plan` | Create a budget based on historical spending patterns |

## Data Integrity

The core design principle: **never guess, always calculate**. The `CLAUDE.md` and `.claude/DATA_RULES.md` enforce strict rules:

- Every number must come from a pandas calculation on the actual CSV
- Prohibited phrases: "approximately", "roughly", "around", "I estimate"
- If data is missing, the AI says so rather than filling gaps
- All slash commands include verification checklists

This prevents the common problem of LLMs confidently reporting plausible-but-wrong financial figures.

## Directory Structure

```
BudgetTracker/
├── CLAUDE.md                 # Project instructions for Claude Code
├── .claude/
│   ├── commands/             # Slash command definitions
│   │   ├── quick-summary.md
│   │   ├── analyze-spending.md
│   │   ├── monthly-report.md
│   │   ├── find-savings.md
│   │   ├── category-breakdown.md
│   │   ├── compare-periods.md
│   │   └── budget-plan.md
│   ├── DATA_RULES.md         # Data integrity enforcement rules
│   └── settings.local.json   # Claude Code permissions
├── data/                     # Your transaction CSVs go here
├── reports/                  # Generated analysis reports
├── budgets/                  # Generated budget plans
├── scripts/
│   ├── analysis.py           # Core analysis utilities (pandas)
│   ├── visualize.py          # Chart generation (matplotlib)
│   ├── generate_dashboard.py # Interactive HTML dashboard generator
│   ├── generate_business_dashboard.py  # Side project expense tracker
│   └── create_icon.py        # App icon generator
└── .gitignore                # Keeps personal data out of version control
```

## Dashboard

Generate an interactive HTML dashboard from your data:

```bash
python scripts/generate_dashboard.py
```

Then open `reports/dashboard.html` in your browser. Features:
- Category breakdown with click-to-drill-down
- Dining deep dive with transaction size distribution
- Subscription tracker with expected vs actual costs
- Recurring charge detection
- Year/month filtering

## Customizing

### Your Own Data
Replace the sample CSV in `data/` with your own credit card export. The system expects these columns: `Date`, `Amount`, `Card`, `Category`, `Description`.

### Subscription Tracking
Edit the `SUBSCRIPTIONS` array in `scripts/generate_dashboard.py` to match your actual subscriptions. Each entry has a name, merchant pattern to match, expected amount, and billing cycle.

### Business Expenses
Edit `scripts/generate_business_dashboard.py` to categorize business-related transactions for a side project. Customize the `categorize_business_expense()` function with your own service patterns.

### Budget Categories
The budget planner classifies categories as "Needs" vs "Wants" using the 50/30/20 framework. Adjust the category lists in the `/budget-plan` command to match your spending.

## Privacy

The `.gitignore` is configured to exclude all personal financial data (`data/`, `reports/`, `budgets/`). Only the tooling and instructions are tracked in version control.

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- Python 3.8+ with pandas, matplotlib (for scripts)
- A credit card that exports transactions as CSV

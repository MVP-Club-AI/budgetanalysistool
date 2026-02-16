#!/usr/bin/env python3
"""
Generate Budget Dashboard HTML
Reads transaction CSV and creates an interactive HTML dashboard with D3.js visualization.
"""

import pandas as pd
import json
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
REPORTS_DIR = PROJECT_DIR / "reports"

def load_transactions():
    """Load and process transaction data from all CSV files in the data directory."""
    all_dfs = []

    for csv_path in DATA_DIR.glob('*.csv'):
        df = pd.read_csv(csv_path)

        # Handle different CSV formats
        if 'Transaction Date' in df.columns:
            # New format: Transaction Date, Debit, Credit columns
            df['Date'] = pd.to_datetime(df['Transaction Date'], format='%Y-%m-%d')
            df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
            df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
            # Debit = spending (positive), Credit = payments (skip)
            df['Amount'] = df['Debit']
            # Filter out payment/credit rows
            df = df[df['Debit'] > 0].copy()
        elif 'Date' in df.columns and 'Amount' in df.columns:
            # Old format: Date, Amount columns
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        else:
            print(f"Warning: Unknown CSV format in {csv_path.name}, skipping")
            continue

        all_dfs.append(df)

    if not all_dfs:
        raise ValueError("No valid CSV files found in data directory")

    df = pd.concat(all_dfs, ignore_index=True)

    # Remove duplicates based on Date, Amount, Description
    df = df.drop_duplicates(subset=['Date', 'Amount', 'Description'], keep='first')

    df['Year'] = df['Date'].dt.year.astype(str)
    df['Month'] = df['Date'].dt.month.astype(str).str.zfill(2)
    df['YearMonth'] = df['Year'] + '-' + df['Month']

    return df

def process_data(df):
    """Process dataframe into structured data for visualization."""
    spending = df[df['Amount'] > 0].copy()

    years = sorted(spending['Year'].unique().tolist())
    categories = sorted(spending['Category'].unique().tolist())

    by_month = {}
    for ym in spending['YearMonth'].unique():
        month_data = spending[spending['YearMonth'] == ym]
        total = month_data['Amount'].sum()

        cat_data = {}
        for cat in categories:
            cat_transactions = month_data[month_data['Category'] == cat]
            if len(cat_transactions) > 0:
                cat_data[cat] = {
                    'total': round(cat_transactions['Amount'].sum(), 2),
                    'count': len(cat_transactions),
                    'transactions': cat_transactions[['Date', 'Amount', 'Description']].to_dict('records')
                }

        by_month[ym] = {
            'total': round(total, 2),
            'categories': cat_data
        }

    for ym in by_month:
        for cat in by_month[ym]['categories']:
            for txn in by_month[ym]['categories'][cat]['transactions']:
                txn['Date'] = txn['Date'].strftime('%m/%d/%Y')
                txn['Amount'] = round(txn['Amount'], 2)

    return {
        'years': years,
        'categories': categories,
        'byMonth': by_month
    }

def generate_html(data):
    """Generate the dashboard HTML with embedded data."""

    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Budget Dashboard</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f0f;
            color: #e0e0e0;
            min-height: 100vh;
        }

        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 30px;
        }

        h1 { font-size: 1.5rem; font-weight: 600; color: #fff; }

        .business-link {
            color: #8b5cf6;
            text-decoration: none;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 8px 12px;
            border: 1px solid #8b5cf6;
            border-radius: 6px;
            transition: all 0.2s;
        }

        .business-link:hover { background: #8b5cf6; color: #fff; }

        .filters { display: flex; gap: 15px; align-items: center; }

        .view-tabs {
            display: flex;
            gap: 5px;
            margin-right: 20px;
        }

        .view-tab {
            background: #1a1a1a;
            border: 1px solid #333;
            color: #888;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .view-tab:hover { border-color: #555; color: #e0e0e0; }
        .view-tab.active { background: #333; color: #fff; border-color: #555; }

        select {
            background: #1a1a1a;
            border: 1px solid #333;
            color: #e0e0e0;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
        }

        .stats-bar {
            display: flex;
            gap: 30px;
            padding: 20px;
            background: #1a1a1a;
            border-radius: 12px;
            margin-bottom: 30px;
        }

        .stat { text-align: center; }
        .stat-value { font-size: 1.8rem; font-weight: 700; color: #4ade80; }
        .stat-label { font-size: 0.85rem; color: #888; margin-top: 4px; }

        .visualization {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 30px;
        }

        .funnel-container { width: 100%; }

        .funnel-row {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            cursor: pointer;
            padding: 8px;
            border-radius: 8px;
            transition: background 0.2s;
        }

        .funnel-row:hover { background: #252525; }

        .funnel-label {
            width: 180px;
            font-size: 14px;
            color: #e0e0e0;
            flex-shrink: 0;
        }

        .funnel-bar-container {
            flex: 1;
            height: 32px;
            background: #252525;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }

        .funnel-bar {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            padding-left: 10px;
        }

        .funnel-bar-text {
            color: white;
            font-size: 12px;
            font-weight: 600;
            white-space: nowrap;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }

        .funnel-amount {
            width: 120px;
            text-align: right;
            font-size: 14px;
            color: #4ade80;
            font-weight: 600;
            flex-shrink: 0;
            margin-left: 15px;
        }

        .funnel-pct {
            width: 60px;
            text-align: right;
            font-size: 12px;
            color: #888;
            flex-shrink: 0;
            margin-left: 10px;
        }

        .total-row {
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }

        .total-row .funnel-label { font-weight: 700; color: #4ade80; font-size: 16px; }
        .total-row .funnel-amount { font-size: 18px; }

        .tooltip {
            position: fixed;
            background: #252525;
            border: 1px solid #444;
            border-radius: 8px;
            padding: 15px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s;
            max-width: 400px;
            max-height: 450px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }

        .tooltip.visible { opacity: 1; }
        .tooltip.pinned { opacity: 1; pointer-events: auto; }
        .tooltip-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #444; padding-bottom: 8px; }
        .tooltip h3 { font-size: 14px; color: #fff; margin: 0; }
        .tooltip-close { background: none; border: none; color: #888; font-size: 18px; cursor: pointer; padding: 0 5px; }
        .tooltip-close:hover { color: #fff; }
        .tooltip-total { font-size: 1.2rem; color: #4ade80; margin-bottom: 10px; }
        .tooltip-transactions { font-size: 12px; }

        .tooltip-transaction {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #333;
            gap: 10px;
        }

        .tooltip-transaction:last-child { border-bottom: none; }
        .tooltip-date { color: #666; font-size: 11px; flex-shrink: 0; }
        .tooltip-merchant { color: #aaa; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .tooltip-amount { color: #4ade80; flex-shrink: 0; }
        .tooltip-more { color: #666; text-align: center; padding-top: 10px; font-style: italic; }
        .tooltip-expand {
            color: #06b6d4;
            text-align: center;
            padding: 10px;
            cursor: pointer;
            border-top: 1px solid #333;
            margin-top: 10px;
            font-size: 12px;
            transition: color 0.2s;
        }
        .tooltip-expand:hover { color: #22d3ee; }

        .no-data {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 200px;
            color: #666;
            font-size: 1.2rem;
        }

        .recurring-container { width: 100%; }

        .recurring-header {
            display: flex;
            padding: 10px 8px;
            border-bottom: 2px solid #333;
            margin-bottom: 10px;
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
        }

        .recurring-row {
            display: flex;
            align-items: center;
            padding: 12px 8px;
            border-radius: 8px;
            transition: background 0.2s;
        }

        .recurring-row:hover { background: #252525; }

        .recurring-name { flex: 2; font-size: 14px; color: #e0e0e0; }
        .recurring-category { flex: 1; font-size: 12px; color: #888; }
        .recurring-frequency { flex: 1; font-size: 14px; color: #06b6d4; text-align: center; }
        .recurring-avg { flex: 1; font-size: 14px; color: #888; text-align: right; }
        .recurring-total { flex: 1; font-size: 14px; color: #4ade80; font-weight: 600; text-align: right; }

        .recurring-summary {
            display: flex;
            justify-content: space-between;
            padding: 20px;
            background: #252525;
            border-radius: 8px;
            margin-top: 20px;
        }

        .recurring-summary-item { text-align: center; }
        .recurring-summary-value { font-size: 1.5rem; font-weight: 700; color: #f97316; }
        .recurring-summary-label { font-size: 0.8rem; color: #888; margin-top: 4px; }

        .hidden { display: none; }

        .dining-container { width: 100%; }

        .dining-stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }

        .dining-stat-card {
            background: #252525;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }

        .dining-stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #4ade80;
        }

        .dining-stat-value.warning { color: #f97316; }
        .dining-stat-value.danger { color: #ef4444; }
        .dining-stat-value.good { color: #22c55e; }

        .dining-stat-label {
            font-size: 0.75rem;
            color: #888;
            margin-top: 4px;
        }

        .dining-stat-target {
            font-size: 0.7rem;
            color: #666;
            margin-top: 2px;
        }

        .dining-section {
            margin-bottom: 25px;
        }

        .dining-section-title {
            font-size: 14px;
            font-weight: 600;
            color: #06b6d4;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #333;
        }

        .dining-distribution {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .dining-bucket {
            flex: 1;
            min-width: 120px;
            background: #252525;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }

        .dining-bucket-label {
            font-size: 12px;
            color: #888;
            margin-bottom: 5px;
        }

        .dining-bucket-count {
            font-size: 1.3rem;
            font-weight: 700;
            color: #e0e0e0;
        }

        .dining-bucket-pct {
            font-size: 11px;
            color: #666;
        }

        .dining-bar {
            height: 8px;
            background: #333;
            border-radius: 4px;
            margin-top: 8px;
            overflow: hidden;
        }

        .dining-bar-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        .dining-monthly-table {
            width: 100%;
            border-collapse: collapse;
        }

        .dining-monthly-table th,
        .dining-monthly-table td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }

        .dining-monthly-table th {
            color: #888;
            font-size: 12px;
            text-transform: uppercase;
            font-weight: 500;
        }

        .dining-monthly-table td {
            font-size: 14px;
        }

        .dining-monthly-table tr:hover {
            background: #252525;
        }

        .trend-up { color: #ef4444; }
        .trend-down { color: #22c55e; }
        .trend-flat { color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Budget Dashboard</h1>
            <div class="filters">
                <div class="view-tabs">
                    <button class="view-tab active" data-view="categories">Categories</button>
                    <button class="view-tab" data-view="dining">Dining</button>
                    <button class="view-tab" data-view="dog">Dog</button>
                    <button class="view-tab" data-view="subscriptions">Subscriptions</button>
                    <button class="view-tab" data-view="recurring">Recurring</button>
                </div>
                <select id="yearFilter"></select>
                <select id="monthFilter"></select>
            </div>
        </header>

        <div class="stats-bar">
            <div class="stat">
                <div class="stat-value" id="totalSpend">$0</div>
                <div class="stat-label">Total Spent</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="transactionCount">0</div>
                <div class="stat-label">Transactions</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="avgTransaction">$0</div>
                <div class="stat-label">Avg Transaction</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="topCategory">-</div>
                <div class="stat-label">Top Category</div>
            </div>
        </div>

        <div class="visualization">
            <div class="funnel-container" id="funnel"></div>
            <div class="dining-container hidden" id="dining"></div>
            <div class="dining-container hidden" id="dog"></div>
            <div class="recurring-container hidden" id="subscriptions"></div>
            <div class="recurring-container hidden" id="recurring"></div>
        </div>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <script>
        const DATA = ''' + json.dumps(data) + ''';

        const COLORS = {
            'Dining': '#ef4444',
            'Merchandise': '#f97316',
            'Grocery': '#eab308',
            'Airfare': '#22c55e',
            'Other Services': '#14b8a6',
            'Internet': '#06b6d4',
            'Professional Services': '#3b82f6',
            'Entertainment': '#8b5cf6',
            'Healthcare': '#ec4899',
            'Phone/Cable': '#f43f5e',
            'Gas/Automotive': '#84cc16',
            'Other': '#6b7280',
            'Other Travel': '#0ea5e9',
            'Lodging': '#a855f7'
        };

        const monthNames = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                           'July', 'August', 'September', 'October', 'November', 'December'];

        let currentYear = DATA.years[DATA.years.length - 1];
        let currentMonth = 'all';
        let pinnedCategory = null;
        let currentView = 'categories';
        let expandedTooltip = false;
        let currentTooltipData = null;

        // Known subscriptions with expected amounts and billing cycles
        // cycle: 'monthly', 'annual', 'biannual'
        // amount: expected charge amount
        // tolerance: how much variance to allow when matching
        const SUBSCRIPTIONS = [
            // Streaming & Entertainment
            { name: 'Netflix', patterns: ['NETFLIX'], category: 'Streaming', amount: 15.49, cycle: 'monthly', tolerance: 2 },
            { name: 'Spotify', patterns: ['SPOTIFY'], category: 'Streaming', amount: 10.99, cycle: 'monthly', tolerance: 2 },
            { name: 'Hulu', patterns: ['HULU'], category: 'Streaming', amount: 7.99, cycle: 'monthly', tolerance: 2 },

            // Software & Services
            { name: 'iCloud', patterns: ['ICLOUD', 'APPLE.COM/BILL'], category: 'Software', amount: 2.99, cycle: 'monthly', tolerance: 1 },
            { name: 'Google Storage', patterns: ['GOOGLE *CLOUD', 'GOOGLE STORAGE'], category: 'Software', amount: 2.99, cycle: 'monthly', tolerance: 1 },

            // Telecom
            { name: 'AT&T Wireless', patterns: ['AT&T'], category: 'Telecom', amount: 85, cycle: 'monthly', tolerance: 10 },

            // Insurance
            { name: 'State Farm', patterns: ['STATE FARM'], category: 'Insurance', amount: 55, cycle: 'monthly', tolerance: 5 },

            // Memberships
            { name: 'Gym Membership', patterns: ['GYM', 'FITNESS'], category: 'Membership', amount: 40, cycle: 'monthly', tolerance: 10 },
            { name: 'Audible', patterns: ['AUDIBLE'], category: 'Membership', amount: 14.95, cycle: 'monthly', tolerance: 2 },
        ];

        // Expected monthly budget for subscriptions
        const EXPECTED_MONTHLY = 235;

        // Identify recurring payments (merchants appearing 2+ times)
        function getRecurringPayments() {
            const allTransactions = [];
            Object.values(DATA.byMonth).forEach(month => {
                Object.entries(month.categories).forEach(([cat, catData]) => {
                    catData.transactions.forEach(txn => {
                        allTransactions.push({ ...txn, category: cat });
                    });
                });
            });

            // Group by merchant
            const byMerchant = {};
            allTransactions.forEach(txn => {
                const name = txn.Description;
                if (!byMerchant[name]) {
                    byMerchant[name] = { name, category: txn.category, transactions: [], total: 0 };
                }
                byMerchant[name].transactions.push(txn);
                byMerchant[name].total += txn.Amount;
            });

            // Filter to recurring (2+ occurrences) and calculate stats
            const recurring = Object.values(byMerchant)
                .filter(m => m.transactions.length >= 2)
                .map(m => ({
                    name: m.name,
                    category: m.category,
                    count: m.transactions.length,
                    total: Math.round(m.total * 100) / 100,
                    avg: Math.round((m.total / m.transactions.length) * 100) / 100,
                    transactions: m.transactions.sort((a, b) => new Date(b.Date) - new Date(a.Date))
                }))
                .sort((a, b) => b.total - a.total);

            return recurring;
        }

        function getSubscriptions() {
            const allTransactions = [];
            Object.values(DATA.byMonth).forEach(month => {
                Object.entries(month.categories).forEach(([cat, catData]) => {
                    catData.transactions.forEach(txn => {
                        allTransactions.push({ ...txn, category: cat });
                    });
                });
            });

            const results = [];

            SUBSCRIPTIONS.forEach(sub => {
                // Skip canceled/free subscriptions with $0 expected
                if (sub.amount === 0) {
                    results.push({
                        name: sub.name,
                        subCategory: sub.category,
                        cycle: sub.cycle,
                        expectedAmount: 0,
                        expectedMonthly: 0,
                        count: 0,
                        total: 0,
                        actualMonthly: 0,
                        status: 'inactive',
                        note: sub.note || 'Not active',
                        transactions: []
                    });
                    return;
                }

                // Find matching transactions within tolerance of expected amount
                const matches = allTransactions.filter(txn => {
                    if (txn.Amount <= 0) return false;
                    const matchesPattern = sub.patterns.some(pattern =>
                        txn.Description.toUpperCase().includes(pattern.toUpperCase())
                    );
                    if (!matchesPattern) return false;

                    // Check if amount is within tolerance
                    const diff = Math.abs(txn.Amount - sub.amount);
                    return diff <= sub.tolerance;
                });

                const total = matches.reduce((sum, t) => sum + t.Amount, 0);
                const expectedMonthly = sub.cycle === 'annual' ? sub.amount / 12 :
                                        sub.cycle === 'biannual' ? sub.amount / 6 : sub.amount;

                // Determine status
                let status = 'active';
                if (matches.length === 0) {
                    status = 'not-found';
                } else if (sub.cycle === 'monthly' && matches.length < 6) {
                    status = 'irregular';
                }

                results.push({
                    name: sub.name,
                    subCategory: sub.category,
                    cycle: sub.cycle,
                    expectedAmount: sub.amount,
                    expectedMonthly: Math.round(expectedMonthly * 100) / 100,
                    count: matches.length,
                    total: Math.round(total * 100) / 100,
                    actualMonthly: Math.round((total / 12) * 100) / 100,
                    status: status,
                    note: sub.note || '',
                    transactions: matches.sort((a, b) => new Date(b.Date) - new Date(a.Date))
                });
            });

            // Sort: active first, then by expected monthly cost descending
            return results.sort((a, b) => {
                if (a.status === 'inactive' && b.status !== 'inactive') return 1;
                if (b.status === 'inactive' && a.status !== 'inactive') return -1;
                return b.expectedMonthly - a.expectedMonthly;
            });
        }

        function initViewTabs() {
            document.querySelectorAll('.view-tab').forEach(tab => {
                tab.addEventListener('click', () => {
                    document.querySelectorAll('.view-tab').forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    currentView = tab.dataset.view;

                    document.getElementById('funnel').classList.toggle('hidden', currentView !== 'categories');
                    document.getElementById('dining').classList.toggle('hidden', currentView !== 'dining');
                    document.getElementById('dog').classList.toggle('hidden', currentView !== 'dog');
                    document.getElementById('subscriptions').classList.toggle('hidden', currentView !== 'subscriptions');
                    document.getElementById('recurring').classList.toggle('hidden', currentView !== 'recurring');

                    render();
                });
            });
        }

        function initFilters() {
            const yearSelect = document.getElementById('yearFilter');
            const monthSelect = document.getElementById('monthFilter');

            DATA.years.forEach(year => {
                const opt = document.createElement('option');
                opt.value = year;
                opt.textContent = year;
                yearSelect.appendChild(opt);
            });
            yearSelect.value = currentYear;

            updateMonthFilter();

            yearSelect.addEventListener('change', (e) => {
                currentYear = e.target.value;
                updateMonthFilter();
                currentMonth = 'all';
                monthSelect.value = 'all';
                render();
            });

            monthSelect.addEventListener('change', (e) => {
                currentMonth = e.target.value;
                render();
            });
        }

        function updateMonthFilter() {
            const monthSelect = document.getElementById('monthFilter');
            monthSelect.innerHTML = '<option value="all">All Months</option>';

            const monthsWithData = Object.keys(DATA.byMonth)
                .filter(ym => ym.startsWith(currentYear))
                .map(ym => parseInt(ym.split('-')[1]))
                .sort((a, b) => a - b);

            monthsWithData.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.toString().padStart(2, '0');
                opt.textContent = monthNames[m];
                monthSelect.appendChild(opt);
            });
        }

        function getFilteredData() {
            let relevantMonths = currentMonth === 'all'
                ? Object.keys(DATA.byMonth).filter(ym => ym.startsWith(currentYear))
                : (DATA.byMonth[`${currentYear}-${currentMonth}`] ? [`${currentYear}-${currentMonth}`] : []);

            const aggregated = { total: 0, categories: {} };

            relevantMonths.forEach(ym => {
                const monthData = DATA.byMonth[ym];
                aggregated.total += monthData.total;

                Object.entries(monthData.categories).forEach(([cat, catData]) => {
                    if (!aggregated.categories[cat]) {
                        aggregated.categories[cat] = { total: 0, count: 0, transactions: [] };
                    }
                    aggregated.categories[cat].total += catData.total;
                    aggregated.categories[cat].count += catData.count;
                    aggregated.categories[cat].transactions.push(...catData.transactions);
                });
            });

            aggregated.total = Math.round(aggregated.total * 100) / 100;
            Object.values(aggregated.categories).forEach(cat => {
                cat.total = Math.round(cat.total * 100) / 100;
            });

            return aggregated;
        }

        function updateStats(data) {
            const totalCount = Object.values(data.categories).reduce((sum, c) => sum + c.count, 0);
            const avgTxn = totalCount > 0 ? data.total / totalCount : 0;

            let topCat = '-', topAmount = 0;
            Object.entries(data.categories).forEach(([cat, catData]) => {
                if (catData.total > topAmount) {
                    topAmount = catData.total;
                    topCat = cat;
                }
            });

            document.getElementById('totalSpend').textContent = '$' + data.total.toLocaleString('en-US', {minimumFractionDigits: 2});
            document.getElementById('transactionCount').textContent = totalCount.toLocaleString();
            document.getElementById('avgTransaction').textContent = '$' + avgTxn.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            document.getElementById('topCategory').textContent = topCat;
        }

        function renderFunnel(data) {
            const container = document.getElementById('funnel');
            container.innerHTML = '';

            if (data.total === 0) {
                container.innerHTML = '<div class="no-data">No data for selected period</div>';
                return;
            }

            // Total row
            const totalRow = document.createElement('div');
            totalRow.className = 'funnel-row total-row';
            totalRow.innerHTML = `
                <div class="funnel-label">TOTAL SPENDING</div>
                <div class="funnel-bar-container">
                    <div class="funnel-bar" style="width: 100%; background: linear-gradient(90deg, #4ade80, #22c55e);">
                        <span class="funnel-bar-text">${data.total.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</span>
                    </div>
                </div>
                <div class="funnel-amount">$${data.total.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                <div class="funnel-pct">100%</div>
            `;
            container.appendChild(totalRow);

            // Category rows sorted by amount
            const sortedCategories = Object.entries(data.categories)
                .sort((a, b) => b[1].total - a[1].total);

            sortedCategories.forEach(([cat, catData]) => {
                const pct = (catData.total / data.total) * 100;
                const color = COLORS[cat] || '#6b7280';

                const row = document.createElement('div');
                row.className = 'funnel-row';
                row.innerHTML = `
                    <div class="funnel-label">${cat}</div>
                    <div class="funnel-bar-container">
                        <div class="funnel-bar" style="width: ${pct}%; background: ${color};">
                            ${pct > 8 ? `<span class="funnel-bar-text">${catData.count} txns</span>` : ''}
                        </div>
                    </div>
                    <div class="funnel-amount">$${catData.total.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    <div class="funnel-pct">${pct.toFixed(1)}%</div>
                `;

                row.addEventListener('mouseenter', (e) => { if (!pinnedCategory) showTooltip(e, cat, catData); });
                row.addEventListener('mousemove', (e) => { if (!pinnedCategory) moveTooltip(e); });
                row.addEventListener('mouseleave', () => { if (!pinnedCategory) hideTooltip(); });
                row.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (pinnedCategory === cat) {
                        unpinTooltip();
                    } else {
                        pinTooltip(e, cat, catData);
                    }
                });

                container.appendChild(row);
            });
        }

        function showTooltip(event, cat, catData, forceExpanded = false) {
            const tooltip = document.getElementById('tooltip');
            const sortedTxns = [...catData.transactions].sort((a, b) => b.Amount - a.Amount);
            const isExpanded = forceExpanded || expandedTooltip;
            const displayTxns = isExpanded ? sortedTxns : sortedTxns.slice(0, 20);

            // Store data for expansion
            currentTooltipData = { cat, catData };

            let html = `
                <div class="tooltip-header">
                    <h3>${cat}</h3>
                    <button class="tooltip-close" onclick="unpinTooltip()">&times;</button>
                </div>
                <div class="tooltip-total">$${catData.total.toLocaleString('en-US', {minimumFractionDigits: 2})} (${catData.count} transactions)</div>
                <div class="tooltip-transactions">
            `;

            displayTxns.forEach(txn => {
                html += `
                    <div class="tooltip-transaction">
                        <span class="tooltip-date">${txn.Date}</span>
                        <span class="tooltip-merchant">${txn.Description}</span>
                        <span class="tooltip-amount">$${txn.Amount.toFixed(2)}</span>
                    </div>
                `;
            });

            html += '</div>';

            if (sortedTxns.length > 20 && !isExpanded) {
                html += `<div class="tooltip-expand" onclick="event.stopPropagation(); expandTooltip()">▼ Show all ${sortedTxns.length} transactions</div>`;
            } else if (sortedTxns.length > 20 && isExpanded) {
                html += `<div class="tooltip-expand" onclick="event.stopPropagation(); collapseTooltip()">▲ Show less</div>`;
            }

            tooltip.innerHTML = html;
            tooltip.classList.add('visible');

            if (!forceExpanded) {
                moveTooltip(event);
            }
        }

        function expandTooltip() {
            if (currentTooltipData) {
                expandedTooltip = true;
                const tooltip = document.getElementById('tooltip');
                const rect = tooltip.getBoundingClientRect();
                showTooltip({ clientX: rect.left, clientY: rect.top }, currentTooltipData.cat, currentTooltipData.catData, true);
                // Keep position and pinned state
                tooltip.style.left = rect.left + 'px';
                tooltip.style.top = rect.top + 'px';
                tooltip.classList.add('pinned');
                // Increase max height for expanded view
                tooltip.style.maxHeight = '70vh';
            }
        }

        function collapseTooltip() {
            if (currentTooltipData) {
                expandedTooltip = false;
                const tooltip = document.getElementById('tooltip');
                const rect = tooltip.getBoundingClientRect();
                showTooltip({ clientX: rect.left, clientY: rect.top }, currentTooltipData.cat, currentTooltipData.catData, true);
                // Keep position and pinned state
                tooltip.style.left = rect.left + 'px';
                tooltip.style.top = rect.top + 'px';
                tooltip.classList.add('pinned');
                // Reset max height
                tooltip.style.maxHeight = '450px';
            }
        }

        function moveTooltip(event) {
            const tooltip = document.getElementById('tooltip');
            const padding = 15;
            let x = event.clientX + padding;
            let y = event.clientY + padding;

            const rect = tooltip.getBoundingClientRect();
            if (x + rect.width > window.innerWidth) x = event.clientX - rect.width - padding;
            if (y + rect.height > window.innerHeight) y = event.clientY - rect.height - padding;

            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
        }

        function hideTooltip() {
            document.getElementById('tooltip').classList.remove('visible');
        }

        function renderSubscriptions() {
            const container = document.getElementById('subscriptions');
            const subs = getSubscriptions();

            if (subs.length === 0) {
                container.innerHTML = '<div class="no-data">No subscriptions found</div>';
                return;
            }

            const activeSubs = subs.filter(s => s.status !== 'inactive');
            const totalActual = activeSubs.reduce((sum, s) => sum + s.total, 0);
            const expectedMonthlyTotal = activeSubs.reduce((sum, s) => sum + s.expectedMonthly, 0);
            const actualMonthlyTotal = activeSubs.reduce((sum, s) => sum + s.actualMonthly, 0);

            // Group by category
            const byCategory = {};
            subs.forEach(s => {
                if (!byCategory[s.subCategory]) byCategory[s.subCategory] = [];
                byCategory[s.subCategory].push(s);
            });

            let html = `
                <div class="recurring-summary" style="margin-bottom: 20px; margin-top: 0;">
                    <div class="recurring-summary-item">
                        <div class="recurring-summary-value">${activeSubs.filter(s => s.count > 0).length}/${activeSubs.length}</div>
                        <div class="recurring-summary-label">Found / Expected</div>
                    </div>
                    <div class="recurring-summary-item">
                        <div class="recurring-summary-value">$${expectedMonthlyTotal.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                        <div class="recurring-summary-label">Expected Monthly</div>
                    </div>
                    <div class="recurring-summary-item">
                        <div class="recurring-summary-value">$${actualMonthlyTotal.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                        <div class="recurring-summary-label">Actual Monthly Avg</div>
                    </div>
                    <div class="recurring-summary-item">
                        <div class="recurring-summary-value">$${totalActual.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                        <div class="recurring-summary-label">Total YTD</div>
                    </div>
                </div>

                <div class="recurring-header">
                    <div class="recurring-name">Subscription</div>
                    <div class="recurring-category">Cycle</div>
                    <div class="recurring-frequency">Found</div>
                    <div class="recurring-avg">Expected</div>
                    <div class="recurring-total">Actual YTD</div>
                </div>
            `;

            // Render by category
            Object.entries(byCategory).forEach(([cat, items]) => {
                if (cat === 'Canceled/Free') return; // Show at end

                const catExpected = items.reduce((sum, i) => sum + i.expectedMonthly, 0);
                html += `
                    <div style="margin-top: 20px; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #333;">
                        <span style="color: #06b6d4; font-weight: 600;">${cat}</span>
                        <span style="color: #888; float: right;">~$${catExpected.toFixed(2)}/mo expected</span>
                    </div>
                `;

                items.forEach(s => {
                    const statusIcon = s.status === 'active' ? '✓' : s.status === 'not-found' ? '?' : '~';
                    const statusColor = s.status === 'active' ? '#4ade80' : s.status === 'not-found' ? '#f97316' : '#eab308';
                    const cycleLabel = s.cycle === 'annual' ? '/yr' : s.cycle === 'biannual' ? '/6mo' : '/mo';

                    html += `
                        <div class="recurring-row" data-sub="${s.name}" style="opacity: ${s.status === 'inactive' ? 0.5 : 1}">
                            <div class="recurring-name">
                                <span style="color: ${statusColor}; margin-right: 8px;">${statusIcon}</span>
                                ${s.name}
                                ${s.note ? `<span style="color: #666; font-size: 11px; margin-left: 8px;">(${s.note})</span>` : ''}
                            </div>
                            <div class="recurring-category" style="color: #888;">${s.cycle}</div>
                            <div class="recurring-frequency">${s.count > 0 ? s.count + 'x' : '-'}</div>
                            <div class="recurring-avg">$${s.expectedAmount}${cycleLabel}</div>
                            <div class="recurring-total" style="color: ${s.count > 0 ? '#4ade80' : '#666'}">
                                ${s.count > 0 ? '$' + s.total.toLocaleString('en-US', {minimumFractionDigits: 2}) : '-'}
                            </div>
                        </div>
                    `;
                });
            });

            // Show canceled/free at end
            if (byCategory['Canceled/Free']) {
                html += `
                    <div style="margin-top: 30px; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #333;">
                        <span style="color: #666; font-weight: 600;">Canceled / Free</span>
                    </div>
                `;
                byCategory['Canceled/Free'].forEach(s => {
                    html += `
                        <div class="recurring-row" style="opacity: 0.5">
                            <div class="recurring-name" style="color: #666;">
                                <span style="margin-right: 8px;">✗</span>
                                ${s.name}
                                ${s.note ? `<span style="font-size: 11px; margin-left: 8px;">(${s.note})</span>` : ''}
                            </div>
                            <div class="recurring-category" style="color: #666;">-</div>
                            <div class="recurring-frequency">-</div>
                            <div class="recurring-avg">$0</div>
                            <div class="recurring-total" style="color: #666;">-</div>
                        </div>
                    `;
                });
            }

            container.innerHTML = html;

            // Add click handlers
            container.querySelectorAll('.recurring-row[data-sub]').forEach(row => {
                const subName = row.dataset.sub;
                const subData = subs.find(s => s.name === subName);
                if (!subData || subData.count === 0) return;

                row.style.cursor = 'pointer';
                row.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (pinnedCategory === subName) {
                        unpinTooltip();
                    } else {
                        showSubscriptionTooltip(e, subData);
                        pinnedCategory = subName;
                        document.getElementById('tooltip').classList.add('pinned');
                    }
                });
            });
        }

        function showSubscriptionTooltip(event, data) {
            const tooltip = document.getElementById('tooltip');
            const cycleLabel = data.cycle === 'annual' ? 'year' : data.cycle === 'biannual' ? '6 months' : 'month';

            let html = `
                <div class="tooltip-header">
                    <h3>${data.name}</h3>
                    <button class="tooltip-close" onclick="unpinTooltip()">&times;</button>
                </div>
                <div class="tooltip-total">$${data.total.toLocaleString('en-US', {minimumFractionDigits: 2})} YTD</div>
                <div style="color: #888; font-size: 12px; margin-bottom: 5px;">
                    Expected: $${data.expectedAmount}/${cycleLabel} (~$${data.expectedMonthly.toFixed(2)}/mo)
                </div>
                <div style="color: #888; font-size: 12px; margin-bottom: 10px;">
                    ${data.count} charges found | Actual avg: ~$${data.actualMonthly.toFixed(2)}/mo
                </div>
                <div class="tooltip-transactions">
            `;

            data.transactions.forEach(txn => {
                html += `
                    <div class="tooltip-transaction">
                        <span class="tooltip-date">${txn.Date}</span>
                        <span class="tooltip-merchant" style="flex: 1; font-size: 11px;">${txn.Description}</span>
                        <span class="tooltip-amount">$${txn.Amount.toFixed(2)}</span>
                    </div>
                `;
            });

            html += '</div>';
            tooltip.innerHTML = html;
            tooltip.classList.add('visible');

            const rect = tooltip.getBoundingClientRect();
            let x = event.clientX + 15;
            let y = event.clientY - 100;
            if (x + rect.width > window.innerWidth) x = event.clientX - rect.width - 15;
            if (y < 10) y = 10;
            if (y + rect.height > window.innerHeight - 10) y = window.innerHeight - rect.height - 10;
            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
        }

        function renderRecurring() {
            const container = document.getElementById('recurring');
            const recurring = getRecurringPayments();

            if (recurring.length === 0) {
                container.innerHTML = '<div class="no-data">No recurring payments found</div>';
                return;
            }

            const totalRecurring = recurring.reduce((sum, r) => sum + r.total, 0);
            const monthlyEstimate = totalRecurring / 12;

            let html = `
                <div class="recurring-header">
                    <div class="recurring-name">Merchant</div>
                    <div class="recurring-category">Category</div>
                    <div class="recurring-frequency">Frequency</div>
                    <div class="recurring-avg">Avg Amount</div>
                    <div class="recurring-total">Total</div>
                </div>
            `;

            recurring.forEach(r => {
                html += `
                    <div class="recurring-row" data-merchant="${r.name}">
                        <div class="recurring-name">${r.name}</div>
                        <div class="recurring-category">${r.category}</div>
                        <div class="recurring-frequency">${r.count}x</div>
                        <div class="recurring-avg">$${r.avg.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                        <div class="recurring-total">$${r.total.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    </div>
                `;
            });

            html += `
                <div class="recurring-summary">
                    <div class="recurring-summary-item">
                        <div class="recurring-summary-value">${recurring.length}</div>
                        <div class="recurring-summary-label">Recurring Merchants</div>
                    </div>
                    <div class="recurring-summary-item">
                        <div class="recurring-summary-value">$${totalRecurring.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                        <div class="recurring-summary-label">Total Recurring Spend</div>
                    </div>
                    <div class="recurring-summary-item">
                        <div class="recurring-summary-value">$${monthlyEstimate.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                        <div class="recurring-summary-label">Est. Monthly</div>
                    </div>
                </div>
            `;

            container.innerHTML = html;

            // Add click handlers for recurring rows
            container.querySelectorAll('.recurring-row').forEach(row => {
                const merchantName = row.dataset.merchant;
                const merchantData = recurring.find(r => r.name === merchantName);

                row.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (pinnedCategory === merchantName) {
                        unpinTooltip();
                    } else {
                        showRecurringTooltip(e, merchantData);
                        pinnedCategory = merchantName;
                        document.getElementById('tooltip').classList.add('pinned');
                    }
                });
            });
        }

        function showRecurringTooltip(event, data) {
            const tooltip = document.getElementById('tooltip');

            let html = `
                <div class="tooltip-header">
                    <h3>${data.name}</h3>
                    <button class="tooltip-close" onclick="unpinTooltip()">&times;</button>
                </div>
                <div class="tooltip-total">$${data.total.toLocaleString('en-US', {minimumFractionDigits: 2})} total (${data.count} charges)</div>
                <div style="color: #888; font-size: 12px; margin-bottom: 10px;">Category: ${data.category} | Avg: $${data.avg.toFixed(2)}</div>
                <div class="tooltip-transactions">
            `;

            data.transactions.forEach(txn => {
                html += `
                    <div class="tooltip-transaction">
                        <span class="tooltip-date">${txn.Date}</span>
                        <span class="tooltip-amount">$${txn.Amount.toFixed(2)}</span>
                    </div>
                `;
            });

            html += '</div>';
            tooltip.innerHTML = html;
            tooltip.classList.add('visible');

            // Position tooltip
            const rect = tooltip.getBoundingClientRect();
            let x = event.clientX + 15;
            let y = event.clientY - 100;
            if (x + rect.width > window.innerWidth) x = event.clientX - rect.width - 15;
            if (y < 10) y = 10;
            if (y + rect.height > window.innerHeight - 10) y = window.innerHeight - rect.height - 10;
            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
        }

        function pinTooltip(event, cat, catData) {
            pinnedCategory = cat;
            showTooltip(event, cat, catData);
            const tooltip = document.getElementById('tooltip');
            tooltip.classList.add('pinned');

            // Position it nicely for scrolling
            const rect = tooltip.getBoundingClientRect();
            let x = event.clientX + 15;
            let y = event.clientY - 100;
            if (x + rect.width > window.innerWidth) x = event.clientX - rect.width - 15;
            if (y < 10) y = 10;
            if (y + rect.height > window.innerHeight - 10) y = window.innerHeight - rect.height - 10;
            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
        }

        function unpinTooltip() {
            pinnedCategory = null;
            expandedTooltip = false;
            currentTooltipData = null;
            const tooltip = document.getElementById('tooltip');
            tooltip.classList.remove('pinned');
            tooltip.classList.remove('visible');
            tooltip.style.maxHeight = '450px';
        }

        // Close pinned tooltip when clicking outside
        document.addEventListener('click', (e) => {
            if (pinnedCategory && !e.target.closest('.tooltip') && !e.target.closest('.funnel-row') && !e.target.closest('.recurring-row')) {
                unpinTooltip();
            }
        });

        function getDiningData() {
            const allTransactions = [];

            // Get transactions based on current filter
            let relevantMonths = currentMonth === 'all'
                ? Object.keys(DATA.byMonth).filter(ym => ym.startsWith(currentYear))
                : (DATA.byMonth[`${currentYear}-${currentMonth}`] ? [`${currentYear}-${currentMonth}`] : []);

            relevantMonths.forEach(ym => {
                const monthData = DATA.byMonth[ym];
                if (monthData.categories['Dining']) {
                    monthData.categories['Dining'].transactions.forEach(txn => {
                        allTransactions.push({ ...txn, month: ym });
                    });
                }
            });

            return allTransactions.filter(t => t.Amount > 0);
        }

        function renderDining() {
            const container = document.getElementById('dining');
            const transactions = getDiningData();

            if (transactions.length === 0) {
                container.innerHTML = '<div class="no-data">No dining transactions for selected period</div>';
                return;
            }

            const total = transactions.reduce((sum, t) => sum + t.Amount, 0);
            const avg = total / transactions.length;
            const targetAvg = 25; // Target average per transaction
            const targetTotal = 800; // Monthly budget target

            // Calculate monthly data
            const byMonth = {};
            transactions.forEach(t => {
                if (!byMonth[t.month]) byMonth[t.month] = { transactions: [], total: 0 };
                byMonth[t.month].transactions.push(t);
                byMonth[t.month].total += t.Amount;
            });

            // Distribution buckets
            const buckets = [
                { label: 'Under $15', min: 0, max: 15, count: 0, color: '#22c55e' },
                { label: '$15 - $30', min: 15, max: 30, count: 0, color: '#84cc16' },
                { label: '$30 - $50', min: 30, max: 50, count: 0, color: '#eab308' },
                { label: '$50 - $75', min: 50, max: 75, count: 0, color: '#f97316' },
                { label: '$75 - $100', min: 75, max: 100, count: 0, color: '#ef4444' },
                { label: 'Over $100', min: 100, max: Infinity, count: 0, color: '#dc2626' }
            ];

            transactions.forEach(t => {
                for (const bucket of buckets) {
                    if (t.Amount >= bucket.min && t.Amount < bucket.max) {
                        bucket.count++;
                        break;
                    }
                }
            });

            const maxBucketCount = Math.max(...buckets.map(b => b.count));

            // Calculate trend (compare recent to older)
            const sortedMonths = Object.keys(byMonth).sort();
            let trendText = '';
            let trendClass = 'trend-flat';
            if (sortedMonths.length >= 2) {
                const recentMonths = sortedMonths.slice(-3);
                const olderMonths = sortedMonths.slice(0, -3);

                if (olderMonths.length > 0) {
                    const recentAvg = recentMonths.reduce((sum, m) => {
                        const monthTxns = byMonth[m].transactions;
                        return sum + (byMonth[m].total / monthTxns.length);
                    }, 0) / recentMonths.length;

                    const olderAvg = olderMonths.reduce((sum, m) => {
                        const monthTxns = byMonth[m].transactions;
                        return sum + (byMonth[m].total / monthTxns.length);
                    }, 0) / olderMonths.length;

                    const change = ((recentAvg - olderAvg) / olderAvg) * 100;
                    if (change > 5) {
                        trendText = `+${change.toFixed(0)}% vs earlier`;
                        trendClass = 'trend-up';
                    } else if (change < -5) {
                        trendText = `${change.toFixed(0)}% vs earlier`;
                        trendClass = 'trend-down';
                    } else {
                        trendText = 'Stable';
                        trendClass = 'trend-flat';
                    }
                }
            }

            // Determine value classes
            const avgClass = avg <= targetAvg ? 'good' : avg <= targetAvg * 1.3 ? 'warning' : 'danger';
            const monthlyAvg = Object.keys(byMonth).length > 0 ? total / Object.keys(byMonth).length : total;
            const totalClass = monthlyAvg <= targetTotal ? 'good' : monthlyAvg <= targetTotal * 1.2 ? 'warning' : 'danger';

            let html = `
                <div class="dining-stats">
                    <div class="dining-stat-card">
                        <div class="dining-stat-value ${avgClass}">$${avg.toFixed(2)}</div>
                        <div class="dining-stat-label">Avg per Transaction</div>
                        <div class="dining-stat-target">Target: $${targetAvg}</div>
                    </div>
                    <div class="dining-stat-card">
                        <div class="dining-stat-value">${transactions.length}</div>
                        <div class="dining-stat-label">Total Transactions</div>
                        <div class="dining-stat-target">${(transactions.length / Object.keys(byMonth).length).toFixed(1)}/month avg</div>
                    </div>
                    <div class="dining-stat-card">
                        <div class="dining-stat-value ${totalClass}">$${total.toFixed(2)}</div>
                        <div class="dining-stat-label">Total Spent</div>
                        <div class="dining-stat-target">Target: $${targetTotal}/mo</div>
                    </div>
                    <div class="dining-stat-card">
                        <div class="dining-stat-value ${trendClass}">${trendText || 'N/A'}</div>
                        <div class="dining-stat-label">Avg Trend</div>
                        <div class="dining-stat-target">Recent vs earlier months</div>
                    </div>
                </div>

                <div class="dining-section">
                    <div class="dining-section-title">Transaction Size Distribution</div>
                    <div class="dining-distribution">
            `;

            buckets.forEach(bucket => {
                const pct = transactions.length > 0 ? (bucket.count / transactions.length * 100).toFixed(0) : 0;
                const barWidth = maxBucketCount > 0 ? (bucket.count / maxBucketCount * 100) : 0;
                html += `
                    <div class="dining-bucket">
                        <div class="dining-bucket-label">${bucket.label}</div>
                        <div class="dining-bucket-count">${bucket.count}</div>
                        <div class="dining-bucket-pct">${pct}%</div>
                        <div class="dining-bar">
                            <div class="dining-bar-fill" style="width: ${barWidth}%; background: ${bucket.color};"></div>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>

                <div class="dining-section">
                    <div class="dining-section-title">Monthly Breakdown</div>
                    <table class="dining-monthly-table">
                        <thead>
                            <tr>
                                <th>Month</th>
                                <th>Transactions</th>
                                <th>Avg/Transaction</th>
                                <th>Total</th>
                                <th>vs Target</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            sortedMonths.forEach(month => {
                const data = byMonth[month];
                const monthAvg = data.total / data.transactions.length;
                const vsTarget = data.total - targetTotal;
                const vsTargetClass = vsTarget <= 0 ? 'trend-down' : 'trend-up';
                const avgVsTarget = monthAvg - targetAvg;
                const avgClass = avgVsTarget <= 0 ? 'trend-down' : avgVsTarget <= 5 ? 'trend-flat' : 'trend-up';

                html += `
                    <tr>
                        <td>${month}</td>
                        <td>${data.transactions.length}</td>
                        <td class="${avgClass}">$${monthAvg.toFixed(2)}</td>
                        <td>$${data.total.toFixed(2)}</td>
                        <td class="${vsTargetClass}">${vsTarget >= 0 ? '+' : ''}$${vsTarget.toFixed(0)}</td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                </div>

                <div class="dining-section">
                    <div class="dining-section-title">High-Value Transactions (Over $75)</div>
            `;

            const highValue = transactions.filter(t => t.Amount >= 75).sort((a, b) => b.Amount - a.Amount);
            if (highValue.length === 0) {
                html += '<div style="color: #666; padding: 10px;">No transactions over $75 - great job!</div>';
            } else {
                html += '<div style="max-height: 200px; overflow-y: auto;">';
                highValue.slice(0, 15).forEach(t => {
                    html += `
                        <div class="recurring-row" style="padding: 8px;">
                            <div class="recurring-name">${t.Description}</div>
                            <div class="recurring-category" style="color: #666;">${t.Date}</div>
                            <div class="recurring-total" style="color: #ef4444;">$${t.Amount.toFixed(2)}</div>
                        </div>
                    `;
                });
                html += '</div>';
            }

            html += '</div>';

            container.innerHTML = html;
        }

        // Dog spending patterns - matches pet stores, vet, pet meds
        // Excludes false positives like "Hot Dogs" restaurants and "BrewDog" brewery
        const DOG_PATTERNS = [
            { pattern: /petsmart/i, category: 'Pet Store' },
            { pattern: /petco/i, category: 'Pet Store' },
            { pattern: /pet\\s?supplies/i, category: 'Pet Store' },
            { pattern: /chewy/i, category: 'Pet Store' },
            { pattern: /petmed/i, category: 'Medications' },
            { pattern: /vet|veterinar/i, category: 'Vet' },
            { pattern: /animal\\s?hospital/i, category: 'Vet' },
            { pattern: /rover\\.com/i, category: 'Services' },
            { pattern: /wag\\!/i, category: 'Services' },
            { pattern: /groom/i, category: 'Grooming' },
            { pattern: /kennel|boarding/i, category: 'Boarding' },
            { pattern: /dog\\s?daycare/i, category: 'Daycare' },
            { pattern: /bark\\s?box/i, category: 'Subscription' },
        ];

        // Patterns to exclude (false positives)
        const DOG_EXCLUDE_PATTERNS = [
            /hot\\s?dog/i,
            /brewdog/i,
            /dog\\s?haus/i,
        ];

        function getDogData() {
            const allTransactions = [];

            // Get all transactions
            Object.values(DATA.byMonth).forEach(month => {
                Object.entries(month.categories).forEach(([cat, catData]) => {
                    catData.transactions.forEach(txn => {
                        allTransactions.push({ ...txn, originalCategory: cat });
                    });
                });
            });

            // Filter to dog-related transactions
            const dogTransactions = allTransactions.filter(txn => {
                if (txn.Amount <= 0) return false;
                const desc = txn.Description;

                // Check exclusions first
                if (DOG_EXCLUDE_PATTERNS.some(p => p.test(desc))) return false;

                // Check if matches any dog pattern
                for (const { pattern, category } of DOG_PATTERNS) {
                    if (pattern.test(desc)) {
                        txn.dogCategory = category;
                        return true;
                    }
                }
                return false;
            });

            return dogTransactions;
        }

        function renderDog() {
            const container = document.getElementById('dog');
            const transactions = getDogData();

            if (transactions.length === 0) {
                container.innerHTML = '<div class="no-data">No dog-related transactions found</div>';
                return;
            }

            const total = transactions.reduce((sum, t) => sum + t.Amount, 0);
            const avg = total / transactions.length;

            // Group by dog category
            const byCategory = {};
            transactions.forEach(t => {
                const cat = t.dogCategory || 'Other';
                if (!byCategory[cat]) byCategory[cat] = { transactions: [], total: 0 };
                byCategory[cat].transactions.push(t);
                byCategory[cat].total += t.Amount;
            });

            // Group by month
            const byMonth = {};
            transactions.forEach(t => {
                const date = new Date(t.Date);
                const ym = date.getFullYear() + '-' + String(date.getMonth() + 1).padStart(2, '0');
                if (!byMonth[ym]) byMonth[ym] = { transactions: [], total: 0 };
                byMonth[ym].transactions.push(t);
                byMonth[ym].total += t.Amount;
            });

            const monthlyAvg = Object.keys(byMonth).length > 0 ? total / Object.keys(byMonth).length : total;

            let html = `
                <div class="dining-stats">
                    <div class="dining-stat-card">
                        <div class="dining-stat-value">$${total.toFixed(2)}</div>
                        <div class="dining-stat-label">Total Dog Spending</div>
                        <div class="dining-stat-target">YTD</div>
                    </div>
                    <div class="dining-stat-card">
                        <div class="dining-stat-value">${transactions.length}</div>
                        <div class="dining-stat-label">Transactions</div>
                        <div class="dining-stat-target">${(transactions.length / Object.keys(byMonth).length).toFixed(1)}/month</div>
                    </div>
                    <div class="dining-stat-card">
                        <div class="dining-stat-value">$${monthlyAvg.toFixed(2)}</div>
                        <div class="dining-stat-label">Monthly Average</div>
                        <div class="dining-stat-target">Over ${Object.keys(byMonth).length} months</div>
                    </div>
                    <div class="dining-stat-card">
                        <div class="dining-stat-value">$${avg.toFixed(2)}</div>
                        <div class="dining-stat-label">Avg per Transaction</div>
                        <div class="dining-stat-target"></div>
                    </div>
                </div>

                <div class="dining-section">
                    <div class="dining-section-title">Spending by Type</div>
                    <div class="dining-distribution">
            `;

            // Sort categories by total
            const sortedCategories = Object.entries(byCategory).sort((a, b) => b[1].total - a[1].total);
            const maxCatTotal = Math.max(...sortedCategories.map(([_, d]) => d.total));

            const catColors = {
                'Pet Store': '#22c55e',
                'Vet': '#ef4444',
                'Medications': '#f97316',
                'Grooming': '#8b5cf6',
                'Services': '#06b6d4',
                'Boarding': '#eab308',
                'Daycare': '#ec4899',
                'Subscription': '#3b82f6',
                'Other': '#6b7280'
            };

            sortedCategories.forEach(([cat, data]) => {
                const pct = (data.total / total * 100).toFixed(0);
                const barWidth = maxCatTotal > 0 ? (data.total / maxCatTotal * 100) : 0;
                const color = catColors[cat] || '#6b7280';
                html += `
                    <div class="dining-bucket" style="min-width: 140px;">
                        <div class="dining-bucket-label">${cat}</div>
                        <div class="dining-bucket-count">$${data.total.toFixed(0)}</div>
                        <div class="dining-bucket-pct">${pct}% (${data.transactions.length} txns)</div>
                        <div class="dining-bar">
                            <div class="dining-bar-fill" style="width: ${barWidth}%; background: ${color};"></div>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>

                <div class="dining-section">
                    <div class="dining-section-title">Monthly Breakdown</div>
                    <table class="dining-monthly-table">
                        <thead>
                            <tr>
                                <th>Month</th>
                                <th>Transactions</th>
                                <th>Total</th>
                                <th>Top Merchant</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            const sortedMonths = Object.keys(byMonth).sort();
            sortedMonths.forEach(month => {
                const data = byMonth[month];
                // Find top merchant this month
                const merchantTotals = {};
                data.transactions.forEach(t => {
                    merchantTotals[t.Description] = (merchantTotals[t.Description] || 0) + t.Amount;
                });
                const topMerchant = Object.entries(merchantTotals).sort((a, b) => b[1] - a[1])[0];

                html += `
                    <tr>
                        <td>${month}</td>
                        <td>${data.transactions.length}</td>
                        <td style="color: #4ade80;">$${data.total.toFixed(2)}</td>
                        <td style="color: #888; font-size: 12px;">${topMerchant ? topMerchant[0] : '-'}</td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                </div>

                <div class="dining-section">
                    <div class="dining-section-title">All Dog Transactions</div>
                    <div style="max-height: 300px; overflow-y: auto;">
            `;

            // Sort by date descending
            const sortedTxns = [...transactions].sort((a, b) => new Date(b.Date) - new Date(a.Date));
            sortedTxns.forEach(t => {
                const catColor = catColors[t.dogCategory] || '#6b7280';
                html += `
                    <div class="recurring-row" style="padding: 8px;">
                        <div class="recurring-name">${t.Description}</div>
                        <div class="recurring-category" style="color: ${catColor};">${t.dogCategory}</div>
                        <div class="recurring-avg" style="color: #666;">${t.Date}</div>
                        <div class="recurring-total">$${t.Amount.toFixed(2)}</div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;

            container.innerHTML = html;
        }

        function render() {
            unpinTooltip();
            const data = getFilteredData();
            updateStats(data);

            if (currentView === 'categories') {
                renderFunnel(data);
            } else if (currentView === 'dining') {
                renderDining();
            } else if (currentView === 'dog') {
                renderDog();
            } else if (currentView === 'subscriptions') {
                renderSubscriptions();
            } else if (currentView === 'recurring') {
                renderRecurring();
            }
        }

        initFilters();
        initViewTabs();
        render();
    </script>
</body>
</html>'''

    return html_template

def main():
    print("Loading transaction data...")
    df = load_transactions()

    print("Processing data...")
    data = process_data(df)

    print("Generating HTML dashboard...")
    html = generate_html(data)

    REPORTS_DIR.mkdir(exist_ok=True)
    output_path = REPORTS_DIR / "dashboard.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nDashboard generated: {output_path}")

if __name__ == "__main__":
    main()

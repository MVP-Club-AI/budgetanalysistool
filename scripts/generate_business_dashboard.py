#!/usr/bin/env python3
"""
Generate Business Expenses Dashboard
Tracks development costs for a side project.

Customize the `categorize_business_expense()` function to match
the services and tools you use for your project.
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
    """Load and process transaction data from CSV."""
    all_dfs = []

    for csv_path in DATA_DIR.glob('*.csv'):
        df = pd.read_csv(csv_path)
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        all_dfs.append(df)

    if not all_dfs:
        raise ValueError("No valid CSV files found in data directory")

    df = pd.concat(all_dfs, ignore_index=True)
    df['Year'] = df['Date'].dt.year.astype(str)
    df['Month'] = df['Date'].dt.month.astype(str).str.zfill(2)
    df['YearMonth'] = df['Year'] + '-' + df['Month']

    return df

def categorize_business_expense(description):
    """Categorize a transaction as a business expense and return service name.

    Customize this function with the services and tools you use.
    Returns (service_name, category) or (None, None) if not a business expense.
    """
    desc_upper = description.upper()

    # Map patterns to service names and categories
    # Add your own services here
    patterns = [
        (['EXAMPLE HOSTING'], 'Hosting Provider', 'Infrastructure'),
        (['EXAMPLE API'], 'API Service', 'Infrastructure'),
        (['EXAMPLE DOMAIN'], 'Domain Registrar', 'Infrastructure'),
        (['EXAMPLE DESIGN'], 'Design Tool', 'Art/Assets'),
    ]

    for keywords, service, category in patterns:
        for keyword in keywords:
            if keyword in desc_upper:
                return service, category

    return None, None

def process_business_data(df):
    """Extract and process business-related transactions."""
    transactions = []

    for _, row in df.iterrows():
        if row['Amount'] <= 0:
            continue

        service, category = categorize_business_expense(row['Description'])
        if service:
            transactions.append({
                'date': row['Date'].strftime('%m/%d/%Y'),
                'yearMonth': row['YearMonth'],
                'amount': round(row['Amount'], 2),
                'description': row['Description'],
                'service': service,
                'category': category
            })

    refunds = []
    for _, row in df.iterrows():
        if row['Amount'] >= 0:
            continue
        service, category = categorize_business_expense(row['Description'])
        if service:
            refunds.append({
                'date': row['Date'].strftime('%m/%d/%Y'),
                'yearMonth': row['YearMonth'],
                'amount': round(row['Amount'], 2),
                'description': row['Description'],
                'service': service,
                'category': category
            })

    return {
        'transactions': transactions,
        'refunds': refunds,
        'years': sorted(df['Year'].unique().tolist()),
    }

def generate_html(data):
    """Generate the business dashboard HTML."""

    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Side Project - Business Expenses</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 100%);
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

        .logo {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #8b5cf6, #06b6d4);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }

        h1 { font-size: 1.5rem; font-weight: 600; color: #fff; }
        .subtitle { font-size: 0.85rem; color: #888; margin-top: 2px; }

        .filters { display: flex; gap: 15px; align-items: center; }

        select {
            background: #1a1a1a;
            border: 1px solid #333;
            color: #e0e0e0;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
        }

        .back-link {
            color: #06b6d4;
            text-decoration: none;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .back-link:hover { color: #22d3ee; }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid #333;
        }

        .stat-card.highlight {
            border-color: #8b5cf6;
            background: linear-gradient(135deg, #1a1a2e 0%, #1a1a1a 100%);
        }

        .stat-value { font-size: 2rem; font-weight: 700; color: #4ade80; }
        .stat-value.expense { color: #f97316; }
        .stat-value.neutral { color: #06b6d4; }
        .stat-label { font-size: 0.85rem; color: #888; margin-top: 4px; }
        .stat-sublabel { font-size: 0.75rem; color: #666; margin-top: 2px; }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }

        .panel {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #333;
        }

        .panel-title {
            font-size: 14px;
            font-weight: 600;
            color: #06b6d4;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #333;
        }

        .service-row {
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #252525;
        }

        .service-row:last-child { border-bottom: none; }

        .service-icon {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            margin-right: 12px;
            flex-shrink: 0;
        }

        .service-info { flex: 1; }
        .service-name { font-size: 14px; color: #e0e0e0; }
        .service-category { font-size: 11px; color: #666; }

        .service-stats { text-align: right; }
        .service-total { font-size: 14px; color: #4ade80; font-weight: 600; }
        .service-monthly { font-size: 11px; color: #888; }

        .service-bar {
            width: 100px;
            height: 6px;
            background: #252525;
            border-radius: 3px;
            margin-left: 15px;
            overflow: hidden;
        }

        .service-bar-fill {
            height: 100%;
            border-radius: 3px;
            transition: width 0.3s ease;
        }

        .month-row {
            display: flex;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #252525;
        }

        .month-row:last-child { border-bottom: none; }

        .month-name { width: 100px; font-size: 14px; color: #e0e0e0; }
        .month-bar-container { flex: 1; margin: 0 15px; }

        .month-bar {
            height: 24px;
            background: #252525;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }

        .month-bar-fill {
            height: 100%;
            border-radius: 4px;
            display: flex;
            align-items: center;
            padding-left: 8px;
        }

        .month-bar-text {
            color: white;
            font-size: 11px;
            font-weight: 600;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }

        .month-total { width: 80px; text-align: right; font-size: 14px; color: #4ade80; }
        .month-change { width: 60px; text-align: right; font-size: 12px; }
        .month-change.up { color: #ef4444; }
        .month-change.down { color: #22c55e; }
        .month-change.flat { color: #888; }

        .full-width { grid-column: 1 / -1; }

        .transactions-table {
            width: 100%;
            border-collapse: collapse;
        }

        .transactions-table th,
        .transactions-table td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #252525;
        }

        .transactions-table th {
            color: #888;
            font-size: 11px;
            text-transform: uppercase;
            font-weight: 500;
        }

        .transactions-table td { font-size: 13px; }
        .transactions-table tr:hover { background: #252525; }

        .pnl-section {
            margin-top: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #1a1a2e 0%, #1a1a1a 100%);
            border-radius: 12px;
            border: 1px solid #8b5cf6;
        }

        .pnl-title {
            font-size: 16px;
            font-weight: 600;
            color: #8b5cf6;
            margin-bottom: 20px;
        }

        .pnl-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 30px;
            text-align: center;
        }

        .pnl-item { }
        .pnl-value { font-size: 1.8rem; font-weight: 700; }
        .pnl-value.revenue { color: #22c55e; }
        .pnl-value.expenses { color: #f97316; }
        .pnl-value.loss { color: #ef4444; }
        .pnl-value.profit { color: #4ade80; }
        .pnl-label { font-size: 0.85rem; color: #888; margin-top: 4px; }

        .no-data {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 200px;
            color: #666;
            font-size: 1rem;
        }

        .scrollable { max-height: 400px; overflow-y: auto; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">
                <div class="logo-icon">💼</div>
                <div>
                    <h1>Side Project</h1>
                    <div class="subtitle">Business Expenses Dashboard</div>
                </div>
            </div>
            <div class="filters">
                <a href="dashboard.html" class="back-link">&larr; Personal Dashboard</a>
                <select id="yearFilter"></select>
                <select id="monthFilter"></select>
            </div>
        </header>

        <div class="stats-grid" id="statsGrid"></div>

        <div class="dashboard-grid">
            <div class="panel">
                <div class="panel-title">Cost by Service</div>
                <div id="serviceBreakdown"></div>
            </div>
            <div class="panel">
                <div class="panel-title">Monthly Trend</div>
                <div id="monthlyTrend" class="scrollable"></div>
            </div>
        </div>

        <div class="panel full-width">
            <div class="panel-title">All Transactions</div>
            <div id="transactionsList" class="scrollable"></div>
        </div>

        <div class="pnl-section">
            <div class="pnl-title">Profit & Loss (YTD)</div>
            <div class="pnl-grid" id="pnlGrid"></div>
        </div>
    </div>

    <script>
        const DATA = ''' + json.dumps(data) + ''';

        const SERVICE_COLORS = {
            'Hosting Provider': '#000000',
            'API Service': '#8b5cf6',
            'Domain Registrar': '#333333',
            'Design Tool': '#06b6d4',
        };

        const SERVICE_ICONS = {
            'Hosting Provider': '▲',
            'API Service': '⚡',
            'Domain Registrar': '🌐',
            'Design Tool': '🎨',
        };

        const monthNames = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

        let currentYear = DATA.years[DATA.years.length - 1];
        let currentMonth = 'all';

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

            const monthsWithData = [...new Set(
                DATA.transactions
                    .filter(t => t.yearMonth.startsWith(currentYear))
                    .map(t => parseInt(t.yearMonth.split('-')[1]))
            )].sort((a, b) => a - b);

            monthsWithData.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.toString().padStart(2, '0');
                opt.textContent = monthNames[m];
                monthSelect.appendChild(opt);
            });
        }

        function getFilteredTransactions() {
            return DATA.transactions.filter(t => {
                if (currentMonth === 'all') {
                    return t.yearMonth.startsWith(currentYear);
                }
                return t.yearMonth === `${currentYear}-${currentMonth}`;
            });
        }

        function renderStats(transactions) {
            const total = transactions.reduce((sum, t) => sum + t.amount, 0);
            const monthsActive = new Set(transactions.map(t => t.yearMonth)).size || 1;
            const monthlyAvg = total / monthsActive;
            const serviceCount = new Set(transactions.map(t => t.service)).size;

            const allMonths = [...new Set(DATA.transactions.map(t => t.yearMonth))].sort();
            const currentMonthKey = currentMonth === 'all'
                ? allMonths.filter(m => m.startsWith(currentYear)).pop()
                : `${currentYear}-${currentMonth}`;
            const currentIdx = allMonths.indexOf(currentMonthKey);
            const prevMonthKey = currentIdx > 0 ? allMonths[currentIdx - 1] : null;

            let momChange = null;
            if (prevMonthKey) {
                const currTotal = DATA.transactions.filter(t => t.yearMonth === currentMonthKey).reduce((s, t) => s + t.amount, 0);
                const prevTotal = DATA.transactions.filter(t => t.yearMonth === prevMonthKey).reduce((s, t) => s + t.amount, 0);
                if (prevTotal > 0) {
                    momChange = ((currTotal - prevTotal) / prevTotal) * 100;
                }
            }

            const statsGrid = document.getElementById('statsGrid');
            statsGrid.innerHTML = `
                <div class="stat-card highlight">
                    <div class="stat-value expense">$${total.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    <div class="stat-label">Total Expenses</div>
                    <div class="stat-sublabel">${currentMonth === 'all' ? 'Year to Date' : monthNames[parseInt(currentMonth)] + ' ' + currentYear}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value neutral">$${monthlyAvg.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    <div class="stat-label">Monthly Average</div>
                    <div class="stat-sublabel">Over ${monthsActive} month${monthsActive > 1 ? 's' : ''}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value neutral">${serviceCount}</div>
                    <div class="stat-label">Active Services</div>
                    <div class="stat-sublabel">Recurring subscriptions</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value ${momChange === null ? 'neutral' : momChange > 0 ? 'expense' : ''}" style="color: ${momChange === null ? '#888' : momChange > 0 ? '#ef4444' : '#22c55e'}">
                        ${momChange === null ? 'N/A' : (momChange > 0 ? '+' : '') + momChange.toFixed(0) + '%'}
                    </div>
                    <div class="stat-label">Month-over-Month</div>
                    <div class="stat-sublabel">Cost change</div>
                </div>
            `;
        }

        function renderServiceBreakdown(transactions) {
            const byService = {};
            transactions.forEach(t => {
                if (!byService[t.service]) {
                    byService[t.service] = { total: 0, count: 0, category: t.category };
                }
                byService[t.service].total += t.amount;
                byService[t.service].count++;
            });

            const sorted = Object.entries(byService).sort((a, b) => b[1].total - a[1].total);
            const maxTotal = sorted.length > 0 ? sorted[0][1].total : 1;
            const grandTotal = sorted.reduce((sum, [_, d]) => sum + d.total, 0);
            const monthsActive = new Set(transactions.map(t => t.yearMonth)).size || 1;

            const container = document.getElementById('serviceBreakdown');

            if (sorted.length === 0) {
                container.innerHTML = '<div class="no-data">No expenses in this period</div>';
                return;
            }

            container.innerHTML = sorted.map(([service, data]) => {
                const pct = (data.total / grandTotal * 100).toFixed(0);
                const barWidth = (data.total / maxTotal * 100);
                const color = SERVICE_COLORS[service] || '#6b7280';
                const icon = SERVICE_ICONS[service] || '📦';
                const monthly = data.total / monthsActive;

                return `
                    <div class="service-row">
                        <div class="service-icon" style="background: ${color};">${icon}</div>
                        <div class="service-info">
                            <div class="service-name">${service}</div>
                            <div class="service-category">${data.category}</div>
                        </div>
                        <div class="service-stats">
                            <div class="service-total">$${data.total.toFixed(2)}</div>
                            <div class="service-monthly">~$${monthly.toFixed(0)}/mo</div>
                        </div>
                        <div class="service-bar">
                            <div class="service-bar-fill" style="width: ${barWidth}%; background: ${color};"></div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function renderMonthlyTrend(transactions) {
            const byMonth = {};
            DATA.transactions.filter(t => t.yearMonth.startsWith(currentYear)).forEach(t => {
                if (!byMonth[t.yearMonth]) byMonth[t.yearMonth] = 0;
                byMonth[t.yearMonth] += t.amount;
            });

            const months = Object.keys(byMonth).sort();
            const maxTotal = Math.max(...Object.values(byMonth), 1);

            const container = document.getElementById('monthlyTrend');

            if (months.length === 0) {
                container.innerHTML = '<div class="no-data">No data for this year</div>';
                return;
            }

            container.innerHTML = months.map((ym, idx) => {
                const [year, month] = ym.split('-');
                const total = byMonth[ym];
                const barWidth = (total / maxTotal * 100);
                const prevTotal = idx > 0 ? byMonth[months[idx - 1]] : null;

                let changeHtml = '';
                if (prevTotal !== null) {
                    const change = ((total - prevTotal) / prevTotal) * 100;
                    const changeClass = change > 5 ? 'up' : change < -5 ? 'down' : 'flat';
                    changeHtml = `<span class="month-change ${changeClass}">${change > 0 ? '+' : ''}${change.toFixed(0)}%</span>`;
                }

                return `
                    <div class="month-row">
                        <div class="month-name">${monthNames[parseInt(month)]} ${year}</div>
                        <div class="month-bar-container">
                            <div class="month-bar">
                                <div class="month-bar-fill" style="width: ${barWidth}%; background: linear-gradient(90deg, #8b5cf6, #06b6d4);">
                                    <span class="month-bar-text">$${total.toFixed(0)}</span>
                                </div>
                            </div>
                        </div>
                        <div class="month-total">$${total.toFixed(2)}</div>
                        ${changeHtml}
                    </div>
                `;
            }).join('');
        }

        function renderTransactions(transactions) {
            const container = document.getElementById('transactionsList');
            const sorted = [...transactions].sort((a, b) => new Date(b.date) - new Date(a.date));

            if (sorted.length === 0) {
                container.innerHTML = '<div class="no-data">No transactions in this period</div>';
                return;
            }

            container.innerHTML = `
                <table class="transactions-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Service</th>
                            <th>Description</th>
                            <th>Category</th>
                            <th style="text-align: right;">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sorted.map(t => `
                            <tr>
                                <td style="color: #888;">${t.date}</td>
                                <td>
                                    <span style="color: ${SERVICE_COLORS[t.service] || '#888'};">${SERVICE_ICONS[t.service] || '📦'}</span>
                                    ${t.service}
                                </td>
                                <td style="color: #666; font-size: 12px;">${t.description}</td>
                                <td style="color: #888;">${t.category}</td>
                                <td style="text-align: right; color: #4ade80;">$${t.amount.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }

        function renderPnL(transactions) {
            const totalExpenses = transactions.reduce((sum, t) => sum + t.amount, 0);
            const revenue = 0; // No revenue yet
            const netIncome = revenue - totalExpenses;

            const container = document.getElementById('pnlGrid');
            container.innerHTML = `
                <div class="pnl-item">
                    <div class="pnl-value revenue">$${revenue.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    <div class="pnl-label">Revenue</div>
                </div>
                <div class="pnl-item">
                    <div class="pnl-value expenses">$${totalExpenses.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    <div class="pnl-label">Expenses</div>
                </div>
                <div class="pnl-item">
                    <div class="pnl-value ${netIncome >= 0 ? 'profit' : 'loss'}">
                        ${netIncome >= 0 ? '' : '-'}$${Math.abs(netIncome).toLocaleString('en-US', {minimumFractionDigits: 2})}
                    </div>
                    <div class="pnl-label">Net Income</div>
                </div>
            `;
        }

        function render() {
            const transactions = getFilteredTransactions();
            renderStats(transactions);
            renderServiceBreakdown(transactions);
            renderMonthlyTrend(transactions);
            renderTransactions(transactions);
            renderPnL(transactions);
        }

        initFilters();
        render();
    </script>
</body>
</html>'''

    return html_template

def main():
    print("Loading transaction data...")
    df = load_transactions()

    print("Extracting business expenses...")
    data = process_business_data(df)

    print(f"Found {len(data['transactions'])} business transactions")

    print("Generating HTML dashboard...")
    html = generate_html(data)

    REPORTS_DIR.mkdir(exist_ok=True)
    output_path = REPORTS_DIR / "business-dashboard.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nBusiness dashboard generated: {output_path}")

if __name__ == "__main__":
    main()

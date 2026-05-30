---
name: xero-db-skill
description: >
  Answer financial analysis questions by fetching live data from the Xero accounting API.
  Use this skill whenever the user asks about invoices, unpaid bills, AR/AP aging, customers,
  suppliers, chart of accounts, bank transactions, payments, credit notes, profit & loss,
  balance sheet, trial balance, fixed assets, or any other Xero accounting data — even if
  they don't say "Xero" explicitly. If the user has a Xero account and wants financial insights,
  this skill is the right tool. Always use it proactively for: "show me unpaid invoices",
  "who owes us money", "what's our P&L this month", "list our top customers", "how much do we
  owe suppliers", "what's in our bank account", "show me the balance sheet".
---

# Xero Financial Analysis Skill

You help users answer financial questions by fetching live data directly from the Xero API using a Python script, then analyzing the results.

## Workflow

**Step 1 — Understand the question**

Work out what the user is actually asking. Some questions are straightforward ("show unpaid invoices"), others require reasoning across multiple angles ("are we profitable this month?"). Note any filters they imply: date ranges, specific customers, statuses, thresholds.

**Step 2 — Identify which entities you need**

Consult `references/xero-entities.md` (read it if you haven't already — it lists all entities and which questions they answer). Most common:
- Invoices/bills/AR/AP → `invoices`
- Customer or supplier analysis → `contacts`  
- P&L, Balance Sheet, Trial Balance → `reports`
- Cash movements, bank feed → `bank_transactions`
- Payments received/made → `payments`

**Step 3 — Check credentials exist**

Before running the script, verify credentials are set up (see Credential Setup below). If they aren't, guide the user through setup rather than failing silently.

**Step 4 — Run `xero_fetch.py`**

```bash
uv run python scripts/xero_fetch.py --entity <entity_name> [--limit N] [--env-file PATH]
```

The script outputs a JSON array to stdout and progress messages to stderr. Capture stdout as your data.

For large datasets you don't need in full, use `--limit` to keep responses fast:
```bash
uv run python scripts/xero_fetch.py --entity invoices --limit 200
```

**Step 5 — Analyze and respond**

Work through the JSON to answer the user's question. Be concrete: show numbers, totals, rankings, trends. If the data has a date range, note what period it covers. Format clearly — tables work well for lists, narrative for summaries.

If the data is larger than you can fully process, prioritize the most relevant subset and say so.

---

## Script Reference

```bash
# Available entities
uv run python scripts/xero_fetch.py --list-entities

# Common fetches
uv run python scripts/xero_fetch.py --entity invoices           # All invoices/bills
uv run python scripts/xero_fetch.py --entity contacts           # All customers & suppliers
uv run python scripts/xero_fetch.py --entity reports            # P&L, Balance Sheet, Trial Balance
uv run python scripts/xero_fetch.py --entity bank_transactions  # Bank feed
uv run python scripts/xero_fetch.py --entity payments           # Payment records
uv run python scripts/xero_fetch.py --entity accounts           # Chart of accounts
uv run python scripts/xero_fetch.py --entity credit_notes       # Credit notes
uv run python scripts/xero_fetch.py --entity items              # Products/services
uv run python scripts/xero_fetch.py --entity assets             # Fixed assets

# Modifiers
uv run python scripts/xero_fetch.py --entity invoices --limit 500        # Cap records
uv run python scripts/xero_fetch.py --entity invoices --pretty           # Pretty JSON
uv run python scripts/xero_fetch.py --entity invoices --env-file ~/.env  # Custom .env path
```

---

## Credential Setup

The script uses **Xero Custom Connections** — no browser login, no OAuth redirect. Just a client ID and secret.

### How to get credentials

1. Go to [developer.xero.com](https://developer.xero.com/) and sign in
2. Click **New App** → choose **Custom Connection**
3. Give it a name, add the scopes you need (see Default Scopes below)
4. Copy the **Client ID** and **Client Secret**
5. In Xero: go to **Settings → Custom Connections** → authorize your app for your organisation

### Setting up the `.env` file

Copy `.env.example` to `.env` in the skill directory and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your credentials
```

`.env` contents:
```
XERO_CLIENT_ID=your-client-id-here
XERO_CLIENT_SECRET=your-client-secret-here
```

The script will find `.env` automatically if it's in the same directory as `xero_fetch.py`.

### Environment variables (alternative)

You can also export credentials directly:
```bash
export XERO_CLIENT_ID=your-client-id
export XERO_CLIENT_SECRET=your-client-secret
```

### Multiple organisations

If you have multiple Xero organisations under one Custom Connection, specify which tenant to use:
```
XERO_TENANT_ID=your-xero-tenant-id
```

Run `uv run python scripts/xero_fetch.py --entity organisations` to see all connected organisations and their IDs.

### Default Scopes

The script requests these scopes (configure in your Xero app):
- `accounting.invoices` — read/write invoices
- `accounting.contacts.read` — contacts
- `accounting.settings.read` — accounts, tax rates
- `accounting.banktransactions.read` — bank transactions
- `accounting.payments.read` — payments
- `accounting.manualjournals` — journals
- `accounting.reports.profitandloss.read` — P&L report
- `accounting.reports.balancesheet.read` — Balance Sheet
- `accounting.reports.trialbalance.read` — Trial Balance

For assets, files, or projects, also add: `assets`, `files.read`, `projects`

---

## Analysis Guidance

### AR Aging (who owes us money)
Fetch `invoices`, filter `type == "ACCREC"` and `status == "AUTHORISED"`, look at `amount_due > 0`. Group by days overdue: `due_date` vs today. Present as an aging table: Current / 1-30 / 31-60 / 60-90 / 90+ days.

### AP Aging (who we owe money to)
Same approach but `type == "ACCPAY"` and `status == "AUTHORISED"`.

### Top customers / suppliers
Fetch `invoices`, group by `contact.name`, sum `total`. Sort descending. Show top N with totals and percentages.

### P&L summary
Fetch `reports`. The `profit_and_loss` reports contain structured `rows` with sections (Revenue, COGS, Expenses). Navigate the row hierarchy to extract totals. Look for `row_type == "SummaryRow"` entries for subtotals.

### Cash flow snapshot
Fetch `bank_transactions`. Sum `type == "RECEIVE"` for cash in, `type == "SPEND"` for cash out. Group by month or week.

### Balance Sheet
Fetch `reports`. The `balance_sheet` report has Assets, Liabilities, and Equity sections.

---

## Installation (for Claude Desktop)

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if not already installed
2. From the skill directory, sync dependencies: `uv sync`
3. Create your `.env` file with credentials: `cp .env.example scripts/.env`
4. Upload the `.skill` file to Claude Desktop via Settings → Skills

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `xero-python package not installed` | Run `uv sync` from the skill root directory |
| `Xero credentials not found` | Add `.env` file or set env vars (see Credential Setup above) |
| `No Xero tenant connections found` | Authorize your Custom Connection app in Xero Settings |
| `Scope denied` | Add missing scopes in your Xero app authorization |
| API timeout | Reduce with `--limit` or increase `XERO_PAGE_TIMEOUT` |

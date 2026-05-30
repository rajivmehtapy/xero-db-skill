# Xero Entities Reference

Use this guide to decide which entity to fetch for a given financial analysis question.

## Quick Decision Guide

| User asks about... | Fetch entity |
|---|---|
| Unpaid bills, invoices owed, AR aging | `invoices` |
| Customer list, supplier details, who owes money | `contacts` |
| Chart of accounts, account codes | `accounts` |
| Bank movements, cash in/out | `bank_transactions` |
| Payments received or made | `payments` |
| Credits issued, refunds | `credit_notes` |
| Products sold, stock items | `items` |
| Journal entries, manual adjustments | `manual_journals` |
| Company name, base currency, org info | `organisations` |
| Profit & Loss, Balance Sheet, Trial Balance | `reports` |
| Fixed assets, depreciation | `assets` |
| Tax rates, VAT/GST | `tax_rates` |
| Departments, regions, tracking | `tracking_categories` |

---

## Entity Details

### `invoices`
Sales invoices (ACCREC) and purchase bills (ACCPAY).

Key fields:
- `invoice_id` — unique ID
- `invoice_number` — e.g. INV-0001
- `type` — `ACCREC` (sales) or `ACCPAY` (purchase)
- `status` — `DRAFT`, `SUBMITTED`, `AUTHORISED`, `PAID`, `VOIDED`
- `contact.name` — customer or supplier name
- `date` — invoice date
- `due_date` — payment due date
- `total` — gross amount (inc. tax)
- `sub_total` — net amount (exc. tax)
- `total_tax` — tax amount
- `amount_due` — outstanding balance
- `amount_paid` — amount paid so far
- `currency_code` — e.g. GBP, USD

**Common analysis:**
- AR aging: filter `type=ACCREC`, `status=AUTHORISED`, sort by `due_date`
- AP aging: filter `type=ACCPAY`, `status=AUTHORISED`
- Top customers: group by `contact.name`, sum `total`
- Overdue invoices: filter where `due_date < today` and `amount_due > 0`

---

### `contacts`
Customers and suppliers in the Xero address book.

Key fields:
- `contact_id` — unique ID
- `name` — full name
- `contact_status` — `ACTIVE` or `ARCHIVED`
- `email_address`
- `is_customer` — boolean
- `is_supplier` — boolean
- `balances.accounts_receivable.outstanding` — total outstanding AR
- `balances.accounts_payable.outstanding` — total outstanding AP

---

### `accounts`
Chart of accounts — the ledger structure.

Key fields:
- `account_id`, `code`, `name`
- `type` — `BANK`, `CURRENT`, `CURRLIAB`, `DEPRECIATN`, `DIRECTCOSTS`, `EQUITY`, `EXPENSE`, `FIXED`, `INVENTORY`, `LIABILITY`, `NONCURRENT`, `OTHERINCOME`, `OVERHEADS`, `PREPAYMENT`, `REVENUE`, `SALES`, `TERMLIAB`, `PAYGLIABILITY`
- `status` — `ACTIVE` or `ARCHIVED`
- `currency_code`
- `tax_type`

---

### `bank_transactions`
Bank and credit card statement lines.

Key fields:
- `bank_transaction_id`
- `type` — `SPEND`, `RECEIVE`, `SPEND-TRANSFER`, `RECEIVE-TRANSFER`
- `status` — `AUTHORISED`, `DELETED`
- `contact.name` — counterparty
- `bank_account.name` — which bank account
- `date` — transaction date
- `total` — amount
- `reference`

---

### `payments`
Payments applied to invoices or credit notes.

Key fields:
- `payment_id`
- `date` — payment date
- `amount` — payment amount
- `payment_type` — `ACCRECPAYMENT`, `ACCPAYPAYMENT`, etc.
- `invoice.invoice_id` — linked invoice
- `account.code` — bank account used
- `status` — `AUTHORISED`, `DELETED`

---

### `credit_notes`
Credit notes issued to customers or received from suppliers.

Key fields:
- `credit_note_id`, `credit_note_number`
- `type` — `ACCRECCREDIT` (issued) or `ACCPAYCREDIT` (received)
- `status` — `DRAFT`, `SUBMITTED`, `AUTHORISED`, `PAID`, `VOIDED`
- `contact.name`
- `date`, `total`, `remaining_credit`

---

### `items`
Products and services (inventory or non-inventory).

Key fields:
- `item_id`, `code`, `name`
- `is_sold`, `is_purchased`
- `quantity_on_hand`
- `purchase_details.unit_price`, `sales_details.unit_price`

---

### `manual_journals`
Manual accounting entries posted directly to the ledger.

Key fields:
- `manual_journal_id`
- `narration` — description of the entry
- `date` — journal date
- `status` — `DRAFT`, `POSTED`, `VOIDED`
- `journal_lines` — array of debit/credit lines with account codes and amounts

---

### `reports`
Aggregated financial statements. Returns multiple reports:
- **profit_and_loss** (current + last 3 months) — Revenue, Cost of Sales, Gross Profit, Expenses, Net Profit
- **balance_sheet** (current) — Assets, Liabilities, Equity
- **trial_balance** (current) — All accounts with debit/credit balances

The `rows` array in each report contains the structured data with `row_type`, `cells`, and nested sections.

---

### `assets`
Fixed asset register (requires Assets module enabled in Xero).

Key fields:
- `asset_id`, `asset_name`, `asset_number`
- `asset_status` — `DRAFT`, `REGISTERED`, `DISPOSED`
- `purchase_date`, `purchase_price`
- `accounting_book_value` — current book value after depreciation
- `serial_number`

---

### `tax_rates`
Tax codes configured in Xero.

Key fields:
- `tax_type` — internal code (e.g. `OUTPUT2`, `INPUT2`)
- `name` — display name (e.g. "Tax on Sales 20%")
- `effective_rate`, `display_tax_rate`
- `status` — `ACTIVE` or `DELETED`

---

### `tracking_categories`
Dimensions for categorising transactions (e.g. Department, Region, Project).

Key fields:
- `tracking_category_id`, `name`, `status`
- `options` — list of available values

---

## Script Usage Examples

```bash
# Fetch all invoices
uv run python scripts/xero_fetch.py --entity invoices

# Fetch contacts (limit to first 100)
uv run python scripts/xero_fetch.py --entity contacts --limit 100

# Fetch reports (P&L, Balance Sheet, Trial Balance)
uv run python scripts/xero_fetch.py --entity reports

# Fetch with explicit env file
uv run python scripts/xero_fetch.py --entity invoices --env-file ~/.xero.env

# Pretty-print JSON
uv run python scripts/xero_fetch.py --entity organisations --pretty

# List all available entities
uv run python scripts/xero_fetch.py --list-entities
```

## Multi-entity analysis

For questions requiring multiple entities (e.g. "show payments with contact details"), fetch both:

```bash
uv run python scripts/xero_fetch.py --entity invoices > invoices.json
uv run python scripts/xero_fetch.py --entity contacts > contacts.json
```

Then analyze both JSON files together.

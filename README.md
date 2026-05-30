# xero-db-skill

A Claude Desktop skill that answers financial analysis questions using live data from the Xero accounting API. Ask Claude about unpaid invoices, AR/AP aging, top customers, profit & loss, balance sheets, and more — Claude fetches the data directly from Xero and analyzes it for you.

---

## Prerequisites

Before installing, you will need:

- **Claude Desktop** — download from [claude.ai/download](https://claude.ai/download)
- **A Xero account** with admin access
- **A Xero Custom Connection app** — [set one up here](https://developer.xero.com/) (takes ~5 minutes, no browser login required at runtime)
- **uv** — Python package manager (installation steps below)

---

## macOS Installation

### Step 1 — Install uv

Open **Terminal** and run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart Terminal, then verify:

```bash
uv --version
```

### Step 2 — Clone the repo

```bash
git clone https://github.com/rajivmehtapy/xero-db-skill.git ~/xero-db-skill
cd ~/xero-db-skill
uv sync
```

### Step 3 — Build the .skill file

The `.skill` file is not included in the repo — build it with one command:

```bash
cd ~
zip -r xero-db-skill.skill xero-db-skill \
  --exclude "xero-db-skill/.venv/*" \
  --exclude "xero-db-skill/.env" \
  --exclude "xero-db-skill/.git/*" \
  --exclude "xero-db-skill/evals/*"
```

This creates `~/xero-db-skill.skill`, ready to upload.

### Step 4 — Set up Xero credentials

#### Get your credentials from Xero

1. Go to [developer.xero.com](https://developer.xero.com/) and sign in
2. Click **New App** → choose **Custom Connection**
3. Name your app (e.g. "Claude Financial Assistant")
4. Under **Scopes**, add:
   - `accounting.invoices`
   - `accounting.contacts.read`
   - `accounting.settings.read`
   - `accounting.banktransactions.read`
   - `accounting.payments.read`
   - `accounting.manualjournals`
   - `accounting.reports.profitandloss.read`
   - `accounting.reports.balancesheet.read`
   - `accounting.reports.trialbalance.read`
5. Click **Save**, then copy your **Client ID** and **Client Secret**
6. In Xero: go to **Settings → Custom Connections** → authorize your app

#### Create the `.env` file

```bash
cd ~/xero-db-skill
cp .env.example scripts/.env
```

Open `scripts/.env` in any text editor and fill in your credentials:

```
XERO_CLIENT_ID=paste-your-client-id-here
XERO_CLIENT_SECRET=paste-your-client-secret-here
```

#### Verify credentials work

```bash
uv run python scripts/xero_fetch.py --entity organisations --pretty
```

You should see your Xero organisation details printed as JSON.

### Step 5 — Upload the skill

1. Go to **[claude.ai](https://claude.ai)** and sign in
2. Click your profile icon → **Settings**
3. Go to **Customize → Skills**
4. Click the **+** button (or **Upload a skill**)
5. Select `xero-db-skill.skill` from your home folder — it uploads as-is
6. The skill activates immediately in both claude.ai and Claude Desktop

### Step 6 — Test it

Open Claude Desktop (or a new claude.ai conversation) and try:

> "Show me all unpaid invoices"

> "Who are our top 5 customers by revenue?"

> "Give me a P&L summary for this month"

Claude will use the skill to fetch live data from Xero and analyze it for you.

---

## Windows Installation

### Step 1 — Install uv

Open **PowerShell** (search "PowerShell" in the Start menu) and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen PowerShell, then verify:

```powershell
uv --version
```

### Step 2 — Clone the repo

Open **PowerShell** and run:

```powershell
git clone https://github.com/rajivmehtapy/xero-db-skill.git $env:USERPROFILE\xero-db-skill
cd $env:USERPROFILE\xero-db-skill
uv sync
```

### Step 3 — Build the .skill file

The `.skill` file is not included in the repo — build it with one command:

```powershell
Compress-Archive -Path $env:USERPROFILE\xero-db-skill `
  -DestinationPath $env:USERPROFILE\xero-db-skill.skill `
  -Force
```

This creates `%USERPROFILE%\xero-db-skill.skill`, ready to upload.

### Step 4 — Set up Xero credentials

#### Get your credentials from Xero

1. Go to [developer.xero.com](https://developer.xero.com/) and sign in
2. Click **New App** → choose **Custom Connection**
3. Name your app (e.g. "Claude Financial Assistant")
4. Under **Scopes**, add:
   - `accounting.invoices`
   - `accounting.contacts.read`
   - `accounting.settings.read`
   - `accounting.banktransactions.read`
   - `accounting.payments.read`
   - `accounting.manualjournals`
   - `accounting.reports.profitandloss.read`
   - `accounting.reports.balancesheet.read`
   - `accounting.reports.trialbalance.read`
5. Click **Save**, then copy your **Client ID** and **Client Secret**
6. In Xero: go to **Settings → Custom Connections** → authorize your app

#### Create the `.env` file

```powershell
cd $env:USERPROFILE\xero-db-skill
Copy-Item .env.example scripts\.env
```

Open `scripts\.env` in Notepad (or any text editor):

```powershell
notepad scripts\.env
```

Fill in your credentials:

```
XERO_CLIENT_ID=paste-your-client-id-here
XERO_CLIENT_SECRET=paste-your-client-secret-here
```

Save and close.

#### Verify credentials work

```powershell
uv run python scripts\xero_fetch.py --entity organisations --pretty
```

You should see your Xero organisation details printed as JSON.

### Step 5 — Upload the skill

1. Go to **[claude.ai](https://claude.ai)** and sign in
2. Click your profile icon → **Settings**
3. Go to **Customize → Skills**
4. Click the **+** button (or **Upload a skill**)
5. Select `xero-db-skill.skill` from your user folder — it uploads as-is
6. The skill activates immediately in both claude.ai and Claude Desktop

### Step 6 — Test it

Open Claude Desktop (or a new claude.ai conversation) and try:

> "Show me all unpaid invoices"

> "Who are our top 5 customers by revenue?"

> "Give me a P&L summary for this month"

---

## What you can ask

| Question | What Claude fetches |
|---|---|
| Unpaid invoices, who owes us | `invoices` (AR) |
| Bills we owe, AP aging | `invoices` (AP) |
| Top customers or suppliers | `invoices` + grouping |
| Profit & Loss this month | `reports` |
| Balance sheet | `reports` |
| Bank transactions, cash flow | `bank_transactions` |
| Payments received/made | `payments` |
| Products and stock | `items` |
| Fixed assets | `assets` |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `uv: command not found` | Restart your terminal after installing uv |
| `Xero credentials not found` | Check that `scripts/.env` exists and has `XERO_CLIENT_ID` and `XERO_CLIENT_SECRET` |
| `No Xero tenant connections found` | Go to Xero → Settings → Custom Connections → authorize your app |
| `Scope denied` | Add the missing scope to your Xero Custom Connection app and re-authorize |
| Skill not appearing after upload | Re-upload via claude.ai → Settings → Customize → Skills; ensure you selected the `.skill` file |
| API timeout on large datasets | The script supports `--limit N` to cap record count |

---

## Multiple Xero organisations

If your Custom Connection is authorized for more than one organisation, specify which one to use by adding to `scripts/.env`:

```
XERO_TENANT_ID=your-tenant-id-here
```

To find your tenant ID, run:

```bash
# macOS
uv run python scripts/xero_fetch.py --entity organisations --pretty

# Windows
uv run python scripts\xero_fetch.py --entity organisations --pretty
```

# xero-db-skill

A Claude Desktop skill + MCP server that answers financial analysis questions using live data from the Xero accounting API. Ask Claude about unpaid invoices, AR/AP aging, top customers, profit & loss, balance sheets, and more — Claude fetches the data directly from Xero and analyzes it for you.

> **Note:** Claude Desktop runs skills inside a sandboxed VM with no outbound internet access. This repo includes an **MCP server** that runs on your local machine (with full network access) and exposes Xero data to Claude Desktop. Both the skill file and MCP server are required.

---

## Prerequisites

- **Claude Desktop** — download from [claude.ai/download](https://claude.ai/download)
- **A Xero account** with admin access
- **A Xero Custom Connection app** — [set one up here](https://developer.xero.com/) (takes ~5 minutes)
- **uv** — Python package manager (installation steps below)

---

## macOS Installation

### Step 1 — Install uv

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

### Step 3 — Set up Xero credentials

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
   - `assets`
   - `files.read`
   - `projects`
5. Click **Save**, then copy your **Client ID** and **Client Secret**
6. In Xero: go to **Settings → Custom Connections** → authorize your app

#### Create the `.env` file

```bash
cp scripts/.env.example scripts/.env
```

Open `scripts/.env` and fill in your credentials:

```
XERO_CLIENT_ID=paste-your-client-id-here
XERO_CLIENT_SECRET=paste-your-client-secret-here
```

#### Verify credentials work

```bash
uv run python scripts/xero_fetch.py --entity organisations --pretty
```

You should see your Xero organisation details as JSON.

### Step 4 — Register the MCP server with Claude Desktop

Open `~/Library/Application Support/Claude/claude_desktop_config.json` in any text editor and add the `xero-db-skill` entry inside `mcpServers`:

```json
{
  "mcpServers": {
    "xero-db-skill": {
      "command": "/bin/bash",
      "args": ["/Users/YOUR_USERNAME/xero-db-skill/run-mcp.sh"]
    }
  }
}
```

Replace `YOUR_USERNAME` with your macOS username. If the file doesn't exist yet, create it with exactly the content above.

Make the launcher executable:

```bash
chmod +x ~/xero-db-skill/run-mcp.sh
```

### Step 5 — Upload the skill file

Build the `.skill` file:

```bash
cd ~
zip -r xero-db-skill.skill xero-db-skill \
  --exclude "xero-db-skill/.venv/*" \
  --exclude "xero-db-skill/.env" \
  --exclude "xero-db-skill/.git/*" \
  --exclude "xero-db-skill/evals/*"
```

Upload it to Claude Desktop:

1. Go to **Claude Desktop** → **Settings** → **Customize** → **Skills**
2. Click **Upload a skill** and select `~/xero-db-skill.skill`

### Step 6 — Restart Claude Desktop and test

Quit Claude Desktop completely (Cmd+Q) and reopen it. Then try:

> "Show me all unpaid invoices"

> "Who are our top 5 customers by revenue?"

> "Give me a P&L summary for this month"

---

## Windows Installation

### Step 1 — Install uv

Open **PowerShell** and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen PowerShell, then verify:

```powershell
uv --version
```

### Step 2 — Clone the repo

```powershell
git clone https://github.com/rajivmehtapy/xero-db-skill.git $env:USERPROFILE\xero-db-skill
cd $env:USERPROFILE\xero-db-skill
uv sync
```

### Step 3 — Set up Xero credentials

```powershell
Copy-Item scripts\.env.example scripts\.env
notepad scripts\.env
```

Fill in your credentials:

```
XERO_CLIENT_ID=paste-your-client-id-here
XERO_CLIENT_SECRET=paste-your-client-secret-here
```

Verify credentials work:

```powershell
uv run python scripts\xero_fetch.py --entity organisations --pretty
```

### Step 4 — Register the MCP server with Claude Desktop

Open `%APPDATA%\Claude\claude_desktop_config.json` in Notepad and add the `xero-db-skill` entry:

```json
{
  "mcpServers": {
    "xero-db-skill": {
      "command": "cmd.exe",
      "args": ["/c", "C:\\Users\\YOUR_USERNAME\\xero-db-skill\\run-mcp.bat"]
    }
  }
}
```

Replace `YOUR_USERNAME` with your Windows username.

### Step 5 — Upload the skill file

```powershell
Compress-Archive -Path $env:USERPROFILE\xero-db-skill `
  -DestinationPath $env:USERPROFILE\xero-db-skill.skill `
  -Force
```

Upload it in Claude Desktop → **Settings** → **Customize** → **Skills** → **Upload a skill**.

### Step 6 — Restart Claude Desktop and test

Quit Claude Desktop and reopen it, then ask:

> "Show me all unpaid invoices"

---

## Why both a skill file AND an MCP server?

Claude Desktop runs skills inside a sandboxed virtual machine that has **no outbound internet access**. The skill file (`.skill`) provides Claude with the instructions and Python script, but the script cannot reach external APIs from inside the VM.

The **MCP server** (`mcp_server.py`) runs directly on your machine — outside the sandbox — where it can freely connect to Xero's API. Claude Desktop communicates with it over a local socket. This is the same pattern used by all MCP integrations in Claude Desktop.

```
Claude Desktop VM (sandboxed)        Your Machine
┌──────────────────────────────┐     ┌────────────────────────┐
│  Skill (SKILL.md + script)   │────▶│  MCP Server            │
│  reads instructions only     │ MCP │  runs xero_fetch.py    │
│  calls MCP tools             │◀────│  connects to Xero API  │
└──────────────────────────────┘     └────────────────────────┘
```

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
| MCP server not connecting | Check Claude Desktop config JSON for syntax errors; restart Claude Desktop |
| Skill not appearing after upload | Re-upload via Settings → Customize → Skills |
| API timeout on large datasets | The script supports `--limit N` to cap record count |

---

## Multiple Xero organisations

If your Custom Connection is authorized for more than one organisation, add to `scripts/.env`:

```
XERO_TENANT_ID=your-tenant-id-here
```

To find your tenant ID:

```bash
# macOS
uv run python scripts/xero_fetch.py --entity organisations --pretty

# Windows
uv run python scripts\xero_fetch.py --entity organisations --pretty
```

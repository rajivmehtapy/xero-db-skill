#!/usr/bin/env python3
"""MCP server exposing Xero financial data to Claude Desktop."""
import os
import sys
import json
import subprocess

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("xero-db-skill")

SCRIPT = os.path.join(os.path.dirname(__file__), "scripts", "xero_fetch.py")
ENV_FILE = os.path.join(os.path.dirname(__file__), "scripts", ".env")


def _run(entity: str, limit: int = 0) -> list[dict]:
    cmd = ["uv", "run", "python", SCRIPT, "--entity", entity, "--env-file", ENV_FILE]
    if limit > 0:
        cmd += ["--limit", str(limit)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout)


@mcp.tool()
def xero_get_invoices(limit: int = 500) -> list[dict]:
    """Fetch all invoices (AR and AP) from Xero. Filter for unpaid ones using status=AUTHORISED and amount_due>0."""
    return _run("invoices", limit)


@mcp.tool()
def xero_get_contacts(limit: int = 500) -> list[dict]:
    """Fetch all customers and suppliers from Xero."""
    return _run("contacts", limit)


@mcp.tool()
def xero_get_reports() -> list[dict]:
    """Fetch P&L, Balance Sheet, and Trial Balance reports from Xero."""
    return _run("reports")


@mcp.tool()
def xero_get_bank_transactions(limit: int = 500) -> list[dict]:
    """Fetch bank and credit card transactions from Xero."""
    return _run("bank_transactions", limit)


@mcp.tool()
def xero_get_payments(limit: int = 500) -> list[dict]:
    """Fetch payment records (received and made) from Xero."""
    return _run("payments", limit)


@mcp.tool()
def xero_get_accounts() -> list[dict]:
    """Fetch chart of accounts from Xero."""
    return _run("accounts")


@mcp.tool()
def xero_get_credit_notes(limit: int = 200) -> list[dict]:
    """Fetch credit notes from Xero."""
    return _run("credit_notes", limit)


@mcp.tool()
def xero_get_items() -> list[dict]:
    """Fetch products and services catalog from Xero."""
    return _run("items")


@mcp.tool()
def xero_get_organisations() -> list[dict]:
    """Fetch Xero organisation details."""
    return _run("organisations")


@mcp.tool()
def xero_get_assets() -> list[dict]:
    """Fetch fixed assets register from Xero."""
    return _run("assets")


if __name__ == "__main__":
    mcp.run()

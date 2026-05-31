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


def _contact_name(c) -> str:
    if not c:
        return ""
    if isinstance(c, dict):
        return c.get("name") or ""
    return str(c)


def _slim_invoices(records: list[dict]) -> list[dict]:
    out = []
    for r in records:
        out.append({
            "invoice_id": r.get("invoice_id"),
            "invoice_number": r.get("invoice_number"),
            "type": r.get("type"),
            "status": r.get("status"),
            "date": str(r.get("date") or ""),
            "due_date": str(r.get("due_date") or ""),
            "amount_due": r.get("amount_due"),
            "amount_paid": r.get("amount_paid"),
            "sub_total": r.get("sub_total"),
            "total": r.get("total"),
            "currency_code": r.get("currency_code"),
            "contact": _contact_name(r.get("contact")),
            "reference": r.get("reference"),
        })
    return out


def _slim_contacts(records: list[dict]) -> list[dict]:
    out = []
    for r in records:
        out.append({
            "contact_id": r.get("contact_id"),
            "name": r.get("name"),
            "email_address": r.get("email_address"),
            "is_customer": r.get("is_customer"),
            "is_supplier": r.get("is_supplier"),
            "account_number": r.get("account_number"),
            "balances": r.get("balances"),
        })
    return out


def _slim_bank_transactions(records: list[dict]) -> list[dict]:
    out = []
    for r in records:
        bank = r.get("bank_account") or {}
        out.append({
            "bank_transaction_id": r.get("bank_transaction_id"),
            "type": r.get("type"),
            "status": r.get("status"),
            "date": str(r.get("date") or ""),
            "total": r.get("total"),
            "currency_code": r.get("currency_code"),
            "contact": _contact_name(r.get("contact")),
            "bank_account": bank.get("name") if isinstance(bank, dict) else str(bank),
            "reference": r.get("reference"),
        })
    return out


def _slim_payments(records: list[dict]) -> list[dict]:
    out = []
    for r in records:
        inv = r.get("invoice") or {}
        out.append({
            "payment_id": r.get("payment_id"),
            "date": str(r.get("date") or ""),
            "amount": r.get("amount"),
            "payment_type": r.get("payment_type"),
            "status": r.get("status"),
            "currency_code": r.get("currency_rate"),
            "invoice_number": inv.get("invoice_number") if isinstance(inv, dict) else None,
            "contact": _contact_name(r.get("contact")),
            "reference": r.get("reference"),
        })
    return out


def _slim_credit_notes(records: list[dict]) -> list[dict]:
    out = []
    for r in records:
        out.append({
            "credit_note_id": r.get("credit_note_id"),
            "credit_note_number": r.get("credit_note_number"),
            "type": r.get("type"),
            "status": r.get("status"),
            "date": str(r.get("date") or ""),
            "total": r.get("total"),
            "remaining_credit": r.get("remaining_credit"),
            "currency_code": r.get("currency_code"),
            "contact": _contact_name(r.get("contact")),
        })
    return out


@mcp.tool()
def xero_get_invoices(limit: int = 500) -> list[dict]:
    """Fetch invoices (AR and AP) from Xero, slimmed to key fields. Default 500 records. Filter for unpaid ones using status=AUTHORISED and amount_due>0."""
    return _slim_invoices(_run("invoices", limit))


@mcp.tool()
def xero_get_contacts(limit: int = 500) -> list[dict]:
    """Fetch customers and suppliers from Xero, slimmed to key fields. Default 500 records."""
    return _slim_contacts(_run("contacts", limit))


@mcp.tool()
def xero_get_reports() -> list[dict]:
    """Fetch P&L, Balance Sheet, and Trial Balance reports from Xero."""
    return _run("reports")


@mcp.tool()
def xero_get_bank_transactions(limit: int = 500) -> list[dict]:
    """Fetch bank and credit card transactions from Xero, slimmed to key fields. Default 500 records."""
    return _slim_bank_transactions(_run("bank_transactions", limit))


@mcp.tool()
def xero_get_payments(limit: int = 500) -> list[dict]:
    """Fetch payment records (received and made) from Xero, slimmed to key fields. Default 500 records."""
    return _slim_payments(_run("payments", limit))


@mcp.tool()
def xero_get_accounts() -> list[dict]:
    """Fetch chart of accounts from Xero."""
    return _run("accounts")


@mcp.tool()
def xero_get_credit_notes(limit: int = 500) -> list[dict]:
    """Fetch credit notes from Xero, slimmed to key fields. Default 500 records."""
    return _slim_credit_notes(_run("credit_notes", limit))


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

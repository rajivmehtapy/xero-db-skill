#!/usr/bin/env python3
"""
xero_fetch.py — Fetch data from Xero API and output as JSON.

Usage:
    python xero_fetch.py --entity invoices
    python xero_fetch.py --entity contacts --limit 50
    python xero_fetch.py --entity reports
    python xero_fetch.py --entity invoices --env-file /path/to/.env
    python xero_fetch.py --list-entities

Credentials (in priority order):
    1. --env-file argument
    2. .env in the same directory as this script
    3. .env in the current working directory
    4. XERO_CLIENT_ID / XERO_CLIENT_SECRET environment variables
"""

import argparse
import json
import os
import sys
import calendar
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime
from pathlib import Path

try:
    from xero_python.accounting import AccountingApi
    from xero_python.api_client import ApiClient, Configuration
    from xero_python.api_client.oauth2 import OAuth2Token
    from xero_python.assets import AssetApi
    from xero_python.assets.models import AssetStatusQueryParam
    from xero_python.file import FilesApi
    from xero_python.identity import IdentityApi
    from xero_python.project import ProjectApi
except ImportError:
    print(
        "ERROR: xero-python package not installed.\n"
        "Run: pip install xero-python python-dotenv",
        file=sys.stderr,
    )
    sys.exit(1)

DEFAULT_PAGE_SIZE = 100
DEFAULT_PAGE_TIMEOUT = int(os.environ.get("XERO_PAGE_TIMEOUT", "60"))

SUPPORTED_ENTITIES = {
    "invoices": "Sales and purchase invoices (AR/AP)",
    "contacts": "Customers and suppliers",
    "accounts": "Chart of accounts",
    "bank_transactions": "Bank and credit card transactions",
    "payments": "Invoice payments received/made",
    "credit_notes": "Credit notes issued or received",
    "items": "Products and services catalog",
    "manual_journals": "Manual journal entries",
    "organisations": "Xero organisation details",
    "tax_rates": "Tax rates and types",
    "tracking_categories": "Tracking categories (departments, regions, etc.)",
    "users": "Xero users",
    "reports": "Financial reports (P&L, Balance Sheet, Trial Balance)",
    "assets": "Fixed assets register",
}


def load_dotenv_file(path):
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)
    return True


def load_credentials(env_file=None):
    if env_file:
        if not load_dotenv_file(env_file):
            print(f"WARNING: --env-file '{env_file}' not found", file=sys.stderr)
    else:
        script_dir = Path(__file__).parent
        load_dotenv_file(script_dir / ".env") or load_dotenv_file(Path.cwd() / ".env")

    client_id = (
        os.environ.get("XERO_CLIENT_ID")
        or os.environ.get("XERO_CLIENT_API_ID")
    )
    client_secret = (
        os.environ.get("XERO_CLIENT_SECRET")
        or os.environ.get("XERO_CLIENT_API_SECRET")
    )

    if not client_id or not client_secret:
        print(
            "ERROR: Xero credentials not found.\n\n"
            "Set these in a .env file next to this script:\n"
            "  XERO_CLIENT_ID=your-custom-connection-client-id\n"
            "  XERO_CLIENT_SECRET=your-custom-connection-client-secret\n\n"
            "Or pass --env-file /path/to/.env\n\n"
            "Get your credentials from: https://developer.xero.com/\n"
            "(Create a Custom Connection app — no browser login needed)",
            file=sys.stderr,
        )
        sys.exit(1)

    return client_id, client_secret


def fix_token_scope(token):
    if token and "scope" in token and isinstance(token["scope"], str):
        token["scope"] = token["scope"].split(" ")
    return token


def object_to_dict(record):
    if record is None:
        return {}
    if isinstance(record, dict):
        return dict(record)
    if hasattr(record, "to_dict"):
        return record.to_dict()
    return {"value": str(record)}


class XeroClient:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token_store = {"token": None}
        self._tenant_id = None

        self.api_client = ApiClient(
            configuration=Configuration(
                oauth2_token=OAuth2Token(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )
            )
        )
        self.api_client.oauth2_token_getter(lambda: self._token_store["token"])
        self.api_client.oauth2_token_saver(
            lambda t: self._token_store.update({"token": fix_token_scope(t)})
        )

    def authenticate(self):
        print("Authenticating with Xero...", file=sys.stderr)
        token = fix_token_scope(self.api_client.get_client_credentials_token())
        self._token_store["token"] = token
        return token

    def get_tenant_id(self):
        if self._tenant_id:
            return self._tenant_id
        tenant_id_env = os.environ.get("XERO_TENANT_ID")
        if tenant_id_env:
            self._tenant_id = tenant_id_env.strip()
            return self._tenant_id
        connections = list(IdentityApi(self.api_client).get_connections() or [])
        if not connections:
            print("ERROR: No Xero tenant connections found.", file=sys.stderr)
            sys.exit(1)
        self._tenant_id = connections[0].tenant_id
        return self._tenant_id

    def _paginate(self, fetch_page, attr_name, label, page_size=DEFAULT_PAGE_SIZE, limit=None):
        items = []
        page = 1
        while True:
            print(f"  Fetching {label} page {page}...", file=sys.stderr)
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(fetch_page, page, page_size)
                    response = future.result(timeout=DEFAULT_PAGE_TIMEOUT)
            except FuturesTimeoutError:
                print(f"WARNING: Timeout fetching {label} page {page}", file=sys.stderr)
                break

            batch = list(getattr(response, attr_name) or [])
            if not batch:
                break

            items.extend(batch)

            if limit and len(items) >= limit:
                items = items[:limit]
                break

            if len(batch) < page_size:
                break

            page += 1

        return items

    def fetch(self, entity, limit=None):
        tid = self.get_tenant_id()
        accounting = AccountingApi(self.api_client)
        print(f"Fetching {entity} (tenant: {tid})...", file=sys.stderr)

        if entity == "invoices":
            items = self._paginate(
                lambda p, ps: accounting.get_invoices(tid, page=p, page_size=ps),
                "invoices", "invoices", limit=limit,
            )
            return [object_to_dict(i) for i in items]

        elif entity == "contacts":
            items = self._paginate(
                lambda p, ps: accounting.get_contacts(tid, page=p, page_size=ps),
                "contacts", "contacts", limit=limit,
            )
            return [object_to_dict(i) for i in items]

        elif entity == "accounts":
            response = accounting.get_accounts(tid)
            items = list(response.accounts or [])
            if limit:
                items = items[:limit]
            return [object_to_dict(i) for i in items]

        elif entity == "bank_transactions":
            items = self._paginate(
                lambda p, ps: accounting.get_bank_transactions(tid, page=p, page_size=ps),
                "bank_transactions", "bank_transactions", limit=limit,
            )
            return [object_to_dict(i) for i in items]

        elif entity == "payments":
            items = self._paginate(
                lambda p, ps: accounting.get_payments(tid, page=p, page_size=ps),
                "payments", "payments", limit=limit,
            )
            return [object_to_dict(i) for i in items]

        elif entity == "credit_notes":
            items = self._paginate(
                lambda p, ps: accounting.get_credit_notes(tid, page=p, page_size=ps),
                "credit_notes", "credit_notes", limit=limit,
            )
            return [object_to_dict(i) for i in items]

        elif entity == "items":
            response = accounting.get_items(tid)
            items = list(response.items or [])
            if limit:
                items = items[:limit]
            return [object_to_dict(i) for i in items]

        elif entity == "manual_journals":
            items = self._paginate(
                lambda p, ps: accounting.get_manual_journals(tid, page=p, page_size=ps),
                "manual_journals", "manual_journals", limit=limit,
            )
            return [object_to_dict(i) for i in items]

        elif entity == "organisations":
            response = accounting.get_organisations(tid)
            items = list(response.organisations or [])
            return [object_to_dict(i) for i in items]

        elif entity == "tax_rates":
            response = accounting.get_tax_rates(tid)
            items = list(response.tax_rates or [])
            return [object_to_dict(i) for i in items]

        elif entity == "tracking_categories":
            response = accounting.get_tracking_categories(tid)
            items = list(response.tracking_categories or [])
            return [object_to_dict(i) for i in items]

        elif entity == "users":
            response = accounting.get_users(tid)
            items = list(response.users or [])
            return [object_to_dict(i) for i in items]

        elif entity == "reports":
            return self._fetch_reports(tid, accounting)

        elif entity == "assets":
            return self._fetch_assets(tid)

        else:
            print(f"ERROR: Unknown entity '{entity}'. Run --list-entities to see options.", file=sys.stderr)
            sys.exit(1)

    def _fetch_reports(self, tid, accounting):
        reports = []
        now = datetime.now()

        for report_fn, name in [
            (lambda: accounting.get_report_profit_and_loss(tid), "profit_and_loss"),
            (lambda: accounting.get_report_balance_sheet(tid), "balance_sheet"),
            (lambda: accounting.get_report_trial_balance(tid), "trial_balance"),
        ]:
            try:
                print(f"  Fetching {name} report...", file=sys.stderr)
                response = report_fn()
                raw_reports = list(response.reports or [])
                if raw_reports:
                    reports.append({
                        "report_type": name,
                        "period": "current",
                        **object_to_dict(raw_reports[0]),
                    })
            except Exception as e:
                print(f"  WARNING: Failed to fetch {name}: {e}", file=sys.stderr)

        # Monthly P&L for last 3 months
        yr, mn = now.year, now.month
        for _ in range(3):
            mn -= 1
            if mn == 0:
                mn = 12
                yr -= 1
            _, last_day = calendar.monthrange(yr, mn)
            from_d = f"{yr}-{mn:02d}-01"
            to_d = f"{yr}-{mn:02d}-{last_day}"
            period_label = f"{yr}{mn:02d}"
            try:
                print(f"  Fetching P&L for {period_label}...", file=sys.stderr)
                response = accounting.get_report_profit_and_loss(tid, from_date=from_d, to_date=to_d)
                raw_reports = list(response.reports or [])
                if raw_reports:
                    reports.append({
                        "report_type": "profit_and_loss",
                        "period": period_label,
                        **object_to_dict(raw_reports[0]),
                    })
            except Exception as e:
                print(f"  WARNING: Failed to fetch P&L {period_label}: {e}", file=sys.stderr)

        return reports

    def _fetch_assets(self, tid):
        try:
            asset_api = AssetApi(self.api_client)
            assets = {}
            for status in AssetStatusQueryParam:
                batch = self._paginate(
                    lambda p, ps, s=status: asset_api.get_assets(tid, s, page=p, page_size=ps),
                    "items", f"assets:{status.value}",
                )
                for asset in batch:
                    asset_dict = object_to_dict(asset)
                    asset_id = asset_dict.get("asset_id") or str(asset)
                    assets[asset_id] = asset_dict
            return list(assets.values())
        except Exception as e:
            print(f"ERROR: Failed to fetch assets: {e}", file=sys.stderr)
            return []


def main():
    parser = argparse.ArgumentParser(
        description="Fetch data from Xero API and output as JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--entity", "-e",
        help="Xero entity to fetch (e.g. invoices, contacts, reports)",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Maximum number of records to fetch (default: all)",
    )
    parser.add_argument(
        "--env-file",
        help="Path to .env file with credentials",
    )
    parser.add_argument(
        "--list-entities",
        action="store_true",
        help="List available entities and exit",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )

    args = parser.parse_args()

    if args.list_entities:
        print("Available entities:")
        for name, desc in SUPPORTED_ENTITIES.items():
            print(f"  {name:<22} {desc}")
        sys.exit(0)

    if not args.entity:
        parser.print_help()
        sys.exit(1)

    client_id, client_secret = load_credentials(args.env_file)
    client = XeroClient(client_id, client_secret)
    client.authenticate()

    data = client.fetch(args.entity, limit=args.limit)

    indent = 2 if args.pretty else None
    print(json.dumps(data, default=str, indent=indent))


if __name__ == "__main__":
    main()

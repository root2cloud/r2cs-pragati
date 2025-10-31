# -*- coding: utf-8 -*-
from odoo import models
from datetime import datetime, date
import json

class GeneralLedgerDateFormat(models.TransientModel):
    _inherit = "account.general.ledger"

    # --- helper --------------------------------------------------------------
    def _to_ddmmyyyy(self, v):
        """Return DD-MM-YYYY for date/datetime/ISO string; otherwise return v unchanged."""
        if not v:
            return v
        try:
            if isinstance(v, date) and not isinstance(v, datetime):
                d = v
            elif isinstance(v, datetime):
                d = v.date()
            elif isinstance(v, str):
                # accept 'YYYY-MM-DD' (and ignore any time part)
                if len(v) >= 10 and v[4] == "-" and v[7] == "-":
                    d = datetime.strptime(v[:10], "%Y-%m-%d").date()
                else:
                    return v
            else:
                return v
            return d.strftime("%d-%m-%Y")
        except Exception:
            return v

    # --- UI payload: format the Date column shown in the General Ledger ------
    def get_accounts_line(self, account_id, title):
        res = super().get_accounts_line(account_id, title)

        # Walk every returned block and rewrite ldate to DD-MM-YYYY
        for block in res.get("report_lines", []):
            move_lines = block.get("move_lines")
            if isinstance(move_lines, list):
                for line in move_lines:
                    if "ldate" in line:
                        line["ldate"] = self._to_ddmmyyyy(line.get("ldate"))
        return res

    # --- XLSX export: make Date column DD-MM-YYYY as well --------------------
    def get_dynamic_xlsx_report(self, data, response, report_data, dfr_data):
        try:
            # report_data is a JSON string containing accounts with their move_lines
            if isinstance(report_data, bytes):
                report_data = report_data.decode()
            parsed = json.loads(report_data or "[]")

            for acc in parsed:
                move_lines = acc.get("move_lines")
                if isinstance(move_lines, list):
                    for line in move_lines:
                        if "ldate" in line:
                            line["ldate"] = self._to_ddmmyyyy(line.get("ldate"))

            report_data = json.dumps(parsed, default=str)
        except Exception:
            # If anything goes wrong, keep the original behavior.
            return super().get_dynamic_xlsx_report(data, response, report_data, dfr_data)

        return super().get_dynamic_xlsx_report(data, response, report_data, dfr_data)

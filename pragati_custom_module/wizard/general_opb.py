from odoo import models
import json

class GeneralLedgerOpbFirst(models.TransientModel):
    _inherit = "account.general.ledger"

    # helper: keep OPB lines first, preserve original order for the rest
    def _opb_first(self, lines):
        try:
            return sorted(
                lines,
                key=lambda l: 0 if str(l.get("lcode", "")).upper() == "OPB" else 1
            )
        except Exception:
            return lines

    # UI expand: when frontend asks for account lines, ensure OPB is first under JRNL
    def get_accounts_line(self, account_id, title):
        res = super().get_accounts_line(account_id, title)
        for block in res.get("report_lines", []):
            moves = block.get("move_lines")
            if isinstance(moves, list) and moves:
                block["move_lines"] = self._opb_first(moves)
        return res

    # XLSX export: sort the serialized move_lines so JRNL shows OPB first in the sheet
    def get_dynamic_xlsx_report(self, data, response, report_data, dfr_data):
        try:
            parsed = json.loads(report_data) or []
            for acc in parsed:
                ml = acc.get("move_lines")
                if isinstance(ml, list) and ml:
                    acc["move_lines"] = self._opb_first(ml)
            report_data = json.dumps(parsed)
        except Exception:
            # if anything odd in the payload, fall back to parent untouched
            pass
        return super().get_dynamic_xlsx_report(data, response, report_data, dfr_data)

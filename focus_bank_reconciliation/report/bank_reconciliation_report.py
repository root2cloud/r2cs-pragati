from odoo import models, api


class BankReconciliationReport(models.AbstractModel):
    _name = 'report.focus_bank_reconciliation.report_bank_reconciliation_doc'
    _description = 'Bank Reconciliation Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Fetches the records.
        No complex calculation needed here anymore as we print exactly what is on the screen.
        """
        docs = self.env['bank.reconciliation.console'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'bank.reconciliation.console',
            'docs': docs,
        }
from odoo import models, api


class BankReconciliationReport(models.AbstractModel):
    _name = 'report.focus_bank_reconciliation.report_bank_reconciliation_doc'
    _description = 'Bank Reconciliation Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Standard Odoo Report Method.
        Fetches records and pre-computes the 'Uncleared' data for each record.
        """
        # 1. Fetch the records selected for printing
        docs = self.env['bank.reconciliation.console'].browse(docids)

        # 2. Pre-compute report data for each document
        # We store it in a dictionary keyed by the record ID
        report_data = {}
        for doc in docs:
            report_data[doc.id] = self._get_uncleared_data(doc)

        # 3. Return the values to the QWeb Template
        return {
            'doc_ids': docids,
            'doc_model': 'bank.reconciliation.console',
            'docs': docs,
            'report_data': report_data,  # Pass our computed dictionary
        }

    def _get_uncleared_data(self, doc):
        """
        Helper Logic to calculate Unpresented Checks vs Uncleared Deposits.
        """
        target_account = doc.bank_journal_id.default_account_id

        # Search for Uncleared Lines
        uncleared_lines = self.env['account.move.line'].search([
            ('account_id', '=', target_account.id),
            ('date', '<=', doc.date_to),
            ('parent_state', '=', 'posted'),
            ('is_brs_cleared', '!=', True)
        ])

        # Split Logic
        unpresented_checks = uncleared_lines.filtered(lambda r: r.credit > 0)
        uncleared_deposits = uncleared_lines.filtered(lambda r: r.debit > 0)

        return {
            'unpresented_checks': unpresented_checks,
            'uncleared_deposits': uncleared_deposits,
            'total_unpresented': sum(unpresented_checks.mapped('credit')),
            'total_uncleared': sum(uncleared_deposits.mapped('debit')),
        }

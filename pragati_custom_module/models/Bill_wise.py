from odoo import api, models, _
from odoo.exceptions import UserError

class LedgerPaymentBillWiseAdjustments(models.Model):
    _inherit = 'ledger.payment.bill.wise.adjustments'

    @api.model_create_multi
    def create(self, values_list):
        records = super().create(values_list)

        for record in records:

            if record.jv_list:
                record.journal_entry_id = False
                continue

            # ✅ Otherwise, proceed with journal entry creation
            journal_entry = self.env['account.move'].create({
                'date': record.date,
                'ref': record.name,
                'journal_id': record.journal_id.id,
                'ledger_payment_bwa_id': record.id,
                'state': 'draft',
            })

            lines = []
            if record.boole == 'receive':
                lines = [
                    (0, 0, {
                        'account_id': record.source_acc.id,
                        'debit': record.amount,
                        'credit': 0.0,
                        'date': record.date,
                    }),
                    (0, 0, {
                        'account_id': record.dest_acc.id,
                        'debit': 0.0,
                        'credit': record.amount,
                        'date': record.date,
                    }),
                ]
            elif record.boole == 'send':
                lines = [
                    (0, 0, {
                        'account_id': record.source_acc.id,
                        'debit': 0.0,
                        'credit': record.amount,
                        'date': record.date,
                    }),
                    (0, 0, {
                        'account_id': record.dest_acc.id,
                        'debit': record.amount,
                        'credit': 0.0,
                        'date': record.date,
                    }),
                ]
            journal_entry.write({'line_ids': lines})
            record.journal_entry_id = journal_entry.id

        return records

    def action_confirm(self):
        self.ensure_one()


        if self.jv_list:
            self.is_complete_trans = True
            self.state = 'post'
            return True

        if not self.journal_entry_id:
            raise UserError(_("No linked journal entry found for this transaction."))

        self.journal_entry_id.action_post()
        self.is_complete_trans = True
        self.state = 'post'
        return True

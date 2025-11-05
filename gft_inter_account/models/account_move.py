from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

class AccountMove(models.Model):
    _inherit = 'account.move'


    internal_trans_id = fields.Many2one('internal.transaction', string="Internal Transfer ID:")
    ledger_payment_id = fields.Many2one('ledger.payment', string="Ledger Pay ID:")
    ledger_payment_bwa_id =fields.Many2one('ledger.payment.bill.wise.adjustments', string="Ledger Pay BWA ID:")
    bank_manual_id = fields.Many2one('bank.account.manual', string="Bank Manual ID:")
    is_manual_reconcile = fields.Boolean(string='Reconciled', default=False)
    amount_total_signed = fields.Float(string='Total Signed Amount')
    manual_reconcile_amount = fields.Float(
        string="Reconcile Amount",
        compute='_compute_manual_reconcile_amount',
        store=True
    )
    ledger_pay_id = fields.Many2one('ledger.payment', string="Bank Manual ID:")
    ledger_pay_bwa_id = fields.Many2one('ledger.payment.bill.wise.adjustments', string="Bank Manual ID:")


    @api.depends('amount_total_signed')
    def _compute_manual_reconcile_amount(self):
        for record in self:
            # Set the value of manual_reconcile_amount equal to amount_total_signed
            record.manual_reconcile_amount = record.amount_total_signed






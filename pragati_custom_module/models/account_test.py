from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    balance_amount = fields.Float(
        string="Balance Amount", compute='_compute_balance_amount', store=True
    )

    @api.depends('invoice_origin', 'name', 'ref')
    def _compute_balance_amount(self):
        for move in self:
            move.balance_amount = 0.0
            references_to_try = []

            if move.invoice_origin:
                references_to_try.append(move.invoice_origin.strip())
            if move.name:
                references_to_try.append(move.name.strip())
            if move.ref:
                references_to_try.append(move.ref.strip())

            for ref in references_to_try:
                advice_lines = self.env['payment.advice.line'].search([
                    ('reference', '=', ref)
                ])
                if advice_lines:
                    reference_amount = max(
                        (line.reference_amount for line in advice_lines if line.reference_amount),
                        default=0.0
                    )
                    paid = sum(line.rec_amount or 0.0 for line in advice_lines)
                    move.balance_amount = reference_amount - paid
                    break

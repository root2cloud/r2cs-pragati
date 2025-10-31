# your_custom_module/models/pos_order.py
from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    invoice_number = fields.Char(
        string='Invoice Number',
        related='account_move.name',
        store=True,
        readonly=True
    )

    @api.depends('account_move')
    def _compute_invoice_number(self):
        for order in self:
            order.invoice_number = order.account_move.name if order.account_move else ''

from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    payment_methods_display = fields.Text(string="Payment Methods", compute="_compute_payment_methods")

    @api.depends('payment_ids.payment_method_id', 'payment_ids.amount')
    def _compute_payment_methods(self):
        for order in self:
            lines = [
                f"{payment.payment_method_id.name}: {payment.amount:.2f}"
                for payment in order.payment_ids
            ]
            order.payment_methods_display = '\n'.join(lines)












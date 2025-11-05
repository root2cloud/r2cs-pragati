from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    payment_method_id = fields.Many2one(
        'pos.payment.method',
        string="Payment Method",
        compute='_compute_payment_method',
        store=True
    )

    @api.depends('payment_ids.payment_method_id')
    def _compute_payment_method(self):
        for order in self:
            if order.payment_ids:
                order.payment_method_id = order.payment_ids[0].payment_method_id
            else:
                order.payment_method_id = False

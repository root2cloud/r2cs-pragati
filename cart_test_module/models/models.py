from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # total_amount = fields.Float(compute='_compute_total_amount', string='Total Amount')

    # @api.depends('product_uom_qty', 'price_unit')
    # def _compute_total_amount(self):
    #     for line in self:
    #         line.total_amount = line.product_uom_qty * line.price_unit
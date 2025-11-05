from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    location_id = fields.Many2one('stock.location', string='Location', compute='_compute_location_id', store=False)

    def _compute_location_id(self):
        for product in self:
            quant = self.env['stock.quant'].search([('product_id', '=', product.id)], limit=1)
            product.location_id = quant.location_id

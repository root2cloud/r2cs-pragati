from odoo import models, fields, api
from odoo.exceptions import UserError

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    on_hand_qty = fields.Float(string="On Hand Qty", compute="_compute_on_hand_qty", store=False)

    @api.onchange('product_id', 'location_id')
    def _onchange_product_id_location(self):
        for line in self:
            if line.product_id and line.location_id:
                qty = self.env['stock.quant'].sudo().search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.location_id.id)
                ], limit=1).quantity

                line.on_hand_qty = qty or 0.0

                if qty <= 0:
                    return {
                        'warning': {
                            'title': "No Stock",
                            'message': f"There is no available quantity for {line.product_id.display_name} at {line.location_id.display_name}.",
                        }
                    }
            else:
                line.on_hand_qty = 0.0

    @api.depends('product_id', 'location_id')
    def _compute_on_hand_qty(self):
        for line in self:
            if line.product_id and line.location_id:
                qty = self.env['stock.quant'].sudo().search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.location_id.id)
                ], limit=1).quantity
                line.on_hand_qty = qty or 0.0
            else:
                line.on_hand_qty = 0.0

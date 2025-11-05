from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    on_hand_qty = fields.Float(
        string="On Hand Quantity",
        compute="_compute_on_hand_qty",
        store=False
    )

    destination_location_qty = fields.Float(
        string="On Hand Destination Quantity",
        compute="_compute_destination_location_qty",
        store=False
    )

    @api.depends('product_id', 'location_id')
    def _compute_on_hand_qty(self):
        """Fetch On-Hand Quantity from stock.quant based on the selected From Location (location_id)."""
        for line in self:
            if line.product_id and line.location_id:
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.location_id.id)  # Fetching stock from From Location
                ], limit=1)

                line.on_hand_qty = quant.quantity if quant else 0.0
            else:
                line.on_hand_qty = 0.0

    @api.depends('product_id', 'location_dest_id')
    def _compute_destination_location_qty(self):
        """Fetch Destination Location Quantity from stock.quant."""
        for line in self:
            if line.product_id and line.location_dest_id:
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.location_dest_id.id)
                ], limit=1)

                line.destination_location_qty = quant.quantity if quant else 0.0
            else:
                line.destination_location_qty = 0.0


























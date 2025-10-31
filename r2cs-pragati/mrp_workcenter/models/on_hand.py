from odoo import models, fields

class MrpProduction(models.Model):
    _inherit = 'stock.move'

    on_hand_qty = fields.Float(string="Hand quantity")

    workorder_id = fields.Many2one(
        'mrp.workorder', string='Workorder'
    )


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    workorder_id = fields.Many2one(
        'mrp.workorder', string='Workorder'
    )

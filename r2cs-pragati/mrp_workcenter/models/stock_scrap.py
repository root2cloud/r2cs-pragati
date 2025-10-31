from odoo import models, fields

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    workorder_id = fields.Many2one(
        'mrp.workorder',
        string='Work Order',
        ondelete='set null'
    )

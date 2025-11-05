from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    partner_id = fields.Many2one(
        'res.partner', 'Contact',
        check_company=True, domain="[('state', '=', 'approve')]",
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

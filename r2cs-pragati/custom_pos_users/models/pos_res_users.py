from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    shop_of_pos_id = fields.Many2one('pos.config', string='Assigned POS Shop',
        help='The POS shop this partner is assigned to.'
    )

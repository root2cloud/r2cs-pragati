from odoo import models, fields

class PosOrder(models.Model):
    _inherit = 'pos.order'

    page_note = fields.Text(string="Notes")

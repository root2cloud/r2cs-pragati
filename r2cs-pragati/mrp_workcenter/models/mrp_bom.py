from odoo import models, fields

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    activity_ids = fields.Text(string="Activity IDs")

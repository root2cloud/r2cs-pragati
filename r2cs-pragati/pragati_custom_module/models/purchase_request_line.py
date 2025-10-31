from odoo import models, fields

class PurchaseRequestLineInherit(models.Model):
    _inherit = 'purchase.request.line'

    is_selected_in_po = fields.Boolean(string='Selected in Purchase Order', default=False)

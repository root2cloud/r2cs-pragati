from odoo import models, fields

class PurchaseReportInherit(models.Model):
    _inherit = 'purchase.report'

    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)

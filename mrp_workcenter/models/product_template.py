from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_ref = fields.Char(string="Product Reference")
    unit_cost = fields.Float(string="Unit Cost")
    unit_name_value = fields.Char(string="Unit Name Value")


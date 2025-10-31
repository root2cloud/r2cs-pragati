from odoo import fields,models,api

class ProductTemplate(models.Model):
	_inherit = 'product.template'


	calories_count = fields.Float(string="Calories")


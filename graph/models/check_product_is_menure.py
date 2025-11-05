from odoo import fields,models,api

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    check_product_is_menure_pest = fields.Selection([('none','None'),('menure', 'Menure'), ('pest', 'Pest')],default='none')
    

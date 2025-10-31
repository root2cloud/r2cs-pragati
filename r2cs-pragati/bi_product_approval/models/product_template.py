from odoo import api, fields, models,_
from odoo.osv import expression
import json

from lxml import etree



class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approve')], string='Status', readonly=True, index=True, copy=False, tracking=True, default='draft')

    def button_draft(self):
        self.state = 'draft'
        
    def button_approve(self):
        self.state = 'approve'

    @api.model
    def get_view(self, view_id=None, view_type=False, **options):
        result = super(ProductTemplate, self).get_view(view_id=view_id, view_type=view_type, **options)
        doc = etree.XML(result['arch'])
        if view_type == 'form':
            for node in doc.xpath("//field"):
                modifiers = node.get("modifiers")
                if modifiers:
                    modifiers = json.loads(modifiers)
                else:
                    modifiers = {}
                if 'readonly' not in modifiers:
                    modifiers['readonly'] = "[('state','=','approve')]"
                else:
                    modifiers['readonly'] = "[('state','=','approve')]"
                node.set('modifiers', json.dumps(modifiers))
        result['arch'] = etree.tostring(doc, encoding='unicode')
        return result


class Product(models.Model):
    _inherit = "product.product"
    
    state = fields.Selection(related="product_tmpl_id.state")

    def button_draft(self):
        self.state ='draft'
        
    def button_approve(self):
        self.state = 'approve'

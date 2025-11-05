from odoo import models, fields, api, _

class DeliveryTerms(models.Model):
    _name = "delivery.terms"
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _rec_name = 'delivery_terms'
    _description = "Delivery Terms to the Purchase Order"


    
    delivery_terms = fields.Char(string= 'Delivery Terms')
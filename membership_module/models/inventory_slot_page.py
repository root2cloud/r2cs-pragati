from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'


    plan_id = fields.Many2one("membership.planning", string="Plan Name")
    plan_name = fields.Char(related="plan_id.plan_name", string="Plan Name", store=True)

    @api.onchange('plan_id')
    def onchange_plan_id(self):
        if self.plan_id:
            self.lst_price = self.plan_id.net_price

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    plan_id = fields.Many2one("membership.planning", string="Plan Name")
    plan_name = fields.Char(related="plan_id.plan_name", string="Plan Name", store=True)
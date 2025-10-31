from odoo import models, fields, api


class MembershipPlanning(models.Model):
    _name = 'membership.planning'
    _rec_name = 'plan_name'


    plan_name = fields.Char(string="Membership Plan Name")
    membership_id = fields.Many2one('member.ship', string='Membership')
    plan_duration = fields.Integer(string="Plan Duration")

    price = fields.Float(string="Price")
    discount_percentage = fields.Float(string="Discount (%)")
    discount_amount = fields.Float(string="Discount Amount", compute='_compute_discount_amount', store=True)
    net_price = fields.Float(string="Net Price", compute='_compute_net_price', store=True)

    @api.depends('price', 'discount_percentage')
    def _compute_discount_amount(self):
        for rec in self:
            rec.discount_amount = (rec.price * rec.discount_percentage) / 100

    @api.depends('price', 'discount_percentage')
    def _compute_net_price(self):
        for rec in self:
            rec.net_price = rec.price - rec.discount_amount 
   
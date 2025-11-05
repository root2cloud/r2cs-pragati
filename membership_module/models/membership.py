from odoo import models, fields, api


class MemberShip(models.Model):
    _name = 'member.ship'
    _rec_name = 'membership_name'

    membership_name = fields.Char(string="Membership Name")
    
    
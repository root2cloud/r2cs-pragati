from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'hr.department'

    approver1 = fields.Many2one('res.users', string="Approver 1")
    approver2 = fields.Many2one('res.users', string="Approver 2")
    approver3 = fields.Many2one('res.users', string="Approver 3")




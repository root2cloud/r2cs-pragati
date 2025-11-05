from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    partner_mobile = fields.Char(
        string="Phone Number",
        related='partner_id.phone',
        store=True,
        readonly=True
    )

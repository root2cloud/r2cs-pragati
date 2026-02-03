from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_narration = fields.Char(string='Narration')
    cheque_number = fields.Char(string='Cheque Number')

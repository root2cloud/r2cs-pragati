# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # This field is crucial later for the Reconciliation Console.
    # It tracks if this specific receipt has been "ticked" by the user.
    custom_reconciled = fields.Boolean(
        string='Reconciled',
        default=False,
        copy=False
    )
    payment_narration = fields.Char(string='Narration')
    cheque_number = fields.Char(string='Cheque Number')


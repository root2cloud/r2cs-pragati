# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import frozendict


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    # @api.depends('can_edit_wizard', 'source_amount', 'source_amount_currency', 'source_currency_id', 'company_id',
    #              'currency_id', 'payment_date')
    # def _compute_amount(self):
    #     for wizard in self:
    #         res = super(AccountPaymentRegister,self)._compute_amount()
    #         if wizard.source_currency_id and wizard.can_edit_wizard:
    #             if self.line_ids:
    #                 move_ids = self.line_ids.mapped('move_id')
    #                 for move in move_ids:
    #                     if move.global_discount_type == 'fixed':
    #                         wizard.amount -= move.global_order_discount
    #                     elif move.global_discount_type == 'percent':
    #                         wizard.amount -= move.total_discount
    #                     else:
    #                         wizard.amount = 0
    #         else:
    #             # The wizard is not editable so no partial payment allowed and then, 'amount' is not used.
    #             wizard.amount = None
    #         return res

    def _get_total_amount_in_wizard_currency_to_full_reconcile(self, batch_result, early_payment_discount=True):
        res = super()._get_total_amount_in_wizard_currency_to_full_reconcile(batch_result,early_payment_discount)
        if self.line_ids:
            move_ids = self.line_ids.mapped('move_id')
            for move in move_ids:
                if move.global_discount_type == 'fixed':
                    amount = res[0]-move.global_order_discount
                    return (amount,False)
                elif move.global_discount_type == 'percent':
                    amount = res[0] - move.total_discount
                    return (amount, False)
                else:
                    return res
        return res
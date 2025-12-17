from odoo import models, api
from odoo.exceptions import ValidationError
from decimal import Decimal


class InternalTransactionInherit(models.Model):
    _inherit = "internal.transaction"

    # @api.constrains("amount", "source_acc")
    # def _check_source_account_balance(self):
    #
    #     for record in self:
    #         if record.source_acc and record.amount:
    #             AccountMoveLine = self.env['account.move.line']
    #             domain = [
    #                 ('account_id', '=', record.source_acc.id),
    #                 ('parent_state', '=', 'posted'),
    #             ]
    #             # Get balance using the Odoo sign convention (debit-credit)
    #             lines = AccountMoveLine.read_group(domain, ['debit', 'credit'], [])
    #             debit = Decimal(lines[0]['debit']) if lines and lines[0]['debit'] else Decimal(0)
    #             credit = Decimal(lines[0]['credit']) if lines and lines[0]['credit'] else Decimal(0)
    #             balance = debit - credit
    #             amount = Decimal(str(record.amount))
    #
    #             if balance < amount:
    #                 raise ValidationError(
    #                     f"Insufficient balance in source account '{record.source_acc.name}'.\n\n"
    #                     f"Current Balance: {balance:,.2f}\n"
    #                     f"Requested Transfer: {amount:,.2f}")

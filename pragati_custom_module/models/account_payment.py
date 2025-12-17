from odoo import models, fields, api,_
from num2words import num2words
from decimal import Decimal
from odoo.exceptions import ValidationError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # advice_id = fields.Many2one('payment.advice', string='Advice ID')
    amount_in_words = fields.Char(string='Amount in Words', compute='_compute_amount_in_words', store=True)

    # def action_post(self):
    #     res = super(AccountPayment, self).action_post()
    #     print(self.advice_id,"###########$$$$$$$$$$$$$$$$$$$$@@@@@@@@@@")
    #     for rec in self:
    #         if rec.advice_id:
    #             rec.advice_id.state = 'payment'

    #     return res

    def convert_to_indian_currency_words(self, amount):
        words = num2words(amount, lang='en_IN')
        words = words.capitalize()
        words += " Rupees only"
        return words

    @api.depends('amount')
    def _compute_amount_in_words(self):
        for order in self:
            if order.amount:
                order.amount_in_words = order.convert_to_indian_currency_words(order.amount).title()
            else:
                order.amount_in_words = ""

    @api.constrains("amount", "journal_id")
    def _check_journal_balance(self):
        for rec in self:
            if rec.journal_id and rec.amount:

                # Get the account used by the journal
                account = rec.journal_id.default_account_id
                if not account:
                    continue

                # Compute balance from move lines (posted only)
                AccountMoveLine = self.env['account.move.line']
                domain = [
                    ('account_id', '=', account.id),
                    ('parent_state', '=', 'posted'),
                ]

                grouped = AccountMoveLine.read_group(
                    domain,
                    ['debit', 'credit'],
                    []
                )

                debit = Decimal(grouped[0]['debit']) if grouped and grouped[0]['debit'] else Decimal(0)
                credit = Decimal(grouped[0]['credit']) if grouped and grouped[0]['credit'] else Decimal(0)

                # Actual account balance
                balance = debit - credit  # Odoo sign convention

                requested = Decimal(str(rec.amount))

                # Check if user entered more than available balance
                if requested > balance:
                    raise ValidationError(_(
                        f"Insufficient balance in the selected Journal '{rec.journal_id.name}'.\n\n"
                        f"Account: {account.name}\n"
                        f"Available Balance: {balance:,.2f}\n"
                        f"Requested Amount: {requested:,.2f}"
                    ))

from odoo import models, fields, api
from num2words import num2words

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

    def convert_to_indian_currency_words(self,amount):
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
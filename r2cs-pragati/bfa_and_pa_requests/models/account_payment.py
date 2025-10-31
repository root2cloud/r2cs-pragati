from odoo import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    advice_id = fields.Many2one('payment.advice', string='Advice Id')


    def action_post(self):
        res = super(AccountPayment,self).action_post()
        if self.advice_id:
            self.advice_id.write({'state':'payment'})
        return res

    def action_draft(self):
        res = super(AccountPayment,self).action_draft()
        if self.advice_id:
            self.advice_id.write({'state':'approve'})
        return res

    def action_cancel(self):
        res = super(AccountPayment,self).action_cancel()
        if self.advice_id:
            self.advice_id.write({'state':'approve'})
        return res


    def unlink(self):
        if self.advice_id:
            self.advice_id.write({'state':'approve'})
        return super(AccountPayment,self).unlink()



    



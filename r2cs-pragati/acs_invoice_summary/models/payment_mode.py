from odoo import models, fields, api



class AccountPayment(models.Model):
    _inherit = 'account.payment'


    payment_mode_id = fields.Many2one('payment.mode.sample', string='Payment Mode')
    bank_account_number = fields.Integer(string='Account Number')
    ifsc_code_register = fields.Char(string='IFSC Code')


class PaymentModeSample(models.Model):
    _name = 'payment.mode.sample'


    name = fields.Char(string='Payment Mode')




class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'


    payment_mode_id = fields.Many2one('payment.mode.sample', string='Payment Mode')
    bank_account_number = fields.Integer(string='Account Number')
    ifsc_code_register = fields.Char(string='IFSC Code')
    is_netbanking = fields.Boolean(string='Is Netbanking', default=False)



    @api.onchange('payment_mode_id')
    def _onchange_payment_mode_id(self):
        for record in self:
            if record.payment_mode_id and record.payment_mode_id.name in ['Net Banking', 'netbanking', 'Netbanking']:
                record.is_netbanking = True

            else:
                record.is_netbanking = False


    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)

        # Update payment_vals dictionary here
        # For example, adding a new key-value pair
        payment_vals['payment_mode_id'] = self.payment_mode_id.id
        payment_vals['bank_account_number'] = self.bank_account_number
        payment_vals['ifsc_code_register'] = self.ifsc_code_register


        return payment_vals


    def _create_payments(self):
        # Call the parent class method to create payments
        payments = super(AccountPaymentRegister, self)._create_payments()

        # Get the account move record
        account_move = self.line_ids.move_id

        # Retrieve existing payment IDs
        existing_payment_ids = account_move.payment_process_id.ids if account_move.payment_process_id else []

        # Combine existing and new payment IDs
        all_payment_ids = existing_payment_ids + payments.ids

        # Assign the combined payment IDs to the payment_process_id field
        account_move.payment_process_id = [(6, 0, all_payment_ids)]

        return payments

class AccountMove(models.Model):
    _inherit = 'account.move'

    # is_approved = fields.Boolean(string='Approved', default=False)
    payment_process_id = fields.Many2many('account.payment')
    discount_remarks = fields.Char(string="Discount Remarks")
    # def request_approval(self):
    #     self.ensure_one()
    #     self.activity_schedule(
    #         'mail.mail_activity_data_todo',
    #         date_deadline=fields.Datetime.now(),
    #         summary="Invoice Approval Required",
    #         user_id=self.env.ref('base.user_admin').id,
    #         note="Please approve the invoice.",
    #         res_id=self.id,
    #         res_model='account.move',
    #     )
    # def approve_invoice(self):
    #     self.ensure_one()
    #     self.is_approved = True


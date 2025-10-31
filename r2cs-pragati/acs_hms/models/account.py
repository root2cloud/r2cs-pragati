# -*- coding: utf-8 -*-

from odoo import api,fields,models,_
from odoo.exceptions import ValidationError
from datetime import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'

    ref_physician_id = fields.Many2one('res.partner', ondelete='restrict', string='Referring Physician', 
        index=True, help='Referring Physician', readonly=True, states={'draft': [('readonly', False)]})
    appointment_id = fields.Many2one('hms.appointment',  string='Appointment', readonly=True, states={'draft': [('readonly', False)]})
    procedure_id = fields.Many2one('acs.patient.procedure',  string='Patient Procedure', readonly=True, states={'draft': [('readonly', False)]})
    hospital_invoice_type = fields.Selection(selection_add=[('appointment', 'Appointment'), ('treatment','Treatment'), ('procedure','Procedure')])


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    deadline_date = fields.Datetime(string='Deadline Date')

    # @api.model
    # def create(self, vals):
    #     # Override the create method to set payment amount based on deadline
    #     payment = super(AccountPayment, self).create(vals)
    #     payment.update_payment_amount_cron()
    #     return payment
    #
    # def write(self, vals):
    #     # Override the write method to update payment amount on deadline change
    #     res = super(AccountPayment, self).write(vals)
    #     self.update_payment_amount_cron()
    #     return res
    #
    # @api.model
    # def update_payment_amount_cron(self):
    #     payments = self.search([('deadline_date', '<', fields.Datetime.now()), ('amount', '!=', 0.0)])
    #     for payment in payments:
    #         payment.write({'amount': 0.0})



            # Add any additional logic here if needed

    # You can also add a cron job to periodically check and update payment amounts

    # Other fields and methods as needed

# class AccountPayment(models.Model):
#     _inherit = 'account.payment'

#     deadline_date = fields.Datetime(string='Deadline Date')
#     locked = fields.Boolean(string='Locked', default=False)

#     @api.model
#     def create(self, vals):
#         # Override the create method to set payment amount based on deadline
#         payment = super(AccountPayment, self).create(vals)
#         payment.update_payment_amount_cron()
#         return payment

#     def write(self, vals):
#         # Override the write method to update payment amount on deadline change
#         res = super(AccountPayment, self).write(vals)
#         self.update_payment_amount_cron()
#         return res

#     @api.model
#     def update_payment_amount_cron(self):
#         payments = self.search([('deadline_date', '<', fields.Datetime.now()), ('amount', '!=', 0.0), ('locked', '=', False)])
#         for payment in payments:
#             amount_used = self.calculate_amount_used(payment)
#             if amount_used < payment.amount:
#                 payment.write({'amount': payment.amount - amount_used})
#             else:
#                 payment.write({'amount': 0.0, 'locked': True})

#     def calculate_amount_used(self, payment):
#         # Add your logic here to calculate the amount used based on invoices or outstanding credits
#         # For example, if you have a field named 'outstanding_credits' on the customer, you can use:
#         return payment.partner_id.outstanding_credits

#     @api.model
#     def admin_unlock_payment(self, payment_ids):
#         payments = self.browse(payment_ids)
#         for payment in payments:
#             payment.write({'locked': False})


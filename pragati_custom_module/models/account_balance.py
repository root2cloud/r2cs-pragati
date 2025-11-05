from odoo import models, fields, api

class ServiceCompletion(models.Model):
    _inherit = 'service.completion'

    service_order_id = fields.Many2one('service.order', string="Service Order")
    balance_amount = fields.Float(string="Balance Amount", compute="_compute_balance_amount", store=True)

    @api.depends('service_order_id')
    def _compute_balance_amount(self):
        for rec in self:
            rec.balance_amount = 0.0
            if rec.service_order_id:
                service_order_name = rec.service_order_id.name

                # Get payment advice lines related to this SO
                paid_lines = self.env['payment.advice.line'].search([
                    ('reference', '=', service_order_name)
                ])

                # Take the latest reference_amount from advice lines (in case of multiple entries)
                reference_amount = 0.0
                if paid_lines:
                    reference_amount = max(line.reference_amount for line in paid_lines)

                paid = sum(line.rec_amount for line in paid_lines)

                rec.balance_amount = reference_amount - paid

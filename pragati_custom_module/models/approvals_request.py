# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError



class ApprovalRequest(models.Model):
    _inherit = 'approval.request'




    category_name = fields.Char(related="category_id.name")
    # balance_amount = fields.Float(string='Balance', compute='_compute_balance')
    date = fields.Datetime(string="Date",default=datetime.today())
    pr_confirmation = fields.Boolean(string='PR Confirm', default=False)
    material_indent_id = fields.Many2one('material.indent', string='Material Indent Id', readonly=True)
    purchase_request_id = fields.Many2one('purchase.request', string='Purchase Request Id', readonly=True)
    service_order_sep_id = fields.Many2one('service.order',string='Service Order ID', readonly=True)
    service_completion_id = fields.Many2one('service.completion',string='Service Order ID', readonly=True)
    bills_sep_id = fields.Many2one('bills.approval', string='Bills Approval', readonly=True)
    payment_advice_sep_id = fields.Many2one('payment.advice', string='Payment Advice', readonly=True)
    account_move_sep_id = fields.Many2one('account.move', string='Account Move ID', readonly=True)
    purchase_no_id = fields.Many2one('purchase.order', string='Purchase Number', readonly=True)
    stock_picking_id = fields.Many2one('stock.picking', string='Stock ID', readonly=True)
    ledger_payment_id = fields.Many2one('ledger.payment',string='Bank Receipt', readonly=True)


    # @api.depends('service_order_id.account_move_id')
    # def _compute_paid_amount_details(self):
    #     for record in self:
    #         if record.service_order_id and record.service_order_id.account_move_id:
    #             account_move = record.service_order_id.account_move_id
    #             paid_amount = record.paid_amount
    #             total_amount = account_move.amount_total
    #             amount_residual = account_move.amount_residual

    #             record.paid_amount_details = f'Paid amount is {paid_amount:.2f} and due amount is {amount_residual:.2f} out of a total of {total_amount:.2f}'
    #         else:
    #             record.paid_amount_details = f'Paid amount is 0.00 and due amount is {record.total_amount:.2f}'


    def open_any_order(self):
        for record in self:
            target_model = None
            record_id = None

            if record.service_order_sep_id:
                target_model = 'service.order'  # Replace with your actual model name
                record_id = record.service_order_sep_id.id
            elif record.service_completion_id:
                target_model = 'service.completion'  # Replace with your actual model name
                record_id = record.service_completion_id.id
            elif record.material_indent_id:
                target_model = 'material.indent'  # Replace with your actual model name
                record_id = record.material_indent_id.id
            elif record.purchase_request_id:
                target_model = 'purchase.request'  # Replace with your actual model name
                record_id = record.purchase_request_id.id
            elif record.bills_sep_id:
                target_model = 'bills.approval'  # Replace with your actual model name
                record_id = record.bills_sep_id.id
            elif record.payment_advice_sep_id:
                target_model = 'payment.advice'  # Replace with your actual model name
                record_id = record.payment_advice_sep_id.id
            elif record.account_move_sep_id:
                target_model = 'account.move'  # Replace with your actual model name
                record_id = record.account_move_sep_id.id
            elif record.purchase_no_id:
                target_model = 'purchase.order'  # Replace with your actual model name
                record_id = record.purchase_no_id.id
            elif record.stock_picking_id:
                target_model = 'stock.picking'  # Replace with your actual model name
                record_id = record.stock_picking_id.id
            elif record.ledger_payment_id:
                target_model = 'ledger.payment'  # Replace with your actual model name
                record_id = record.ledger_payment_id.id

            if target_model and record_id:
                return {
                    'name': _('Any Order'),
                    'type': 'ir.actions.act_window',
                    'res_model': target_model,
                    'view_mode': 'form',
                    'res_id': record_id,
                    'target': 'current',
                }


    def action_approve(self, approver=None):
        if self.ledger_payment_id:
            self.ledger_payment_id.state='approve'
        return super(ApprovalRequest,self).action_approve(approver)


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'



class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    status = fields.Selection([
            ('new', 'New'),
            ('pending', 'Pending'),
            ('waiting', 'Waiting'),
            ('approved', 'Approved'),
            ('refused', 'Refused'),
            ('cancel', 'Cancel')], string="Status", default="new", readonly=True)

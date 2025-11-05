from odoo import models, fields, api
from datetime import date

class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    READONLY_STATES = {
        'complete': [('readonly', True)],
    }
    po_status = fields.Selection([
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('done', 'Done'),
        ('canceled', 'Canceled')
    ], string='PO Status', compute='_compute_po_status', store=True)

    purchase_order_ids = fields.One2many('purchase.order', 'requisition_id', string="Purchase Orders")

    # po_status = fields.Char(string="PO Status", compute="_compute_po_status")
    mrn_status = fields.Char(string="MRN Status", compute="_compute_mrn_status")



    po_numbers = fields.Char(string="PO Numbers", compute="_compute_po_details")
    po_dates = fields.Date(string="PO Dates", compute="_compute_po_details")
    po_states = fields.Char(string="PO Statuses", compute="_compute_po_details")
    department_id = fields.Many2one('hr.department', 'Department', tracking=True, states=READONLY_STATES)

    mrn_numbers = fields.Char(string="MRN Numbers", compute="_compute_mrn_details")
    mrn_dates = fields.Date(string="MRN Dates", compute="_compute_mrn_details")
    mrn_states = fields.Char(string="MRN Statuses", compute="_compute_mrn_details")

    delay_days = fields.Integer(string="Delay Days")









    @api.depends('purchase_order_ids.state')
    def _compute_po_status(self):
        for requisition in self:
            po_ids = self.env['purchase.order'].search([('pr_request_ids', 'in', requisition.id)])
            if not po_ids:
                requisition.po_status = 'pending'
            else:
                states = po_ids.mapped('state')
                if all(state in ['purchase', 'done'] for state in states):
                    requisition.po_status = 'done'
                elif any(state == 'cancel' for state in states):
                    requisition.po_status = 'canceled'
                else:
                    requisition.po_status = 'partial'

    @api.depends('purchase_order_ids.picking_ids.state')
    def _compute_mrn_status(self):
        for requisition in self:
            picking_ids = self.env['purchase.order'].search([('pr_request_ids', '=', requisition.id)]).mapped(
                'picking_ids')
            if not picking_ids:
                requisition.mrn_status = 'Pending'
            else:
                states = picking_ids.mapped('state')
                if all(state in ['done', 'customer_signed'] for state in states):
                    requisition.mrn_status = 'Done'
                elif any(state == 'cancel' for state in states):
                    requisition.mrn_status = 'Canceled'
                else:
                    requisition.mrn_status = 'Partial'

    @api.depends('purchase_order_ids')
    def _compute_po_details(self):
        for requisition in self:
            po_ids = self.env['purchase.order'].search([('pr_request_ids', 'in', [requisition.id])])
            requisition.po_numbers = ', '.join(po_ids.mapped('name')) if po_ids else ''
            requisition.po_dates = ', '.join(
                po_ids.mapped(lambda po: po.date_order.strftime('%Y-%m-%d'))) if po_ids else ''
            requisition.po_states = ', '.join(po_ids.mapped('state')) if po_ids else ''

    @api.depends('purchase_order_ids.picking_ids')
    def _compute_mrn_details(self):
        for requisition in self:
            picking_ids = self.env['purchase.order'].search([('pr_request_ids', '=', requisition.id)]).mapped(
                'picking_ids')
            requisition.mrn_numbers = ', '.join(picking_ids.mapped('name')) if picking_ids else ''
            requisition.mrn_dates = ', '.join(
                picking_ids.mapped(lambda p: p.scheduled_date.strftime('%Y-%m-%d'))) if picking_ids else ''
            # requisition.mrn_states = ', '.join(picking_ids.mapped('state')) if picking_ids else ''
            requisition.mrn_states = ', '.join(
                ['Ready' if state == 'assigned' else state for state in picking_ids.mapped('state')]
            ) if picking_ids else ''

from odoo import models, fields, api


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    workorder_count = fields.Integer("Workorder Count", compute='_compute_workorder_counts', store=True)
    workorder_ready_count = fields.Integer("Workorder Ready Count", compute='_compute_workorder_counts', store=True)
    workorder_progress_count = fields.Integer("Workorder Progress Count", compute='_compute_workorder_counts', store=True)
    workorder_late_count = fields.Integer("Workorder Late Count", compute='_compute_workorder_counts', store=True)
    oee = fields.Float("OEE", compute="_compute_oee", store=True)
    oee_target = fields.Float(string='OEE Target')
    working_state = fields.Selection([
        ('normal', 'Running'),
        ('blocked', 'Blocked'),
        ('done', 'Done')
    ], string="Workcenter Status", default="normal")

    order_ids = fields.One2many('mrp.workorder', 'workcenter_id', string="Work Orders")

    @api.depends('order_ids.state', 'order_ids.date_planned_start')
    def _compute_workorder_counts(self):
        for wc in self:
            workorders = wc.order_ids
            wc.workorder_count = len(workorders)
            wc.workorder_ready_count = len(workorders.filtered(lambda x: x.state == 'ready'))
            wc.workorder_progress_count = len(workorders.filtered(lambda x: x.state == 'progress'))
            wc.workorder_late_count = len(workorders.filtered(lambda x: x.state == 'ready' and x.date_planned_start and x.date_planned_start < fields.Datetime.now()))

    @api.depends('performance', 'workcenter_load')  # Adjust according to your data
    def _compute_oee(self):
        for wc in self:
            wc.oee = wc.performance or 0.0
from odoo import models, fields

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    employee_costs_hour = fields.Float(string="Employee Cost per Hour")
    allow_employee = fields.Boolean(string="Allow Employee")
    cost_employee_id = fields.Many2one('hr.employee', string="Cost Responsible Employee")
    company_id = fields.Many2one('res.company', 'Company')
    employee_ids = fields.Many2many(
        'hr.employee',
        required=True,
        check_company=True,
        domain="[('work_email', '!=', False)]"
    )

    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    routing_line_ids = fields.One2many('mrp.routing.workcenter', 'workcenter_id', string="Routing Lines")
    order_ids = fields.One2many('mrp.workorder', 'workcenter_id', string="Orders")
    time_ids = fields.One2many('mrp.workcenter.productivity', 'workcenter_id', string='Time Logs')
    oee_target = fields.Float(string='OEE Target')
    performance = fields.Integer(string='Performance')
    workcenter_load = fields.Float(string='Work Center Load')
    alternative_workcenter_ids = fields.Many2many('mrp.workcenter')
    tag_ids = fields.Many2many('mrp.workcenter.tag')
    capacity_ids = fields.One2many(
        'mrp.workcenter.capacity',
        'workcenter_id',
        string='Product Capacities'
    )

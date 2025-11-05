from odoo import models, fields

class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee'
    )
    workorder_id = fields.Many2one(
        'mrp.workorder',
        string='Work Order',
        ondelete='cascade'
    )
    workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Work Center',
        ondelete='cascade'
    )

from odoo import models, fields

class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    employee_ratio = fields.Float(string="Employee Ratio")
    quality_point_count = fields.Integer(string='Quality Point Count', default=0)
    workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Work Center',
        ondelete='cascade'
    )

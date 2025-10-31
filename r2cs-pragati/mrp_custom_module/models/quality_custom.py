# from odoo import fields, models


# class QualityCheck(models.Model):
#     _inherit = 'quality.check'
#
#     workorder_ids = fields.Many2many(
#         'mrp.workorder',
#         'mrp_workorder_finished_product_check_rel',
#         'check_id',
#         'workorder_id',
#         string='Related Work Orders'
#     )

# class QualityPoint(models.Model):
#     _inherit = 'quality.point'
#
#     workorder_ids = fields.Many2many(
#         'mrp.workorder',
#         'mrp_workorder_quality_point_rel',
#         'point_id',
#         'workorder_id',
#         string="Work Orders"
#     )
# class QualityCheck(models.Model):
#     _inherit = 'quality.alert'
#
#     workorder_ids = fields.Many2many(
#         'mrp.workorder',
#         'mrp_workorder_finished_product_check_rel',
#         'check_id',
#         'workorder_id',
#         string='Related Work Orders'
#     )




from odoo import models, fields

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    workorder_id = fields.Many2one(
        'mrp.workorder',
        string='Work Order',
        ondelete='cascade'
    )
# #
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

class ResUsers(models.Model):
    _inherit = 'res.users'

    workorder_ids = fields.Many2many(
        'mrp.workorder',
        'mrp_workorder_last_users_rel',
        'user_id',
        'workorder_id',
        string="Work Orders"
    )
#
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





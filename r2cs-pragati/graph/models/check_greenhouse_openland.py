from odoo import fields,models,api


class StockLocation(models.Model):
	_inherit = 'stock.location'


	check_greenhouse_openland = fields.Selection([('greenhouse', 'Green House'), ('openland', 'Open Land')])




# class CropPlanning(models.Model):
#     _inherit = 'crop.planning'

#     @api.model
#     def confirm_planning(self):
#         for rec in self:
#             l1 = []
#             for bed in rec.beds_ids:
#                 if not bed.location_confirm:
#                     bed.write({'location_confirm': True, 'planning_id': rec.id})
#                 else:
#                     l1.append(bed.name)
#             bed_names = ",".join(l1)
#             if bed_names:
#                 raise ValidationError(_(f"{bed_names} are already used for another crop "))
#             else:
#                 rec.state = 'confirm'




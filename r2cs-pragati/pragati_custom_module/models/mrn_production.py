from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'


    # pr_request_id = fields.Many2one('purchase.request', string='PR Id')

    # def action_convert_purchase_request(self):
    #     purchase_request_obj = self.env['purchase.request']
    #     for record in self:
    #         if record.move_raw_ids:
    #             for line in record.move_raw_ids:
    #                 if line.on_hand_qty <= 0 and line.product_uom_qty > 0:
    #                     # Create purchase request
    #                     pr_order = purchase_request_obj.create({
    #                         'location_id': line.location_id.id,
    #                         # Add any other required fields here
    #                     })

    #                     # Add purchase request lines
    #                     pr_request_line_values = []
    #                     for rec in record.move_raw_ids:
    #                         # If on_hand_qty is available, use product_uom_qty for quantity
    #                         if rec.on_hand_qty < rec.product_uom_qty:
    #                             quantity = rec.product_uom_qty - rec.on_hand_qty
    #                         else:
    #                             continue
    #                         pr_request_line_values.append((0, 0, {
    #                             'product_id': rec.product_id.id,
    #                             'quantity': quantity,
    #                             # Add any other required fields for purchase request line here
    #                         }))
    #                     pr_order.pr_request_line_ids = pr_request_line_values

    #                     # Open the created purchase request
    #                     action = self.env.ref('material_and_pr_requistion.action_for_purchase_request').read()[0]
    #                     action['views'] = [(self.env.ref('material_and_pr_requistion.view_for_purchase_request_menu_form').id, 'form')]
    #                     action['res_id'] = pr_order.id
    #                     return action

    #     self.pr_request_id = action.id


    def action_update_component_quantities(self):
        for record in self:
            all_done = all(line.quantity_done >= line.product_uom_qty for line in record.move_raw_ids)
            if all_done:
                raise ValidationError(_('The Consume Quantities are all set, Please check it.'))

            for line in record.move_raw_ids:
                line.quantity_done = max(line.quantity_done, line.product_uom_qty)
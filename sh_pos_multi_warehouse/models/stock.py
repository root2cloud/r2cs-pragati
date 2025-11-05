# Copyright (C) Softhealer Technologies.
from odoo import fields, models, api
from odoo.tools import float_is_zero
from odoo.exceptions import UserError, ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
        """We'll create some picking based on order_lines"""
        
        pickings = self.env['stock.picking']
        stockable_lines = lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding))
        if not stockable_lines:
            return pickings
        positive_lines = stockable_lines.filtered(lambda l: l.qty > 0)
        negative_lines = stockable_lines - positive_lines
        picking_list = []
        if positive_lines:

            location_list = []
            for line in positive_lines:
                if line.location_id.id:
                    if int(line.location_id.id) not in location_list:
                        location_list.append(int(line.location_id.id))

            for location in location_list:
                warehouse = self.env['stock.warehouse'].sudo().search([('lot_stock_id','=',int(location))],limit=1)
                if warehouse:
                    if warehouse.picking_type_id:
                        generate_picking_type = warehouse.picking_type_id
                        return_pick_type = warehouse.picking_type_id.return_picking_type_id or warehouse.picking_type_id
                    else:
                        generate_picking_type = picking_type
                
                else:
                        generate_picking_type = picking_type

                positive_picking = self.env['stock.picking'].create(
                    self._prepare_picking_vals(
                        partner, generate_picking_type, location, location_dest_id)
                )
                if positive_picking:
                    for line in positive_lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)):
                    
                        if(int(line.location_id.id) == location):
                            
                            positive_picking._create_move_from_pos_order_lines(
                                line)
                            picking_list.append(positive_picking)
                            try:
                                picking_sate = line.order_id.config_id.sh_picking_sate
                                multi_warehouse_feature = line.order_id.config_id.sh_enable_multi_warehouse
                                with self.env.cr.savepoint():
                                    if picking_sate and multi_warehouse_feature:
                                        positive_picking.action_confirm()
                                    else:
                                        positive_picking._action_done()
                            except (UserError, ValidationError):
                                pass
            if not location_list:
                location_id = picking_type.default_location_src_id.id
                positive_picking = self.env['stock.picking'].create(
                self._prepare_picking_vals(
                        partner, picking_type, location_id, location_dest_id))
                if positive_picking:
                    positive_picking._create_move_from_pos_order_lines(
                        line)
                    try:
                        with self.env.cr.savepoint():
                            positive_picking._action_done()
                    except (UserError, ValidationError):
                        pass
            pickings |= positive_picking
        if negative_lines:
            if picking_type.return_picking_type_id:
                return_picking_type = picking_type.return_picking_type_id
                return_location_id = return_picking_type.default_location_dest_id.id
            else:
                return_picking_type = picking_type
                return_location_id = picking_type.default_location_src_id.id

            negative_picking = self.env['stock.picking'].create(
                self._prepare_picking_vals(partner, return_picking_type, location_dest_id, return_location_id)
            )
            negative_picking._create_move_from_pos_order_lines(negative_lines)
            try:
                with self.env.cr.savepoint():
                    negative_picking._action_done()
            except (UserError, ValidationError):
                pass
            pickings |= negative_picking
        return pickings

class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Operation Type',
        domain="[('warehouse_id', '=', id), ('warehouse_id.company_id', '=', company_id)]",
        ondelete='restrict')

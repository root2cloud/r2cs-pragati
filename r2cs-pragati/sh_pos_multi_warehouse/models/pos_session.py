# Copyright (C) Softhealer Technologies.
from odoo import fields, models, api

class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()

        if 'stock.warehouse' not in result:
            result.append('stock.warehouse')
        
        if 'stock.quant' not in result:
            result.append('stock.quant')

        if 'stock.location' not in result:
            result.append('stock.location')
       
        return result

    def _loader_params_stock_warehouse(self):
        return {'search_params': {'domain': [], 'fields': ["id", "lot_stock_id", "code", "name"], 'load': False}}

    def _get_pos_ui_stock_warehouse(self, params):
        return self.env['stock.warehouse'].search_read(**params['search_params'])

    def _loader_params_stock_location(self):
        return {'search_params': {'domain': [], 'fields': ["id", "name", "display_name", "usage"], 'load': False}}

    def _get_pos_ui_stock_location(self, params):
        return self.env['stock.location'].search_read(**params['search_params'])

    def _loader_params_stock_quant(self):
        return {'search_params': {'domain': [('location_id.usage','=','internal')], 'fields': ["id", "product_id", "location_id", "company_id", "quantity", "reserved_quantity"], 'load': False}}

    def _get_pos_ui_stock_quant(self, params):
        return self.env['stock.quant'].search_read(**params['search_params'])

    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend(['detailed_type'])
        return result

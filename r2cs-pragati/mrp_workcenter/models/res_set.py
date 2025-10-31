from odoo import models, fields, api

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    map_box_token = fields.Char(
        string="Mapbox Token",  # ✅ This is the missing part
        config_parameter='your_module.map_box_token',
    )
    group_mrp_wo_tablet_timer = fields.Boolean(
        string="Enable Work Order Timer",  # ✅ REQUIRED
        group='mrp.group_mrp_user',
        implied_group='mrp_workorder.group_mrp_wo_tablet_timer',
        config_parameter='mrp_workorder.group_mrp_wo_tablet_timer',
    )
    currency_provider = fields.Selection(
        selection=[('ecb', 'European Central Bank'), ('xe_com', 'XE.com')],
        string="Currency Exchange Provider",  # ✅ Add this
        config_parameter='res_currency.currency_provider',
    )
    currency_interval_unit = fields.Selection(
        selection=[('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')],
        string="Currency Update Interval Unit",  # <--- Add this line
        config_parameter='res_currency.currency_interval_unit',
    )
    currency_next_execution_date = fields.Datetime(
        string="Next Currency Update Execution Date",  # ← Add this line
        config_parameter='res_currency.currency_next_execution_date',
    )
from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    hide_validate_button = fields.Boolean(compute='_compute_hide_validate_button')

    @api.depends('user_id')
    def _compute_hide_validate_button(self):
        """Hide the Validate button for 'acharyulu' user"""
        for record in self:
            record.hide_validate_button = self.env.user.login == 'acharyulu@pragatibiopharma.com'

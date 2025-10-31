from odoo import models, fields

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    quality_check_fail = fields.Boolean(string="Quality Check Failed")
    check_ids = fields.Char(
        string="Quality Checks"
    )
    quality_check_todo = fields.Char(
        string="Quality Checks todo"
    )
    quality_alert_count = fields.Char(
        string="Quality alert count"
    )
    manufacturing_date = fields.Char(
        string="manufacturing date"
    )
    expired_date = fields.Date( string = "Date")
    total_quantity = fields.Integer( string = "quantity")
    product_quantity_loss = fields.Integer( string = "loss_quantity")

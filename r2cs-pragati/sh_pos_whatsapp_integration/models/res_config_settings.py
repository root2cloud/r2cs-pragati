# Copyright (C) Softhealer Technologies.
from odoo import fields, models

class ResConfigSettiongsInhert(models.TransientModel):
    _inherit = "res.config.settings"

    pos_enable_whatsapp = fields.Boolean(related="pos_config_id.enable_whatsapp", readonly=False)
    pay_invoices_online = fields.Boolean(config_parameter='account_payment.enable_portal_payment', string="Invoice")

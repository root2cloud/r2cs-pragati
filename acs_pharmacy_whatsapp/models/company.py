# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    acs_pharmacy_order_template_id = fields.Many2one('acs.whatsapp.template', 'Pharmacy Order Template')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    acs_laboratory_request_template_id = fields.Many2one('acs.whatsapp.template', 'Laboratory Request Template')
    acs_laboratory_result_template_id = fields.Many2one('acs.whatsapp.template', 'Laboratory Result Template')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
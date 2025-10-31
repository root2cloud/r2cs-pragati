# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    acs_radiology_request_template_id = fields.Many2one('acs.whatsapp.template', 'Radiology Request Template')
    acs_radiology_result_template_id = fields.Many2one('acs.whatsapp.template', 'Radiology Result Template')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
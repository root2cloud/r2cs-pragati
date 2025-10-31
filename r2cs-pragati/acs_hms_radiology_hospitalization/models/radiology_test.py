# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PatientRadiologyTest(models.Model):
    _inherit = "patient.radiology.test"

    STATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}

    hospitalization_id = fields.Many2one('acs.hospitalization', string='Hospitalization', ondelete='restrict', states=STATES)
    print_in_discharge = fields.Boolean("Print in Discharge Report")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
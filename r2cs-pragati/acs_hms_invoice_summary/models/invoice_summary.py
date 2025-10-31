# -*- coding: utf-8 -*-

from odoo import api, fields, models,_

class AcsInvoiceSummary(models.Model):
    _inherit = 'acs.invoice.summary'

    STATES = {'done': [('readonly', True)]}

    patient_id = fields.Many2one('hms.patient',  string='Patient', index=True, states=STATES, required=True)
    partner_id = fields.Many2one('res.partner',  related="patient_id.partner_id", string='Partner', index=True, store=True)
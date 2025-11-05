# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class AcsHmsPatient(models.Model):
    _name="hms.patient"
    _inherit = ['hms.patient', 'acs.documnt.view.mixin']


class AcsHmsTreatment(models.Model):
    _name="hms.treatment"
    _inherit = ['hms.treatment', 'acs.documnt.view.mixin']


class AcsPatientProcedure(models.Model):
    _name="acs.patient.procedure"
    _inherit = ['acs.patient.procedure', 'acs.documnt.view.mixin']


class AcsHmsAppointment(models.Model):
    _name="hms.appointment"
    _inherit = ['hms.appointment', 'acs.documnt.view.mixin']

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
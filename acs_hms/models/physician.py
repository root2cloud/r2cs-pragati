# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging


class Physician(models.Model):
    _inherit = 'hms.physician'

    # def _phy_rec_count(self):
    #     _logger = logging.getLogger(__name__)
    #     _logger.info("Computing physician records.")
    #     Patient = self.env['hms.patient']
    #     for record in self.with_context(active_test=False):
    #         _logger.info("Processing physician record with ID: %s", record.id)
    #         domain = ['|', ('primary_physician_id', '=', record.id), ('secondary_physician_id', '=', record.id)]
    #         _logger.info("Domain: %s", domain)
    #         try:
    #             record.patient_count = Patient.search_count(domain)
    #         except Exception as e:
    #             _logger.error("Error while computing patient count: %s", str(e))
    #             record.patient_count = 0  # or any default value

    consultaion_service_id = fields.Many2one('product.product', ondelete='restrict', string='Consultation Service')
    followup_service_id = fields.Many2one('product.product', ondelete='restrict', string='Followup Service')
    appointment_duration = fields.Float('Default Consultation Duration', default=0.25)

    is_primary_surgeon = fields.Boolean(string='Primary Surgeon')
    signature = fields.Binary('Signature')
    hr_presence_state = fields.Selection(related='user_id.employee_id.hr_presence_state')
    appointment_ids = fields.One2many("hms.appointment", "physician_id", "Appointments")
    treatment_count = fields.Integer(compute='_compute_treatment_count', string='# Treatments')
    appointment_count = fields.Integer(compute='_compute_appointment_count', string='# Appointment')
    prescription_count = fields.Integer(compute='_compute_prescription_count', string='# Prescriptions')
    patient_count = fields.Integer(compute='_compute_patient_count', string='# Patients')
    def _compute_patient_count(self):
        _logger = logging.getLogger(__name__)
        _logger.info("Computing patient count.")
        Patient = self.env['hms.patient']
        for record in self.with_context(active_test=False):
            _logger.info("Processing physician record with ID: %s", record.id)
            domain = ['|', ('primary_physician_id', '=', record.id), ('secondary_physician_id', '=', record.id)]
            _logger.info("Domain: %s", domain)
            try:
                record.patient_count = Patient.search_count(domain)
            except Exception as e:
                _logger.error("Error while computing patient count: %s", str(e))
                record.patient_count = 0  # or any default value

    def _compute_treatment_count(self):
        Treatment = self.env['hms.treatment']  # replace with your treatment model
        for record in self:
            domain = [('physician_id', '=', record.id)]  # replace with your domain
            record.treatment_count = Treatment.search_count(domain)

    def _compute_appointment_count(self):
        Appointment = self.env['hms.appointment']  # replace with your appointment model
        for record in self:
            domain = [('physician_id', '=', record.id)]  # replace with your domain
            record.appointment_count = Appointment.search_count(domain)

    def _compute_prescription_count(self):
        Prescription = self.env['prescription.order']  # replace with your prescription model
        for record in self:
            domain = [('physician_id', '=', record.id)]  # replace with your domain
            record.prescription_count = Prescription.search_count(domain)


    def action_treatment(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.acs_action_form_hospital_treatment")
        action['domain'] = [('physician_id','=',self.id)]
        action['context'] = {'default_physician_id': self.id}
        return action

    def action_appointment(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_appointment")
        action['domain'] = [('physician_id','=',self.id)]
        action['context'] = {'default_physician_id': self.id}
        return action

    def action_prescription(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.act_open_hms_prescription_order_view")
        action['domain'] = [('physician_id','=',self.id)]
        action['context'] = {'default_physician_id': self.id}
        return action

    def action_patients(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms_base.action_patient")
        action['domain'] = ['|',('primary_physician_id','=',self.id)]
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
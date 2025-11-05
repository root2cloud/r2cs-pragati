# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ACSAppointment(models.Model):
    _inherit='hms.appointment'

    def _rec_count(self):
        for rec in self:
            rec.request_count = len(rec.lab_request_ids)
            rec.test_count = len(rec.test_ids)

    def _acs_get_attachemnts(self):
        attachments = super(ACSAppointment, self)._acs_get_attachemnts()
        attachments += self.test_ids.mapped('attachment_ids')
        return attachments

    test_ids = fields.One2many('patient.laboratory.test', 'appointment_id', string='Lab Tests')
    lab_request_ids = fields.One2many('acs.laboratory.request', 'appointment_id', string='Lab Requests')
    request_count = fields.Integer(compute='_rec_count', string='# Lab Requests')
    test_count = fields.Integer(compute='_rec_count', string='# Lab Tests')

    def action_lab_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.hms_action_lab_test_request")
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id, 'default_appointment_id': self.id}
        action['views'] = [(self.env.ref('acs_laboratory.patient_laboratory_test_request_form').id, 'form')]
        return action

    def action_view_test_results(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.action_lab_result")
        action['domain'] = [('id','in',self.test_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id, 'default_appointment_id': self.id}
        return action

    def action_view_lab_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.hms_action_lab_test_request")
        action['domain'] = [('id','in',self.lab_request_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id, 'default_appointment_id': self.id}
        return action

    #Method to collect common invoice related records data
    def acs_appointment_common_data(self, invoice_id):
        data = super().acs_appointment_common_data(invoice_id)
        req_ids = self.mapped('lab_request_ids').filtered(lambda req: not req.invoice_id)
        data += req_ids.acs_common_invoice_laboratory_data(invoice_id)
        return data


class Treatment(models.Model):
    _inherit = "hms.treatment"

    def _lab_rec_count(self):
        for rec in self:
            rec.request_count = len(rec.request_ids)
            rec.test_count = len(rec.test_ids)

    request_ids = fields.One2many('acs.laboratory.request', 'treatment_id', string='Lab Requests')
    test_ids = fields.One2many('patient.laboratory.test', 'treatment_id', string='Tests')
    request_count = fields.Integer(compute='_lab_rec_count', string='# Lab Requests')
    test_count = fields.Integer(compute='_lab_rec_count', string='# Lab Tests')

    def action_lab_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.hms_action_lab_test_request")
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_treatment_id': self.id}
        action['views'] = [(self.env.ref('acs_laboratory.patient_laboratory_test_request_form').id, 'form')]
        return action

    def action_lab_requests(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.hms_action_lab_test_request")
        action['domain'] = [('id','in',self.request_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_treatment_id': self.id}
        return action

    def action_view_test_results(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_laboratory.action_lab_result")
        action['domain'] = [('id','in',self.test_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_treatment_id': self.id}
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
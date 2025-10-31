#-*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import json


class HmsPatient(models.Model):
    _inherit = 'hms.patient'

    def acs_get_action(self):
        acs_action_id = self.env.ref('acs_hms_base.action_patient')
        for rec in self:
            rec.acs_action_id = acs_action_id

    acs_action_id = fields.Integer(compute="acs_get_action")

    def acs_hms_image_chart(self, param=''):
        self.ensure_one()
        Attachment = self.env['ir.attachment']
        image, image_name = Attachment.get_default_chart_image(False, self.company_id)
        attachment = Attachment.acs_create_chart_image(image, image_name, self._name, self.id)
        acs_action_id = self._context.get('params', {}).get('action') or self._context.get('acs_action_id')
        param = '?acs_model=%s&acs_rec_id=%s&acs_action_id=%s' % (self._name, self.id, acs_action_id)
        action = attachment.acs_hms_image_chart(param=param)
        return action

class HmsTreatment(models.Model):
    _inherit = 'hms.treatment'

    def acs_get_action(self):
        acs_action_id = self.env.ref('acs_hms.acs_action_form_hospital_treatment')
        for rec in self:
            rec.acs_action_id = acs_action_id

    acs_action_id = fields.Integer(compute="acs_get_action")

    def acs_hms_image_chart(self):
        self.ensure_one()
        Attachment = self.env['ir.attachment']
        image, image_name = Attachment.get_default_chart_image(self.department_id, self.company_id)
        attachment = Attachment.acs_create_chart_image(image, image_name, self._name, self.id)
        acs_action_id = self._context.get('params', {}).get('action') or self._context.get('acs_action_id')
        param = '?acs_model=%s&acs_rec_id=%s&acs_action_id=%s' % (self._name, self.id, acs_action_id)
        action = attachment.acs_hms_image_chart(param=param)
        return action


class HmsPatientProcedure(models.Model):
    _inherit = 'acs.patient.procedure'

    def acs_get_action(self):
        acs_action_id = self.env.ref('acs_hms.action_acs_patient_procedure')
        for rec in self:
            rec.acs_action_id = acs_action_id

    acs_action_id = fields.Integer(compute="acs_get_action")

    def acs_hms_image_chart(self):
        self.ensure_one()
        Attachment = self.env['ir.attachment']
        image, image_name = Attachment.get_default_chart_image(self.department_id, self.company_id)
        attachment = Attachment.acs_create_chart_image(image, image_name, self._name, self.id)
        acs_action_id = self._context.get('params', {}).get('action') or self._context.get('acs_action_id')
        param = '?acs_model=%s&acs_rec_id=%s&acs_action_id=%s' % (self._name, self.id, acs_action_id)
        action = attachment.acs_hms_image_chart(param=param)
        return action


class HmsAppointment(models.Model):
    _inherit = 'hms.appointment'

    def acs_get_action(self):
        acs_action_id = self.env.ref('acs_hms.action_appointment')
        for rec in self:
            rec.acs_action_id = acs_action_id

    acs_action_id = fields.Integer(compute="acs_get_action")

    def acs_hms_image_chart(self):
        self.ensure_one()
        Attachment = self.env['ir.attachment']
        image, image_name = Attachment.get_default_chart_image(self.department_id, self.company_id)
        attachment = Attachment.acs_create_chart_image(image, image_name, self._name, self.id)
        acs_action_id = self._context.get('params', {}).get('action') or self._context.get('acs_action_id')
        param = '?acs_model=%s&acs_rec_id=%s&acs_action_id=%s' % (self._name, self.id, acs_action_id)
        action = attachment.acs_hms_image_chart(param=param)
        return action


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    acs_default_chart_image = fields.Binary('Default Chart Image', help="Image to use in chart by default.")
    acs_default_chart_image_name = fields.Char('Default Chart Image name')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
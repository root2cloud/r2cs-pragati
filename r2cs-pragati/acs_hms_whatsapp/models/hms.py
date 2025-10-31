# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HmsAppointment(models.Model):
    _name = 'hms.appointment'
    _inherit = ['hms.appointment','acs.whatsapp.mixin']

    @api.model
    def send_appointment_reminder(self):
        reminder_appointments = super(HmsAppointment, self).send_appointment_reminder()
        for appointment in reminder_appointments:
            if appointment and appointment.patient_id and appointment.patient_id.mobile and appointment.company_id.acs_appointment_reminder_template_id:
                template = appointment.company_id.acs_appointment_reminder_template_id
                rendered = self.env['mail.render.mixin']._render_template(template.body_message, appointment._name, [appointment.id])
                msg = rendered[appointment.id]
                self.send_whatsapp(msg, appointment.patient_id.mobile, appointment.patient_id.partner_id, template=template, res_model='hms.appointment', res_id=appointment.id)
        return reminder_appointments

    #can be updated for further changes easily 
    def get_acs_wa_appointment_reg_message(self):
        company_id = self.sudo().company_id or self.env.user.sudo().company_id
        return company_id.acs_appointment_confirmation_template_id

    def appointment_confirm(self):
        res = super(HmsAppointment, self).appointment_confirm()
        for rec in self:
            template = rec.get_acs_wa_appointment_reg_message()
            if template and rec.patient_id and rec.patient_id.mobile:
                rendered = self.env['mail.render.mixin']._render_template(template.body_message, rec._name, [rec.id])
                msg = rendered[rec.id]
                self.send_whatsapp(msg, rec.patient_id.partner_id.mobile, rec.patient_id.partner_id, template=template, res_model='hms.appointment', res_id=rec.id)
        return res

    def whatsapp_chat_history(self):
        if not (self.patient_id and self.patient_id.mobile):
            raise UserError(_("No Mobile no linked with Record."))     
        return self.acs_whatsapp_chat_history(self.patient_id.partner_id, self.patient_id.mobile)

    def acs_reschedule_appointments(self, reschedule_time):
        res = super(HmsAppointment, self).acs_reschedule_appointments(reschedule_time)
        for rec in self:
            company_id = self.sudo().company_id or self.env.user.sudo().company_id
            template = company_id.acs_appointment_reschedule_template_id
            if template and rec.patient_id and rec.patient_id.mobile:
                rendered = self.env['mail.render.mixin']._render_template(template.body_message, rec._name, [rec.id])
                msg = rendered[rec.id]
                self.send_whatsapp(msg, rec.patient_id.partner_id.mobile, rec.patient_id.partner_id, template=template, res_model='hms.appointment', res_id=rec.id)
        return res


class HmsPatient(models.Model):
    _name = 'hms.patient'
    _inherit = ['hms.patient','acs.whatsapp.mixin']

    #can be updated for further changes easily 
    def get_acs_wa_patient_reg_message(self):
        company_id = self.sudo().company_id or self.env.user.sudo().company_id
        return company_id.acs_patient_reg_template_id

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        template = res.get_acs_wa_patient_reg_message()
        for record in res:    
            if template and record.mobile:
                rendered = self.env['mail.render.mixin']._render_template(template.body_message, record._name, [record.id])
                msg = rendered[res.id]
                self.send_whatsapp(msg, record.partner_id.mobile, record.partner_id, template=template, res_model='hms.patient', res_id=record.id)
        return res

    def whatsapp_chat_history(self):
        if not self.mobile:
            raise UserError(_("No Mobile no linked with Record."))     
        return self.acs_whatsapp_chat_history(self.partner_id, self.mobile)

    def action_send_otp_whatsapp(self):
        self.partner_id.action_send_otp_whatsapp()

    def action_verify_otp_whatsapp(self):
        self.partner_id.action_verify_otp_whatsapp()


class AcsCreateWAMsg(models.TransientModel):
    _inherit = 'acs.send.whatsapp'

    @api.model
    def default_get(self,fields):
        context = self._context or {}
        res = super(AcsCreateWAMsg, self).default_get(fields)
        if context.get('active_model')=='hms.patient':
            patient = self.env['hms.patient'].browse(context.get('active_ids', []))
            res.update({
                'partner_id': patient.partner_id.id,
                'mobile': patient.mobile,
            })

        if context.get('active_model')=='hms.appointment':
            appointment = self.env['hms.appointment'].browse(context.get('active_ids', []))
            if not appointment.patient_id:
                raise UserError(_("No Patient linked with Record."))
            res.update({
                'partner_id': appointment.patient_id.partner_id.id,
                'mobile': appointment.patient_id.mobile,
            })
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
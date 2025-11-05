# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AcsLaboratoryRequest(models.Model):
    _name = 'acs.laboratory.request'
    _inherit = ['acs.laboratory.request','acs.whatsapp.mixin']

    def button_requested(self):
        res = super(AcsLaboratoryRequest, self).button_requested()
        self.filtered(lambda r: r.patient_id.partner_id.mobile).action_send_whatsapp()
        return res

    def action_send_whatsapp(self):
        for rec in self:
            if not rec.patient_id.partner_id.mobile:
                raise UserError(_("Please Define Mobile Number in Customer."))

            template = self.env.user.sudo().company_id.acs_laboratory_request_template_id
            if rec.patient_id.partner_id.mobile and template:
                rendered = self.env['mail.render.mixin']._render_template(template.body_message, rec._name, [rec.id])
                msg = rendered[rec.id]
                rec.send_whatsapp(msg, rec.patient_id.partner_id.mobile, rec.patient_id.partner_id, template=template)
                rec.message_post(body="%s Sent Details by WhatsApp." % (self.env.user.sudo().name))
        return True


class PatientLaboratoryTest(models.Model):
    _name = 'patient.laboratory.test'
    _inherit = ['patient.laboratory.test','acs.whatsapp.mixin']

    def action_done(self):
        res = super(PatientLaboratoryTest, self).action_done()
        self.filtered(lambda r: r.patient_id.partner_id.mobile).action_send_whatsapp()
        return res

    def action_send_whatsapp(self):
        for rec in self:
            if not rec.patient_id.partner_id.mobile:
                raise UserError(_("Please Define Mobile Number in Customer."))

            template = self.env.user.sudo().company_id.acs_laboratory_result_template_id
            if rec.patient_id.partner_id.mobile and template:
                rendered = self.env['mail.render.mixin']._render_template(template.body_message, rec._name, [rec.id])
                msg = rendered[rec.id]
                rec.send_whatsapp(msg, rec.patient_id.partner_id.mobile, rec.patient_id.partner_id, template=template)
                rec.message_post(body="%s Sent Details by WhatsApp." % (self.env.user.sudo().name))
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import math, random


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner','acs.whatsapp.mixin']

    def _count_whatsapp(self):
        Announcement = self.env['acs.whatsapp.announcement']
        for rec in self:
            rec.whatsapp_count = len(rec.whatsapp_ids.ids)
            rec.whatsapp_announcement_count = Announcement.search_count([('partner_ids','in',rec.id)])

    whatsapp_ids = fields.One2many('acs.whatsapp.message', 'partner_id', string='whatsapp')
    whatsapp_count = fields.Integer(compute="_count_whatsapp", string="#whatsapp Count")
    whatsapp_announcement_count = fields.Integer(compute="_count_whatsapp", string="#whatsapp Announcement Count")
    acs_otp_whatsapp = fields.Char(string="OTP Whatsapp", copy=False)
    generated_otp_whatsapp = fields.Char(string="Generated OTP Whatsapp")
    verified_mobile_whatsapp = fields.Boolean(string="Verified Whatsapp", help="The mobile number is verified using the Whatsapp message")

    #can be updated for further changes easily 
    def get_acs_verify_otp_msg_whatsapp(self):
        company_id = self.sudo().company_id or self.env.user.sudo().company_id
        return company_id.acs_waba_verify_otp_template_id

    def whatsapp_chat_history(self):
        if not self.mobile:
            raise UserError(_("No Mobile no linked with Record."))     
        return self.acs_whatsapp_chat_history(self.partner_id, self.mobile)

    def action_send_otp_whatsapp(self):
        self.generateotp_whatsapp()
        for rec in self:
            template_id = rec.get_acs_verify_otp_msg_whatsapp()
            if template_id:
                if rec.mobile:
                    rendered = self.env['mail.render.mixin']._render_template(template_id.body_message, rec._name, [rec.id])
                    msg = rendered[rec.id]
                    self.with_context(force_send=True).send_whatsapp(msg, rec.mobile, False, template=template_id, res_model='res.partner', res_id=rec.id)
                else:
                    raise UserError(_('Please define Mobile Number in the patient.'))
            else:
                raise UserError(_("Message fromat is not Configured, please contact administrator configure it first."))

    def generateotp_whatsapp(self):
        digits = "0123456789"
        otp = ""
        for i in range(4):
            otp += digits[math.floor(random.random() * 10)]
            self.generated_otp_whatsapp = otp

    def action_verify_otp_whatsapp(self):
        if self.acs_otp_whatsapp:
            pass
        else:
            raise UserError(_('Please enter OTP.'))

        if self.generated_otp_whatsapp == self.acs_otp_whatsapp:
            self.verified_mobile_whatsapp = True
        else:
            raise UserError(_('The OTP you entered is invalid. Please enter the correct OTP.'))

    def action_acs_whatsapp(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_whatsapp.action_acs_whatsapp")
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {
            'default_partner_id': self.id,
            'default_mobile': self.mobile,
        }
        return action

    def action_acs_whatsapp_announcement(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_whatsapp.action_whatsapp_announcement")
        action['domain'] = [('partner_ids', 'in', self.id)]
        action['context'] = { 'default_partner_ids': [(6, 0, [self.id])] }
        return action

    def whatsapp_chat_history(self):
        if not self.mobile:
            raise UserError(_("No Mobile no linked with Record."))     
        return self.acs_whatsapp_chat_history(self, self.mobile)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
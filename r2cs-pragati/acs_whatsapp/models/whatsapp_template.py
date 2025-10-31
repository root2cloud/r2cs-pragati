# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


MESSAGE_TYPE = [
    ('TEXT', 'Message'),
    ('DOCUMENT', 'Document'),
    ('IMAGE', 'Image')
]

class whatsappTemplate(models.Model):
    _name = 'acs.whatsapp.template'
    _description = 'whatsapp Template'

    def acs_get_default_lang(self):
        lang = self.env['res.lang'].sudo().search([('code','=',self.env.user.lang)], limit=1)
        return lang

    READONLY_STATES = {'approved': [('readonly', True)], 'cancel': [('readonly', True)]}

    name = fields.Text(string='Name', required=True, states=READONLY_STATES)
    state =  fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved')
    ], string='Status', default='draft', states=READONLY_STATES)

    header_message_type =  fields.Selection(MESSAGE_TYPE, string='Header Message Type', states=READONLY_STATES)
    header_message = fields.Text(string='Header Message', states=READONLY_STATES)
    header_file =  fields.Binary(string='Header File', states=READONLY_STATES)
    header_file_name =  fields.Char(string='Header File Name', states=READONLY_STATES)

    body_message_type =  fields.Selection(MESSAGE_TYPE, string='Body Message Type', default='TEXT', states=READONLY_STATES, required=True)
    body_message = fields.Text(string='Body Message', states=READONLY_STATES)
    body_file =  fields.Binary(string='Body File', states=READONLY_STATES)
    body_file_name =  fields.Char(string='Body File Name', states=READONLY_STATES)

    footer_message_type =  fields.Selection(MESSAGE_TYPE, string='Footer Message Type', states=READONLY_STATES)
    footer_message = fields.Text(string='Footer Message', states=READONLY_STATES)
    footer_file =  fields.Binary(string='Footer File', states=READONLY_STATES)
    footer_file_name =  fields.Char(string='Footer File Name', states=READONLY_STATES)

    category =  fields.Char("Category", default="TRANSACTIONAL")
    whasaap_id = fields.Char("WhatsApp ID")
    whatsapp_data = fields.Text("Whatsapp Data")
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.company, states=READONLY_STATES)

    partner_ids = fields.Many2many("res.partner", "partner_whatsapp_template_rel", "partner_id", "whatsapp_template_id", "Partners", states=READONLY_STATES)
    employee_ids = fields.Many2many("hr.employee", "employee_whatsapp_template_rel", "employee_id", "whatsapp_template_id", "Employees", states=READONLY_STATES)
    language_id = fields.Many2one('res.lang', 'Language', default=acs_get_default_lang, states=READONLY_STATES)

    def action_approve(self):
        self.state = 'approved'

    def action_draft(self):
        self.state = 'draft'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
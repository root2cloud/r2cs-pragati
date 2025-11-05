# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
from datetime import datetime

import base64
from io import BytesIO
import qrcode
import io



class ResPartner(models.Model):
    _inherit= "res.partner"

    is_referring_doctor = fields.Boolean(string="Is Refereinng Physician")
    #ACS Note: Adding assignee as relation with partner for receptionist or Doctor to access only those patients assigned to them

class ResUsers(models.Model):
    _inherit= "res.users"

    @api.depends('physician_ids')
    def _compute_physician_count(self):
        for user in self.with_context(active_test=False):
            user.physician_count = len(user.physician_ids)

    def _compute_patient_count(self):
        Patient = self.env['hms.patient']
        for user in self.with_context(active_test=False):
            user.patient_count = Patient.search_count([('partner_id','=', user.partner_id.id)])

    department_ids = fields.Many2many('hr.department', 'user_department_rel', 'user_id','department_id', 
        domain=[('patient_department', '=', True)], string='Departments')
    physician_count = fields.Integer(string="#Physician", compute="_compute_physician_count")
    physician_ids = fields.One2many('hms.physician', 'user_id', string='Related Physician')
    patient_count = fields.Integer(string="#Patient", compute="_compute_patient_count")

    #ACS NOTE: On changing the department clearing the cache for the access rights and record rules
    def write(self, values):
        if 'department_ids' in values:
            self.env['ir.model.access'].call_cache_clearing_methods()
            self.env['ir.rule'].clear_caches()
            #self.has_group.clear_cache(self)
        return super(ResUsers, self).write(values)

    @property
    def SELF_READABLE_FIELDS(self):
        user_fields = ['department_ids', 'physician_count', 'physician_ids', 'patient_count']
        return super().SELF_READABLE_FIELDS + user_fields

    @property
    def SELF_WRITEABLE_FIELDS(self):
        user_fields = ['department_ids', 'physician_count', 'physician_ids', 'patient_count']
        return super().SELF_WRITEABLE_FIELDS + user_fields 

    def action_create_physician(self):
        self.ensure_one()
        self.env['hms.physician'].create({
            'user_id': self.id,
            'name': self.name,
        })

    def action_create_patient(self):
        self.ensure_one()
        self.env['hms.patient'].create({
            'partner_id': self.partner_id.id,
            'name': self.name,
        })


class HospitalDepartment(models.Model):
    _inherit = 'hr.department'

    note = fields.Text('Note')
    patient_department = fields.Boolean("Patient Department", default=True)
    appointment_ids = fields.One2many("hms.appointment", "department_id", "Appointments")
    department_type = fields.Selection([('general','General')], string="Hospital Department")
    consultaion_service_id = fields.Many2one('product.product', ondelete='restrict', string='Consultation Service')
    followup_service_id = fields.Many2one('product.product', ondelete='restrict', string='Followup Service')
    image = fields.Binary(string='Image')


class ACSEthnicity(models.Model):
    _description = "Ethnicity"
    _name = 'acs.ethnicity'

    name = fields.Char(string='Name', required=True ,translate=True)
    code = fields.Char(string='Code')
    notes = fields.Char(string='Notes')

    _sql_constraints = [('name_uniq', 'UNIQUE(name)', 'Name must be unique!')]


class ACSMedicalAlert(models.Model):
    _name = 'acs.medical.alert'
    _description = "Medical Alert for Patient"

    name = fields.Char(required=True)
    description = fields.Text('Description')


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    birthday = fields.Date('Date of Birth')


class ACSFamilyRelation(models.Model):
    _name = 'acs.family.relation'
    _description = "Family Relation"
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    inverse_relation_id = fields.Many2one("acs.family.relation", string="Inverse Relation")

    def _compute_display_name(self):
        for rec in self:
            name = rec.name 
            if rec.inverse_relation_id:
                name += ' - ' + rec.inverse_relation_id.name
            rec.display_name = name

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The Relation must be unique!')
    ]

    def manage_inverser_relation(self):
        for rec in self:
            if rec.inverse_relation_id and not rec.inverse_relation_id.inverse_relation_id:
                rec.inverse_relation_id.inverse_relation_id = rec.id

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            record.manage_inverser_relation()
        return res

    def write(self, values):
        res = super(ACSFamilyRelation, self).write(values)
        self.manage_inverser_relation()
        return res


class product_template(models.Model):
    _inherit = "product.template"

    hospital_product_type = fields.Selection(selection_add=[('procedure', 'Procedure'), ('consultation','Consultation')])
    common_dosage_id = fields.Many2one('medicament.dosage', ondelete='cascade',
        string='Frequency', help='Drug form, such as tablet or gel')
    manual_prescription_qty = fields.Boolean("Manual Prescription Qty")
    procedure_time = fields.Float("Procedure Time")
    appointment_invoice_policy = fields.Selection([('at_end','Invoice in the End'),
        ('anytime','Invoice Anytime'),
        ('advance','Invoice in Advance')], string="Appointment Invoicing Policy")
    acs_allow_substitution = fields.Boolean(string='Allow Substitution')

    qr_code = fields.Binary(string='QR Code', readonly=True, copy=False)

    @api.model
    def create(self, vals_list):
        res = super(product_template, self).create(vals_list)
        for record in res:
            # Generate QR code upon order confirmation
            qr_code_data = record.generate_qr_code()
            # Encode the QR code data as base64 before saving
            qr_code_base64 = base64.b64encode(qr_code_data.getvalue())
            record.write({'qr_code': qr_code_base64})
        return res


    def generate_qr_code(self):
        # Generate QR code based on order details
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        # products_data = ', '.join(record.product_id.name for record in self.order_line if record.product_id)
        order_info = f"Order ID: {self.id}, Product Name: {self.name}"
        qr.add_data(order_info)
        qr.make(fit=True)

        # Create an in-memory buffer to store the QR code image
        qr_code_image = io.BytesIO()
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_code_image, format='PNG')

        # Reset the buffer to read from the start before returning it
        qr_code_image.seek(0)

        return qr_code_image


class ACSConsumableLine(models.Model):
    _inherit = "hms.consumable.line"

    appointment_id = fields.Many2one('hms.appointment', ondelete="cascade", string='Appointment')
    procedure_id = fields.Many2one('acs.patient.procedure', ondelete="cascade", string="Procedure")
    move_ids = fields.Many2many('stock.move', 'consumable_line_stock_move_rel', 'move_id', 'consumable_id', 'Kit Stock Moves', readonly=True)
    #ACS: In case of kit moves set move_ids but add move_id also. Else it may lead to comume material process again.
    procedure_product_id = fields.Many2one('product.product', string='Procedure', related='procedure_id.product_id', store=True)
    procedure_patient_id = fields.Many2one('hms.patient', string='Patient', related='procedure_id.patient_id', store=True)


class Physician(models.Model):
    _inherit = 'hms.physician'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            record.groups_id = [(4, self.env.ref('acs_hms.group_hms_jr_doctor').id)]
        return res

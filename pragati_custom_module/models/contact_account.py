from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
import re

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _description = 'Contact'
    _inherit = "res.partner"

    # *************************adding doctor field in advance payment receipt*****************

    patient_ids = fields.One2many('hms.patient', 'partner_id', string='Patients')

    primary_physician_id = fields.Many2one('hms.physician', string='Primary Care Doctor',
                                           compute='_compute_primary_physician')

    @api.depends('patient_ids.primary_physician_id')
    def _compute_primary_physician(self):
        for partner in self:
            patient = self.env['hms.patient'].search([('partner_id', '=', partner.id)], limit=1)
            partner.primary_physician_id = patient.primary_physician_id if patient else False

            # *****************************receipt editing****************************

    taxes_id = fields.Many2many('account.tax',
                                string="TDS Taxes",
                                )
    customer_type = fields.Selection([('vendor', 'Vendor'), ('customer', 'Customer'), ('ven_cus', 'Vendor&Customer')])

    @api.constrains('vat', 'l10n_in_pan')
    def _check_unique_vat_l10n_in_pan(self):
        for partner in self:
            if partner.vat:
                duplicate_vat_partners = self.search([('vat', '=', partner.vat), ('id', '!=', partner.id)])
                if duplicate_vat_partners:
                    raise UserError('A contact with the same Tax ID already exists!')

            # if partner.l10n_in_pan:
            #     duplicate_l10n_in_pan_partners = self.search([('l10n_in_pan', '=', partner.l10n_in_pan), ('id', '!=', partner.id)])
            #     if duplicate_l10n_in_pan_partners:
            #         raise UserError('A contact with the same PAN number already exists!')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    igst_tax = fields.Float(string='IGST', compute='_compute_taxes', store=True)
    cgst_tax = fields.Float(string='CGST', compute='_compute_taxes', store=True)
    sgst_tax = fields.Float(string='SGST', compute='_compute_taxes', store=True)
    sgst_tax_char = fields.Float(string='SGST Input', compute='_compute_taxes', store=True)
    cgst_tax_char = fields.Float(string='CGST Input', compute='_compute_taxes', store=True)
    igst_tax_char = fields.Float(string='IGST Input', compute='_compute_taxes', store=True)
    rem_tax_char = fields.Float(string='Other Tax Input', compute='_compute_taxes', store=True)
    remaining_tax = fields.Float(string="Line Taxes", compute='_compute_taxes', store=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes',
                               domain=['|', ('type_tax_use', '=', 'sale'), ('type_tax_use', '=', 'purchase')])
    name_of_record = fields.Char(string='Reference', related='move_id.name')
    gstin_number = fields.Char(string='GSTIN NO', related='move_id.partner_id.vat')
    l10n_in_hsn_code = fields.Char(string='HSN Code', related='product_id.l10n_in_hsn_code')
    l10n_in_gst_treatment = fields.Selection([
        ('regular', 'Registered Business - Regular'),
        ('composition', 'Registered Business - Composition'),
        ('unregistered', 'Unregistered Business'),
        ('consumer', 'Consumer'),
        ('overseas', 'Overseas'),
        ('special_economic_zone', 'Special Economic Zone'),
        ('deemed_export', 'Deemed Export'),
        ('uin_holders', 'UIN Holders'),
    ], string="GST Treatment", related='move_id.partner_id.l10n_in_gst_treatment')
    state_of_rec = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
        related='move_id.state'
    )

    # @api.onchange('partner_id', 'tds_apply')
    # def _onchange_partner_id_tds_apply(self):
    #     for line in self:
    #         if line.tds_apply and line.partner_id and line.partner_id.taxes_id:
    #             existing_taxes = line.tax_ids.ids
    #             new_taxes = line.partner_id.taxes_id.filtered(lambda tax: tax.id not in existing_taxes)
    #             line.tax_ids = [(4, tax.id) for tax in new_taxes]

    @api.depends('tax_ids', 'price_subtotal')
    def _compute_taxes(self):
        for line in self:
            igst = cgst = sgst = gst = remaining_tax = 0.0
            igst_char = cgst_char = sgst_char = rem_char = 0.0  # Separate variables for character fields

            for tax in line.tax_ids:
                # Use regular expression to extract numeric value
                match = re.search(r'(\d+(\.\d+)?)%', tax.name)
                tax_amount = float(match.group(1)) if match else 0.0

                if 'IGST' in tax.name.upper():
                    igst += line.price_subtotal * tax.amount / 100
                    igst_char += tax_amount
                elif 'CGST' in tax.name.upper():
                    cgst += line.price_subtotal * tax.amount / 100
                    cgst_char += tax_amount
                elif 'SGST' in tax.name.upper():
                    sgst += line.price_subtotal * tax.amount / 100
                    sgst_char += tax_amount
                elif 'GST' in tax.name.upper():
                    gst += line.price_subtotal * tax.amount / 100
                    sgst_char += tax_amount / 2
                    cgst_char += tax_amount / 2
                else:
                    # Handle remaining taxes here
                    remaining_tax += line.price_subtotal * tax.amount / 100
                    rem_char += tax_amount

            gst_split = gst / 2
            cgst += gst_split
            sgst += gst_split

            line.igst_tax = igst
            line.cgst_tax = cgst
            line.sgst_tax = sgst

            # Store the character fields
            line.igst_tax_char = igst_char
            line.cgst_tax_char = cgst_char
            line.sgst_tax_char = sgst_char
            line.rem_tax_char = rem_char

            # Store the remaining_tax value in the field
            line.remaining_tax = remaining_tax


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_default_category_id(self):
        domain = [('name', '=', "Account Move"), ('company_id', '=', self.env.company.id)]
        category_type = self.env['approval.category'].search(domain, limit=1)
        if category_type:
            return category_type.id
        return False

    tds_apply = fields.Selection([('yes', "Yes"), ('no', "No")], default='no', string="TDS availability",
                                 compute='_compute_tds_apply')
    stock_name = fields.Char(string='Stock_name')
    schedule_date = fields.Date(string='Schedule Date')

    journal_id_name = fields.Char(string="Journal Name", related="journal_id.name")
    original_bill = fields.Binary(string='Original Bill', store=True, tracking=True)
    bill_reference = fields.Char(string='MRN Bill Reference', tracking=True)
    account_approval_id = fields.Many2one("approval.request", string="Account Approval Id")
    account_approval_status = fields.Selection([('pending', 'Pending'), ('approve', 'Approved')],
                                               string='Approval Status', default='pending',
                                               compute='_compute_approve_status')
    request_owner_id = fields.Many2one('res.users', string="Request Owner",
                                       check_company=True, domain="[('company_ids', 'in', company_id)]",
                                       default=lambda self: self.env.user)
    category_id = fields.Many2one('approval.category', string='category', default=_get_default_category_id)
    approver_1 = fields.Char(string='Approver 1', compute='_compute_approvers_names', store=True)
    approver_2 = fields.Char(string='Approver 2', compute='_compute_approvers_names', store=True)
    reuse_button = fields.Boolean(default=False)
    department_id = fields.Many2one('hr.department', 'Department', tracking=True, required=True)
    approval_level_1 = fields.Many2one('res.users', string='Approver Level 1', domain="[('share', '=', False)]",
                                       readonly=True)
    approval_level_2 = fields.Many2one('res.users', string='Approver Level 2', domain="[('share', '=', False)]",
                                       readonly=True)
    approval_level_3 = fields.Many2one('res.users', string='Approver Level 3', domain="[('share', '=', False)]",
                                       readonly=True)

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            self.approval_level_1 = self.department_id.approver1.id if self.department_id.approver1 else False
            self.approval_level_2 = self.department_id.approver2.id if self.department_id.approver2 else False
            self.approval_level_3 = self.department_id.approver3.id if self.department_id.approver3 else False
        else:
            self.approval_level_1 = False
            self.approval_level_2 = False
            self.approval_level_3 = False

    @api.onchange('approval_level_1')
    def _onchange_approval_level_1(self):
        for record in self:
            if record.approval_level_1 and (
                    record.approval_level_1 == record.approval_level_2 or record.approval_level_1 == record.approval_level_3):
                raise UserError("The same Approver is selected more than once. Please check and correct it.")

    @api.onchange('approval_level_2')
    def _onchange_approval_level_2(self):
        for record in self:
            if record.approval_level_2 and (
                    record.approval_level_2 == record.approval_level_1 or record.approval_level_2 == record.approval_level_3):
                raise UserError("The same Approver is selected more than once. Please check and correct it.")

    @api.onchange('approval_level_3')
    def _onchange_approval_level_3(self):
        for record in self:
            if record.approval_level_3 and (
                    record.approval_level_3 == record.approval_level_1 or record.approval_level_3 == record.approval_level_2):
                raise UserError("The same Approver is selected more than once. Please check and correct it.")

    @api.depends('partner_id', 'partner_id.taxes_id')
    def _compute_tds_apply(self):
        for record in self:
            if record.partner_id and record.partner_id.taxes_id:
                record.tds_apply = "yes"
            else:
                record.tds_apply = "no"

    @api.depends('account_approval_id.approver_ids.status', 'account_approval_id.approver_ids')
    def _compute_approvers_names(self):
        for record in self:
            approver_1_name = False
            approver_2_name = False
            for approver in record.account_approval_id.approver_ids:
                if approver.status == 'approved':
                    if not approver_1_name:
                        approver_1_name = approver.user_id.name
                    else:
                        approver_2_name = approver.user_id.name
            record.approver_1 = approver_1_name
            record.approver_2 = approver_2_name

    @api.depends('account_approval_id.request_status')
    def _compute_approve_status(self):
        for record in self:
            if record.account_approval_id and record.account_approval_id.request_status == 'approved':
                record.account_approval_status = 'approve'
            else:
                record.account_approval_status = 'pending'

    def action_for_account_move_submit(self):
        approver_list = []

        if self.approval_level_1:
            approver_list.append(self.approval_level_1.id)
        if self.approval_level_2:
            approver_list.append(self.approval_level_2.id)
        if self.approval_level_3:
            approver_list.append(self.approval_level_3.id)

        for record in self:

            if not record.request_owner_id or not record.category_id:
                raise UserError("Please fill in the required fields: Purchase No, Request Owner, and Category")
            # if record.reuse_button:
            #     raise ValidationError(_("The record is already Submitted, Please check the Account Approval Id"))
            if record.move_type == 'in_invoice' and record.journal_id.name == 'Vendor Bills':
                rounding_option = self.env['account.cash.rounding'].search([('name', '=', 'ROUNDING')], limit=1)

                if rounding_option:
                    record.invoice_cash_rounding_id = rounding_option
            # Create an approval request
            approval_request = record.env['approval.request'].create({
                'request_owner_id': record.request_owner_id.id,
                'category_id': record.category_id.id,
                'account_move_sep_id': record.id,
                'company_id': self.env.company.id,
            })

            # Update the account_approval_id with the latest approval request ID
            record.write({'account_approval_id': approval_request.id})
            approver_values = []
            for line in approver_list:
                approver_values.append((0, 0, {
                    'user_id': line,
                    'required': True,
                }))
            # Link approval request to the approval approvers
            approval_request.write({
                'approver_ids': approver_values,
            })

            if record.account_approval_id:
                record.account_approval_id.action_confirm()
            # if record.account_approval_id:
            #     record.reuse_button = True

        return True

    def action_post(self):
        for record in self:
            if record.move_type == 'in_invoice' and not record.account_approval_id:
                raise UserError(_('Please submit the record for approval before posting'))
            else:
                return super(AccountMove, self).action_post()

    def action_reset_to_draft(self):
        for record in self:
            record.write({'state': 'draft'})
        return True

    # code for view button
    def open_pdf_viewer(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=account.move&id={}&field=original_bill'.format(self.id),
            'target': 'new',

        }

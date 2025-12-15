from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FreightChargeAdvice(models.Model):
    _name = "freight.charge.advice"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Freight Charge Advice"

    # @api.model
    # def _get_default_user_id(self):
    #     # Define the domain to fetch the user
    #     domain = [('name', '=', "Managing Director"), ('login', '=', 'ajay@pragatigroup.com')]
    #     user_type = self.env['res.users'].search(domain, limit=1)
    #     if user_type:
    #         return user_type.id
    #     else:
    #         return self.env.user.id

    # Setting the rec_name to document_number
    READONLY_STATES = {
        'payment': [('readonly', True)],
    }
    _rec_name = 'document_number'

    document_number = fields.Char(
        string="Document Number",
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: _('New')
    )

    journal_id = fields.Many2one(
        'account.journal',
        string="Cash/Bank account",
        required=True
    )
    vehicle_number = fields.Char(string="Vehicle Number", required=True)
    date = fields.Date(string="Date", default=fields.Date.context_today)
    vendor_name = fields.Char(related='account_id.name', string="Vendor Name", store=True)
    account_id = fields.Many2one('res.partner', string="Account", required=True)
    amount = fields.Float(string='Amount', compute='_compute_amount', tracking=True)
    narration = fields.Text(string="Narration")
    attachment = fields.Binary(string="Attachment", attachment=True, tracking=True)
    attachment_filename = fields.Char(string="Attachment Filename", tracking=True)
    request_owner_id = fields.Many2one('res.users', string="Request Owner",
                                       check_company=True, domain="[('company_ids', 'in', company_id)]",
                                       default=lambda self: self.env.user, tracking=True)
    department_id = fields.Many2one(
        'hr.department',
        string='Department', states=READONLY_STATES,
        help='Select the department', tracking=True, required=True
    )
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id,
                                 help='The default company for this user.', context={'user_preference': True},
                                 tracking=True, readonly=True)

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('payment', 'Payment Complete'),
            ('rejected', 'Rejected'),
        ],
        string="State",
        default='draft',
        tracking=True,
    )

    approval_level_1 = fields.Many2one('res.users', string='Approver Level 1', domain="[('share', '=', False)]",
                                       readonly=True, tracking=True)

    approval_level_2 = fields.Many2one(
        'res.users',
        string='Approval Level 2',
        domain="[('share', '=', False)]",
        readonly=True,
        tracking=True,
        help='Second level approver'
    )
    approval_level_3 = fields.Many2one(
        'res.users',
        string='Approval Level 3',
        domain="[('share', '=', False)]",
        readonly=True,
        tracking=True,
        help='Third level approver'
    )

    approval1_readonly = fields.Boolean(
        compute='_compute_approval_readonly'
    )
    approval2_readonly = fields.Boolean(
        compute='_compute_approval_readonly'
    )

    partner_balance_amount = fields.Float(string='Partner Balance Amount', compute='_compute_partner_balance_amount',
                                          store=True, states=READONLY_STATES)

    show_approve_button = fields.Boolean(string='Show Approve Button', compute='_compute_show_approve_button',
                                         tracking=True)
    show_reject_button = fields.Boolean(string='Show Reject Button', compute='_compute_show_approve_button',
                                        tracking=True)
    terms = fields.Text(string='Terms & Conditions', tracking=True, states=READONLY_STATES)

    order_line_ids = fields.One2many('freight.charge.advice.line', 'advice_id', string="Order Lines")
    payments_count = fields.Integer(string='Payments Count', compute='_compute_payment_count')

    amount_in_word = fields.Char(compute="_compute_amount_in_word")

    # invoice_id = fields.Many2one('account.move', string='Transport Invoice',
    #                              domain=[('invoice_line_ids.product_id', '=', 'Transport Charges')], readonly=False)
    # invoice_ids = fields.Many2many(
    #     'account.move',
    #     'freight_charge_advice_invoice_rel',
    #     'advice_id',
    #     'invoice_id',
    #     string='Transport Invoices',
    #     domain=[('invoice_line_ids.product_id', '=', 'Transport Charges')],
    #     tracking=True
    # )

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

    @api.depends('department_id')
    def _compute_approval_readonly(self):
        for rec in self:
            rec.approval1_readonly = bool(rec.department_id and rec.department_id.approver1)
            rec.approval2_readonly = bool(rec.department_id and rec.department_id.approver2)

    def _compute_amount_in_word(self):
        for rec in self:
            if rec.amount:
                rec.amount_in_word = self.env.company.currency_id.amount_to_text(rec.amount)
            else:
                rec.amount_in_word = False

    @api.onchange('approval_level_1', 'approval_level_2', 'approval_level_3')
    def _onchange_approval_uniqueness(self):
        ids = [
            self.approval_level_1.id if self.approval_level_1 else 0,
            self.approval_level_2.id if self.approval_level_2 else 0,
            self.approval_level_3.id if self.approval_level_3 else 0,
        ]
        nonzero = [i for i in ids if i]
        if len(nonzero) != len(set(nonzero)):
            raise UserError("The same Approver is selected more than once. Please check and correct it.")

    @api.constrains('approval_level_1', 'approval_level_2', 'approval_level_3')
    def _check_approval_uniqueness(self):
        for rec in self:
            ids = [
                rec.approval_level_1.id if rec.approval_level_1 else 0,
                rec.approval_level_2.id if rec.approval_level_2 else 0,
                rec.approval_level_3.id if rec.approval_level_3 else 0,
            ]
            nonzero = [i for i in ids if i]
            if len(nonzero) != len(set(nonzero)):
                raise UserError("The same Approver is selected more than once. Please check and correct it.")

    def _compute_amount_in_word(self):
        for rec in self:
            if rec.amount:
                rec.amount_in_word = self.env.company.currency_id.amount_to_text(rec.amount)
            else:
                rec.amount_in_word = False

    @api.model
    def create(self, vals):
        # Automatically generate document number if it's not already set
        if vals.get('document_number', _('New')) == _('New'):
            vals['document_number'] = self.env['ir.sequence'].next_by_code('freight.charge.advice') or _('New')
        return super(FreightChargeAdvice, self).create(vals)

    # @api.onchange('approval_level_1')
    # def _onchange_approval_level_1(self):
    #     for record in self:
    #         if record.approval_level_1 == self.env.user:
    #             raise UserError("You cannot assign yourself as an approver.")
    # new code start
    # @api.depends('account_id')
    # def _compute_partner_balance_amount(self):
    #     for record in self:
    #         if record.account_id:
    #             partner = record.account_id
    #             partner_balance_amount = partner.credit - partner.debit
    #             record.partner_balance_amount = partner_balance_amount
    #         else:
    #             record.partner_balance_amount = 0.0
    #
    # @api.onchange('account_id')
    # def _onchange_account_id(self):
    #     if self.account_id:
    #         partner = self.account_id
    #         partner_balance_amount = partner.credit - partner.debit
    #         self.partner_balance_amount = partner_balance_amount
    #     else:
    #         self.partner_balance_amount = 0.0
    #
    #
    #
    #
    #
    #
    # @api.depends('account_id')
    # def _compute_balance(self):
    #     for line in self:
    #         if line.account_id:
    #             balance = line._compute_vendor_balance()
    #             line.balance_amount = balance
    #         else:
    #             line.balance_amount = 0.0
    #
    # def _compute_vendor_balance(self):
    #     invoice_total = self._get_invoice_total()
    #     payment_total = self._get_payment_total()
    #     return invoice_total - payment_total
    #
    # def _get_invoice_total(self):
    #     invoices = self.env['account.move'].search([
    #         ('account_id', '=', self.account_id.id),
    #         ('move_type', 'in', ['in_invoice', 'out_invoice']),
    #         ('state', '=', 'posted'),
    #     ])
    #     return sum(invoice.amount_total_signed for invoice in invoices)
    #
    # def _get_payment_total(self):
    #     payments = self.env['account.payment'].search([
    #         ('account_id', '=', self.account_id.id),
    #         ('payment_type', 'in', ['inbound', 'outbound']),
    #         ('state', '=', 'posted'),
    #     ])
    #     payment_total = 0
    #     for payment in payments:
    #         if payment.payment_type == 'inbound':
    #             payment_total += payment.amount
    #         elif payment.payment_type == 'outbound':
    #             payment_total -= payment.amount
    #     return payment_total
    #
    # @api.onchange('account_id')
    # def _onchange_account_id(self):
    #     self.order_line_ids = [(5, 0, 0)]
    #     if self.account_id:
    #         invoices = self.env['account.payment'].search([
    #             ('account_id', '=', self.account_id.id),
    #             ('move_type', 'in', ['in_invoice', 'out_invoice']),
    #             ('state', '=', 'posted'),
    #             ('payment_state', 'in',['not_paid', 'partial']),
    #         ])
    # purchase_orders = self.env['purchase.order'].search([
    #     ('partner_id', '=', self.partner_id.id),
    #     ('state', 'in', ['purchase', 'done']),
    #     ('invoice_ids', '=', False)
    # ])
    # service_orders = self.env['service.order'].search([
    #     ('partner_id', '=', self.partner_id.id),
    #     ('state', 'in', ['approve']),
    #     ('ask_confirm', '=', False)
    # ])

    # order_lines = []
    # for invoice in invoices:
    #     order_lines.append((0, 0, {
    #         'reference': invoice.name,
    #         'reference_amount': invoice.amount_total_signed,
    #         'date': invoice.invoice_date
    #     }))

    # for po in purchase_orders:
    #     payment_advice_lines.append((0, 0, {
    #         'reference': po.name,
    #         'reference_amount': po.amount_total,
    #         'date': po.date_order
    #     }))
    #
    # for so in service_orders:
    #     payment_advice_lines.append((0, 0, {
    #         'reference': so.name,
    #         'reference_amount': so.total_amount,
    #         'date': so.order_date
    #         }))

    # self.order_line_ids = order_lines
    # new code end

    @api.depends('approval_level_1', 'state')
    def _compute_show_approve_button(self):
        for record in self:
            if record.state == 'submitted' and record.approval_level_1 == self.env.user:
                record.show_approve_button = True
                record.show_reject_button = True
            else:
                record.show_approve_button = False
                record.show_reject_button = False

    def action_submit(self):
        self.write({'state': 'submitted'})
        if not self.approval_level_1:
            raise UserError("Please select an approver before submitting.")

            # Send an activity notification to the approver
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=self.approval_level_1.id,
            note=_("Please review and approve Freight Charge Advice: %s" % self.document_number)
        )

    def action_approve(self):
        if self.approval_level_1 != self.env.user:
            raise UserError("You are not authorized to approve this record.")
        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'freight.charge.advice'),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('user_id', '=', self.approval_level_1.id),
        ], limit=1)
        if activity:
            activity.action_done()
        self.write({'state': 'approved'})
        self.message_post(
            body=_("The Freight Charge Advice has been approved by %s." % self.env.user.name),
            subtype_xmlid="mail.mt_comment",
        )
        # return self.action_register_payment()
        # Create bill and register payment

    def action_reject(self):
        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'freight.charge.advice'),
            ('res_id', '=', self.id),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('user_id', '=', self.approval_level_1.id),
        ], limit=1)
        if activity:
            activity.action_done()
        self.write({'state': 'rejected'})
        self.message_post(
            body=_("The Freight Charge Advice has been rejected by %s." % self.env.user.name),
            subtype_xmlid="mail.mt_comment",
        )

    def open_pdf_viewer(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=freight.charge.advice&id={}&field=attachment'.format(self.id),
            'target': 'new',
        }

    @api.depends('order_line_ids.amount')
    def _compute_amount(self):
        for order in self:
            order.amount = sum(order.order_line_ids.mapped('amount'))

    def button_open_payments(self):
        ''' Redirect the user to the payment records associated with this payment advice.
        :return: An action on account.payment.
        '''
        self.ensure_one()
        payments = self.env['account.payment'].search(
            [('freight_advice_id', '=', self.id), ('state', 'in', ['posted', 'draft'])])

        action = {
            'name': _("Payments"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', payments.ids)],
            'context': {
                'search_default_freight_advice_id': self.id,
                'default_freight_advice_id': self.id,
            },
        }
        return action

    def _compute_payment_count(self):
        for advice in self:
            # self.payments_value = 0
            payments = self.env['account.payment'].search(
                [('freight_advice_id', '=', self.id), ('state', 'in', ['posted', 'draft'])])
            payment_values = self.env['account.payment'].search(
                [('freight_advice_id', '=', self.id), ('state', '=', 'posted')])
            advice.payments_count = len(payments)
            # for record in payment_values:
            #     self.payments_value += record.amount

    def action_register_payment(self):
        return {
            'name': _('Register Payment'),
            'view_mode': 'form',
            'res_model': 'open.payment.freight.register.wizard',
            'view_id': self.env.ref('freight_charge_advice.view_wizard_for_register_freight_charge_advice').id,
            'type': 'ir.actions.act_window',
            'context': {'default_communication': self.document_number,
                        'default_amount': self.amount,
                        'default_partner_id': self.account_id.id,
                        'default_advice_id': self.id,
                        'default_journal_id': self.journal_id.id,
                        'default_partner_bank_id': self.account_id.bank_ids.id,
                        },
            'target': 'new'
        }

        return self.action_open_register_wizard()


class FreightChargeAdviceLine(models.Model):
    _name = "freight.charge.advice.line"
    _description = "Freight Charge Advice Line"

    advice_id = fields.Many2one('freight.charge.advice', string="Freight Charge Advice", ondelete="cascade")
    account_id = fields.Many2one('res.partner', string="Account")
    vendor_name = fields.Char(related='account_id.name', string="Vendor Name", store=True)
    amount = fields.Float(string="Amount")
    product_id = fields.Many2one('product.product', string="product", readonly=True)
    # invoice_id = fields.Many2one('account.move', string="Invoice", related='advice_id.invoice_id', store=True)
    remarks = fields.Text(string="Remarks")
    invoice_ids = fields.Many2many(
        'account.move',
        'freight_charge_advice_invoice_rel',
        'advice_id',
        'invoice_id',
        string='Transport Invoices',
        domain=[('invoice_line_ids.product_id', '=', 'Transport Charges')],
        tracking=True
    )


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    freight_advice_id = fields.Many2one('freight.charge.advice')

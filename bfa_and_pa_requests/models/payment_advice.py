from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class PaymentAdvice(models.Model):
    _name = 'payment.advice'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Payment advice module'

    def _get_default_category_id(self):
        domain = [('name', '=', "Payment Advice")]
        category_type = self.env['approval.category'].search(domain, limit=1)
        if category_type:
            return category_type.id
        return False

    @api.model
    def _get_default_user_id(self):
        # Define the domain to fetch the user
        domain = [('name', '=', "Anilkumar Accounts HO"), ('login', '=', 'anilkumar@pragatigroup.com')]
        user_type = self.env['res.users'].search(domain, limit=1)
        if user_type:
            return user_type.id
        else:
            return self.env.user.id

    @api.model
    def _get_default_user_id_1(self):
        # Define the domain to fetch the user
        domain = [('name', '=', "Managing Director"), ('login', '=', 'ajay@pragatigroup.com')]
        user_type = self.env['res.users'].search(domain, limit=1)
        if user_type:
            return user_type.id
        else:
            return self.env.user.id

    READONLY_STATES = {
        'payment': [('readonly', True)],
    }

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, tracking=True,
                       default=lambda self: _('New'), states=READONLY_STATES)
    partner_id = fields.Many2one("res.partner", string="Vendor", required=True, tracking=True, states=READONLY_STATES)
    vendor_refernce = fields.Char(string="Vendor Reference", tracking=True, states=READONLY_STATES)
    order_date = fields.Date(string="Date", tracking=True, states=READONLY_STATES, required=True)
    narration = fields.Char(string="Narration", tracking=True, states=READONLY_STATES)
    payment_approval_id = fields.Many2one("approval.request", string="Payment Advice Approval Id", tracking=True,
                                          readonly=True)
    payment_approval_status = fields.Selection([('pending', 'Pending'), ('approve', 'Approved')],
                                               string='Approval Status', default='pending', tracking=True)
    request_owner_id = fields.Many2one('res.users', string="Request Owner",
                                       check_company=True, domain="[('company_ids', 'in', company_id)]",
                                       default=lambda self: self.env.user, tracking=True)
    category_id = fields.Many2one('approval.category', string='category', default=_get_default_category_id,
                                  tracking=True)

    # code for preview
    original_bills = fields.Binary(string="Original Bill", attachment=True, tracking=True)
    original_bills_filename = fields.Char(string="Original Bill Filename", tracking=True)

    state = fields.Selection([("draft", "Draft"), ("waiting1", "Waiting Level1"), ("waiting2", "Waiting Level2"),
                              ("waiting3", "Waiting Level3"), ("approve", "Approved"), ('reject', 'Approval Rejected'),
                              ('payment', 'Payment Complete'), ("cancel", "Cancel")], default="draft", store=True,
                             tracking=True)

    payment_advice_line_ids = fields.One2many("payment.advice.line", "advice_id", string="Payment Advice lines",
                                              tracking=True, states=READONLY_STATES, required=True)
    amount_in_words = fields.Char(string='Amount in Words', compute='_compute_amount_in_words', store=True,
                                  tracking=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id, tracking=True, readonly="1")
    approver_2 = fields.Char(string='Approver 2', store=True, tracking=True)
    approver_1 = fields.Char(string='Approver 1', store=True, tracking=True)
    approver_3 = fields.Char(string='Approver 3', store=True, tracking=True)
    reuse_button = fields.Boolean(default=False, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id,
                                 help='The default company for this user.', context={'user_preference': True},
                                 readonly="1")
    location_id = fields.Many2one('stock.location', "Cost Center", tracking=True, states=READONLY_STATES,
                                  domain=[('is_cost_center', '=', True)])
    department_id = fields.Many2one('hr.department', 'Department', tracking=True, states=READONLY_STATES)
    shipping_address_id = fields.Many2one('res.partner', string='Shipping Address', tracking=True,
                                          states=READONLY_STATES)
    terms = fields.Text(string='Terms & Conditions', tracking=True, states=READONLY_STATES)
    user_id = fields.Many2one('res.users', string='Responsible user',
                              default=lambda self: self.env.user)

    rec_amount = fields.Float(string='Advanced Amount', compute='_compute_rec_amount', tracking=True)
    reference_amount = fields.Float('Total Project Cost')
    approve_amount = fields.Float(string='Approved Amount', compute='_compute_approve_amount', tracking=True)
    balance_amount = fields.Float(string='Balance Amount', tracking=True)
    partner_balance_amount = fields.Float(string='Partner Balance Amount', compute='_compute_partner_balance_amount',
                                          store=True, states=READONLY_STATES)
    payment_id = fields.Many2one('account.payment', string='Payment Id')
    approval_level_1 = fields.Many2one('res.users', string='Approver Level 1', domain="[('share', '=', False)]",
                                       states=READONLY_STATES, tracking=True)
    approval_level_2 = fields.Many2one('res.users', string='Approver Level 2', domain="[('share', '=', False)]",
                                       states=READONLY_STATES, tracking=True)
    approval_level_3 = fields.Many2one('res.users', string='Approver Level 3', domain="[('share', '=', False)]",
                                       states=READONLY_STATES)
    payments_count = fields.Integer(string='Payments Count', compute='_compute_payment_count')
    payments_value = fields.Float(string='Payments Value', states=READONLY_STATES)
    journal_id = fields.Many2one('account.journal', string='Journal Id', domain=[('type', '=', 'bank')],
                                 states=READONLY_STATES)
    location_id = fields.Many2one('stock.location', "Cost Center", tracking=True, states=READONLY_STATES,
                                  domain=[('is_cost_center', '=', True)])
    department_id = fields.Many2one('hr.department', 'Department', tracking=True, states=READONLY_STATES)
    show_approve_button = fields.Boolean(string='Show Approve Button', compute='_compute_show_approve_button',
                                         tracking=True)
    show_reject_button = fields.Boolean(string='Show Reject Button', compute='_compute_show_approve_button',
                                        tracking=True)
    amount_due = fields.Float(string="Amount Due")
    advice_id = fields.Many2one('payment.advice', string='Advice Id')

    # @api.onchange('department_id')
    # def _onchange_department_id(self):
    #
    #     if self.department_id:
    #         self.approval_level_1 = self.department_id.approver1.id
    #         self.approval_level_2 = self.department_id.approver2.id
    #     else:
    #         self.approval_level_1 = False
    #         self.approval_level_2 = False

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

    # code for partner balance
    @api.depends('partner_id')
    def _compute_partner_balance_amount(self):
        for record in self:
            if record.partner_id:
                partner = record.partner_id
                partner_balance_amount = partner.credit - partner.debit
                record.partner_balance_amount = partner_balance_amount
            else:
                record.partner_balance_amount = 0.0

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            partner = self.partner_id
            partner_balance_amount = partner.credit - partner.debit
            self.partner_balance_amount = partner_balance_amount
        else:
            self.partner_balance_amount = 0.0

    # @api.depends('reference_amount', 'approve_amount')
    # def _compute_balance_amount(self):
    #     for record in self:
    #         record.balance_amount = record.reference_amount - record.approve_amount

    @api.depends('partner_id')
    def _compute_balance(self):
        for line in self:
            if line.partner_id:
                balance = line._compute_vendor_balance()
                line.balance_amount = balance
            else:
                line.balance_amount = 0.0

    def _compute_vendor_balance(self):
        invoice_total = self._get_invoice_total()
        payment_total = self._get_payment_total()
        return invoice_total - payment_total

    def _get_invoice_total(self):
        invoices = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', 'in', ['in_invoice', 'out_invoice']),
            ('state', '=', 'posted'),
        ])
        return sum(invoice.amount_total_signed for invoice in invoices)

    def _get_payment_total(self):
        payments = self.env['account.payment'].search([
            ('partner_id', '=', self.partner_id.id),
            ('payment_type', 'in', ['inbound', 'outbound']),
            ('state', '=', 'posted'),
        ])
        payment_total = 0
        for payment in payments:
            if payment.payment_type == 'inbound':
                payment_total += payment.amount
            elif payment.payment_type == 'outbound':
                payment_total -= payment.amount
        return payment_total

    # @api.onchange('partner_id')
    # def _onchange_partner_id(self):
    #     self.payment_advice_line_ids = [(5, 0, 0)]
    #     if not self.partner_id:
    #         self.partner_balance_amount = 0.0
    #         return
    #
    #     self.partner_balance_amount = self.partner_id.credit - self.partner_id.debit
    #
    #     # ✅ Get one rec_amount per reference — from latest approved/payment advice
    #     past_lines = self.env['payment.advice.line'].search([
    #         ('advice_id.partner_id', '=', self.partner_id.id),
    #         ('advice_id.state', 'in', ['approve', 'payment']),
    #     ], order='id desc')
    #
    #     reference_data = {}
    #     so_advance_map = {}
    #     approve_data = {}
    #     for line in past_lines:
    #         ref = line.reference
    #         amt = line.rec_amount or 0.0
    #         approved = line.approve_amount or 0.0
    #
    #         if ref not in reference_data:
    #             reference_data[ref] = amt + approved
    #         else:
    #             reference_data[ref] += approved
    #
    #         if ref.startswith('SO/'):
    #             so_advance_map[ref] = so_advance_map.get(ref, 0.0) + (amt + approved)
    #
    #     lines = []
    #
    #     def add_line(ref, total_cost, date, bill_ref=""):
    #         past_advance = reference_data.get(ref, 0.0)
    #         balance = total_cost - past_advance
    #
    #         if balance <= 0:
    #             return
    #
    #         lines.append((0, 0, {
    #             'reference': ref,
    #             'reference_amount': total_cost,
    #             'number': bill_ref,
    #             'rec_amount': past_advance,
    #             'balance_amount': balance,
    #             'date': date,
    #         }))
    #
    #     # ✅ SERVICE ORDERS (show until completion)
    #     completed_so_names = self.env['service.completion'].search([]).mapped('service_order_id.name')
    #     service_orders = self.env['service.order'].search([
    #         ('partner_id', '=', self.partner_id.id),
    #         ('state', '=', 'approve'),
    #     ])
    #     for so in service_orders:
    #         if so.name not in completed_so_names:
    #             add_line(so.name, so.total_amount, so.order_date)
    #
    #     # ✅ INVOICES (showing correct rec_amount via invoice_origin)
    #     invoices = self.env['account.move'].search([
    #         ('partner_id', '=', self.partner_id.id),
    #         ('move_type', 'in', ['in_invoice', 'out_invoice']),
    #         ('state', '=', 'posted'),
    #     ])
    #
    #     for inv in invoices:
    #         origin = inv.invoice_origin  # e.g., SO/00092
    #         ref_name = inv.name
    #         total = abs(inv.amount_total_signed)
    #         date = inv.invoice_date
    #         bill_ref = inv.ref or ""
    #
    #         advance = 0.0
    #         if origin:
    #             advance = so_advance_map.get(origin, 0.0)
    #             if not advance:
    #                 service_order = self.env['service.order'].search([('name', '=', origin)], limit=1)
    #                 if service_order:
    #                     advance = reference_data.get(service_order.name, 0.0)
    #
    #         if ref_name in reference_data:
    #             advance += reference_data[ref_name]
    #
    #         balance = total - advance
    #         if balance <= 0:
    #             continue
    #
    #         lines.append((0, 0, {
    #             'reference': ref_name,
    #             'reference_amount': total,
    #             'number': bill_ref,
    #             'rec_amount': advance,
    #             'balance_amount': balance,
    #             'date': date,
    #         }))
    #
    #     self.payment_advice_line_ids = lines


    @api.model_create_multi
    def create(self, values_list):
        records = super(PaymentAdvice, self).create(values_list)

        for record in records:
            if record.name == _('New'):
                fiscal_years = self.env['account.fiscal.year'].search([])
                current_date = fields.Date.context_today(self)

                sequence = self.env['ir.sequence'].next_by_code('payment.advice') or _('New')

                if fiscal_years:
                    for fiscal_year in fiscal_years:
                        start_date = fiscal_year.date_from
                        end_date = fiscal_year.date_to
                        if start_date <= current_date <= end_date:
                            sequence_number = sequence.split('/')[2] if sequence.startswith("PAD/") else \
                                sequence.split('/')[0]
                            year_range = "{}-{}".format(start_date.strftime('%y'), end_date.strftime('%y'))
                            record.name = "PAD/{}/{}".format(year_range, sequence_number.zfill(4))
                            break
                    else:
                        # No fiscal year found for the current date, default to current year and month
                        sequence_number = sequence.split('/')[2] if sequence.startswith("PAD/") else \
                            sequence.split('/')[0]
                        current_year_month = current_date.strftime('%m/%Y')
                        record.name = "PAD/{}/{}".format(current_year_month, sequence_number.zfill(4))
                else:
                    # No fiscal years available, default to current year and month
                    sequence_number = sequence.split('/')[2] if sequence.startswith("PAD/") else sequence.split('/')[0]
                    current_year_month = current_date.strftime('%m/%Y')
                    record.name = "PAD/{}/{}".format(current_year_month, sequence_number.zfill(4))

        return records

    def order_cancel(self):
        self.state = 'cancel'

    def order_draft(self):
        self.state = 'draft'

    # @api.depends('payment_approval_id.approver_ids.status', 'payment_approval_id.approver_ids')
    # def _compute_approvers_names(self):
    #     for record in self:
    #         approver_1_name = False
    #         approver_2_name = False
    #         for approver in record.payment_approval_id.approver_ids:
    #             if approver.status == 'approved':
    #                 if not approver_1_name:
    #                     approver_1_name = approver.user_id.name
    #                 else:
    #                     approver_2_name = approver.user_id.name
    #         record.approver_1 = approver_1_name
    #         record.approver_2 = approver_2_name

    # @api.depends('payment_approval_id.request_status')
    # def _compute_approve_status(self):
    #     for record in self:
    #         if record.payment_approval_id and record.payment_approval_id.request_status == 'approved' and record.state == 'draft':
    #             record.payment_approval_status = 'approve'
    #             record.write({'state':'approve'})
    #         else:
    #             record.payment_approval_status = 'pending'

    def action_for_payment_advice_submit(self):
        approver_list = []

        if self.approval_level_1:
            approver_list.append(self.approval_level_1.id)
        if self.approval_level_2:
            approver_list.append(self.approval_level_2.id)
        if self.approval_level_3:
            approver_list.append(self.approval_level_3.id)

        for record in self:

            if not record.payment_advice_line_ids:
                raise UserError(_("Please enter some lines below..."))

            # if not record.request_owner_id or not record.category_id:
            #     raise UserError("Please fill in the required fields: Purchase No, Request Owner, and Category")
            # if record.reuse_button and record.payment_approval_id:
            #     raise ValidationError(_("The record is already Submitted, Please check the Payment Advice Approval Id"))

            # Create an approval request
            # approval_request = record.env['approval.request'].create({
            #     'request_owner_id': record.request_owner_id.id,
            #     'category_id': record.category_id.id,
            #     'payment_advice_sep_id': record.id,
            # })

            # Update the payment_approval_id with the latest approval request ID
            # record.write({'payment_approval_id': approval_request.id})
            # approver_values = []

            # for line in approver_list:
            #     approver_values.append((0, 0, {
            #         'user_id': line,
            #         'required': True,
            #     }))
            # # Link approval request to the approval approvers
            # approval_request.write({
            #     'approver_ids': approver_values,
            # })

            # if record.payment_approval_id:
            #     record.payment_approval_id.action_confirm()
            # if record.payment_approval_id:
            #     record.reuse_button = True
            self.sudo()._get_user_approval_activities(user=self.env.user)
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            if approver_list:
                record._create_mail_activity_to_approval(approver_list[0])
                record.state = 'waiting1'

        return True

    # ..............Amount in words..........
    @api.depends('approve_amount', 'currency_id')
    def _compute_amount_in_words(self):
        for order in self:
            if order.approve_amount:
                amount_words = order.currency_id.amount_to_text(order.approve_amount)
                order.amount_in_words = amount_words.title()  # Capitalize the first letter
            else:
                order.amount_in_words = ""

    @api.depends('payment_advice_line_ids.rec_amount')
    def _compute_rec_amount(self):
        for order in self:
            order.rec_amount = sum(order.payment_advice_line_ids.mapped('rec_amount'))

    @api.depends('payment_advice_line_ids.approve_amount')
    def _compute_approve_amount(self):
        for order in self:
            order.approve_amount = sum(order.payment_advice_line_ids.mapped('approve_amount'))

    # code for preview

    def open_pdf_viewer(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=payment.advice&id={}&field=original_bills'.format(self.id),
            'target': 'new',

        }

    # action for Register payment button
    # def action_register_payments(self):
    #     self.state = 'payment'
    #     return {
    #         'name': _('Register Payment'),
    #         'res_model': 'account.payment.register',
    #         'view_mode': 'form',
    #         'context': {
    #             'default_advice_id': self.id,
    #             'active_model': 'account.move',
    #             'active_ids': self.ids,
    #         },
    #         'target': 'new',
    #         'type': 'ir.actions.act_window',
    #     }

    # Payment button
    def button_open_payments(self):
        ''' Redirect the user to the payment records associated with this payment advice.
        :return: An action on account.payment.
        '''
        self.ensure_one()
        payments = self.env['account.payment'].search(
            [('advice_id', '=', self.id), ('state', 'in', ['posted', 'draft'])])

        action = {
            'name': _("Payments"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', payments.ids)],
            'context': {
                'search_default_advice_id': self.id,
                'default_advice_id': self.id,
            },
        }
        return action

    def _compute_payment_count(self):
        for advice in self:
            self.payments_value = 0
            payments = self.env['account.payment'].search(
                [('advice_id', '=', self.id), ('state', 'in', ['posted', 'draft'])])
            payment_values = self.env['account.payment'].search([('advice_id', '=', self.id), ('state', '=', 'posted')])
            advice.payments_count = len(payments)
            for record in payment_values:
                self.payments_value += record.amount

    def action_register_payment(self):
        return {
            'name': _('Register Payment'),
            'view_mode': 'form',
            'res_model': 'open.payment.register.wizard',
            'view_id': self.env.ref('bfa_and_pa_requests.view_wizard_for_register_payment_advice').id,
            'type': 'ir.actions.act_window',
            'context': {'default_communication': self.name,
                        'default_amount': self.approve_amount - self.payments_value,
                        'default_partner_id': self.partner_id.id,
                        'default_advice_id': self.id,
                        'default_journal_id': self.journal_id.id,
                        'default_partner_bank_id': self.partner_id.bank_ids.id,
                        },
            'target': 'new'
        }
        return self.action_open_register_wizard()

    def action_reject(self):
        for record in self:
            record.state = 'reject'
            # record._create_mail_activity_for_reject()
            record.sudo()._get_user_approval_activities(user=self.env.user).action_done()
        return True

    def action_advice(self):
        for record in self:
            if record.state == 'waiting1':
                # Logic for approval by level 1 approver
                if record.approval_level_2:
                    record.state = 'waiting2'
                    record._create_mail_activity_to_approval(self.approval_level_2.id)  # Move to the next state
                else:
                    record.state = 'approve'
            elif record.state == 'waiting2':
                # Logic for approval by level 2 approver
                if record.approval_level_3:
                    record.state = 'waiting3'
                    record._create_mail_activity_to_approval(self.approval_level_3.id)
                else:
                    record.state = 'approve'
            elif record.state == 'waiting3':
                # Logic for approval by level 3 approver
                record.state = 'approve'  # Move to the final approval state
            else:
                raise UserError("This record cannot be approved.")

            if record.state == 'approve':
                for line in record.payment_advice_line_ids:
                    paid = line.rec_amount or 0.0
                    approve = line.approve_amount or 0.0
                    ref_amt = line.reference_amount or 0.0

                    new_rec = paid + approve
                    line.rec_amount = new_rec
                    line.balance_amount = max(0.0, ref_amt - new_rec)

        self.sudo()._get_user_approval_activities(user=self.env.user).action_done()
        return True

    @api.depends('state', 'approval_level_1', 'approval_level_2', 'approval_level_3')
    def _compute_show_approve_button(self):
        for record in self:
            if record.state == 'waiting1' and record.approval_level_1 == self.env.user:
                record.show_approve_button = True
                record.approver_1 = self.env.user.name
                record.show_reject_button = True
            elif record.state == 'waiting2' and record.approval_level_2 == self.env.user:
                record.show_approve_button = True
                record.approver_2 = self.env.user.name
                record.show_reject_button = True
            elif record.state == 'waiting3' and record.approval_level_3 == self.env.user:
                record.show_approve_button = True
                record.approver_3 = self.env.user.name
                record.show_reject_button = True
            else:
                record.show_approve_button = False
                record.show_reject_button = False

    def _create_mail_activity_to_approval(self, approver):
        # Create an activity for the specified approver
        if approver:
            activity = self.env['mail.activity'].sudo().create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'date_deadline': fields.Date.today(),
                'user_id': approver,
                'res_model_id': self.env.ref('bfa_and_pa_requests.model_payment_advice').id,
                'res_id': self.id,
                'summary': 'Payment Advice: %s' % self.name,
                'note': 'Payment Advice: %s' % self.name,
                'display_name': 'Payment Advice',
            })
            return activity
        return False

    def _get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'payment.advice'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        print("############", activities)
        return activities

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.payment_advice_line_ids = [(5, 0, 0)]

        if not self.partner_id:
            self.partner_balance_amount = 0.0
            return

        # Partner balance
        self.partner_balance_amount = self.partner_id.credit - self.partner_id.debit

        # ------------------------------
        # 1️⃣ Collect previously approved amounts
        # ------------------------------
        past_lines = self.env['payment.advice.line'].search([
            ('advice_id.partner_id', '=', self.partner_id.id),
            ('advice_id.state', 'in', ['approve', 'payment']),
        ])

        ref_data = {}
        for pl in past_lines:
            ref = pl.reference
            amt = pl.approve_amount or 0.0
            if ref:
                ref_data[ref] = ref_data.get(ref, 0.0) + amt

        lines = []

        # Utility function to add missing entries
        def add_line(ref, total, date, model_balance=None, bill_ref=""):
            # Paid via accounting (already in Odoo invoice residual)
            paid_from_residual = 0.0
            if model_balance is not None:
                paid_from_residual = total - model_balance

            # Paid via previous payment advice
            paid_from_advice = ref_data.get(ref, 0.0)

            # Combine both paid amounts
            combined_paid = paid_from_residual + paid_from_advice
            balance = max(total - combined_paid, 0.0)

            # Skip fully paid items
            if balance <= 0:
                return

            lines.append((0, 0, {
                'reference': ref,
                'reference_amount': total,
                'rec_amount': combined_paid,
                'balance_amount': balance,
                'approve_amount': 0.0,
                'number': bill_ref,
                'date': date,
            }))

        # ------------------------------
        # 2️⃣ SERVICE ORDERS
        # ------------------------------
        completed_so_names = self.env['service.completion'].search([]).mapped('service_order_id.name')

        service_orders = self.env['service.order'].search([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'approve')
        ])

        for so in service_orders:
            if so.name not in completed_so_names:
                add_line(
                    so.name,
                    so.total_amount,
                    so.order_date
                )

        # ------------------------------
        # 3️⃣ BILL APPROVAL (BFA)
        # ------------------------------
        bfas = self.env['bills.approval'].search([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'approve'),
        ])

        for bill in bfas:
            add_line(
                bill.name,
                bill.total_amount,
                bill.date or bill.create_date,
                bill_ref=bill.bill_reference if hasattr(bill, 'bill_reference') else ""
            )

        # ------------------------------
        # 4️⃣ PURCHASE ORDERS (ONLY IF INVOICE NOT CREATED)
        # ------------------------------
        purchase_orders = self.env['purchase.order'].search([
            ('partner_id', '=', self.partner_id.id),
            ('state', 'in', ['purchase', 'done'])
        ])

        for po in purchase_orders:
            # skip PO if invoice exists
            if po.invoice_ids.filtered(lambda inv: inv.state != 'cancel'):
                continue

            add_line(
                po.name,
                po.amount_total,
                po.date_order
            )

        # ------------------------------
        # 5️⃣ INVOICES (IN/OUT)
        # ------------------------------
        invoices = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', 'in', ['in_invoice', 'out_invoice']),
            ('state', '=', 'posted'),
        ])

        for inv in invoices:
            total = abs(inv.amount_total_signed)
            add_line(
                inv.name,
                total,
                inv.invoice_date,
                model_balance=inv.amount_residual,  # RESIDUAL gives balance
                bill_ref=inv.ref or ""
            )

        # Final assignment
        self.payment_advice_line_ids = lines


class PaymentAdviceLine(models.Model):
    _name = 'payment.advice.line'
    _description = 'Payment advice lines'

    advice_id = fields.Many2one('payment.advice', string='Advice Id')
    reference = fields.Char(string='Bill Reference')
    number = fields.Char(string='Bill Number')
    reference_amount = fields.Float('Total Project Cost')
    date = fields.Datetime(string='Reference Date')
    rec_amount = fields.Float('Advanced Amount')
    approve_amount = fields.Float(string='Approved Amount')
    balance_amount = fields.Float(string='Balance Amount', compute='_compute_balance_amount', store=True)
    remarks = fields.Char(string='Remarks')
    amount_due = fields.Float(string='Amount Due')
    payment_advice_id = fields.Many2one('payment.advice', string='Payment Advice')
    service_order_id = fields.Many2one('service.order', string='Service Order')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)

    @api.depends('reference_amount', 'rec_amount', 'approve_amount')
    def _compute_balance_amount(self):
        for line in self:
            total = line.reference_amount or 0.0
            past = line.rec_amount or 0.0
            approve = line.approve_amount or 0.0
            line.balance_amount = max(0.0, total - (past + approve))

    # @api.onchange('approve_amount')
    # def _onchange_approve_amount(self):
    #     for line in self:
    #         approve = line.approve_amount or 0.0
    #         ref_amt = line.reference_amount or 0.0
    #         paid = line.rec_amount or 0.0
    #
    #         # New rec + balance
    #         new_rec = paid + approve
    #         line.rec_amount = new_rec
    #         line.balance_amount = max(0.0, ref_amt - new_rec)

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from num2words import num2words


class ServiceCompletion(models.Model):
    _name = 'service.completion'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Service Completion Module'

    def _get_default_category_id(self):
        domain = [('name', '=', "Service Completion")]
        category_type = self.env['approval.category'].search(domain, limit=1)
        if category_type:
            return category_type.id
        return False

    def _get_default_journal_id(self):
        domain = [('name', 'ilike', "Service Expenses")]
        journal = self.env['account.journal'].search(domain, limit=1)
        if journal:
            return journal.id
        return False

    READONLYSTATES = {
        'complete': [('readonly', True)]
    }

    # name = fields.Char(string='Service Completion Number', required=True)
    service_order_id = fields.Many2one('service.order', string='Service Order')

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, tracking=True,
                       default=lambda self: _('New'), states=READONLYSTATES)

    partner_id = fields.Many2one("res.partner", string="Vendor", tracking=True, states=READONLYSTATES)
    vendor_refernce = fields.Char(string="Vendor Reference", tracking=True, states=READONLYSTATES)
    complete_date = fields.Date(string="Service Completion Date", tracking=True, states=READONLYSTATES,
                                default=fields.Datetime.now())
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id, tracking=True, readonly=True)
    transport = fields.Char(string="Transportation", tracking=True, states=READONLYSTATES)
    bill_reference = fields.Char(string="Bill Reference", tracking=True, states=READONLYSTATES)
    payment_terms_id = fields.Many2one("account.payment.term", string="Payment Terms", tracking=True,
                                       states=READONLYSTATES)
    service_narration = fields.Char(string="Service Narration", tracking=True, states=READONLYSTATES)
    # service_link=fields.Many2many("approval.request",string="Service Link")
    service_order_approval_id = fields.Many2one("approval.request", string="Service Order Approval Id", tracking=True,
                                                readonly=True)
    service_approval_status = fields.Selection([('pending', 'Pending'), ('approve', 'Approved')],
                                               string='Approval Status', default='pending', tracking=True)
    request_owner_id = fields.Many2one('res.users', string="Request Owner",
                                       check_company=True, domain="[('company_ids', 'in', company_id)]",
                                       default=lambda self: self.env.user, tracking=True, readonly=True)
    category_id = fields.Many2one('approval.category', string='category', default=_get_default_category_id,
                                  tracking=True)
    original_bills = fields.Binary(string="Original Bill", attachment=True, tracking=True)
    expect_arrival = fields.Datetime(string="Expected Completion", tracking=True)
    ask_confirm = fields.Boolean(string="Ask Confirmation", tracking=True, states=READONLYSTATES)
    state = fields.Selection([("draft", "Draft"), ("waiting1", "Waiting Level1"), ("waiting2", "Waiting Level2"),
                              ("waiting3", "Waiting Level3"), ("approve", "Approved"), ('reject', 'Approval Rejected'),
                              ("complete", "Completed"), ("cancel", "Cancel")], default="draft", tracking=True)
    total_amount = fields.Monetary(string='Total Amount', compute="_compute_total_amount", store=True, tracking=True)
    amount_in_words = fields.Char(string='Amount in Words', compute='_compute_amount_in_words', store=True,
                                  tracking=True)
    service_completion_line_ids = fields.One2many("service.completion.line", "service_id",
                                                  string="Service Completion Lines", states=READONLYSTATES)
    approver_1 = fields.Char(string='Approver 1', store=True, tracking=True)
    approver_2 = fields.Char(string='Approver 2', store=True, tracking=True)
    approver_3 = fields.Char(string='Approver 3', store=True, tracking=True)
    reuse_button = fields.Boolean(default=False, tracking=True, states=READONLYSTATES)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id,
                                 help='The default company for this user.', context={'user_preference': True})
    service_order_id = fields.Many2one('service.order', string='Service Order Id', states=READONLYSTATES)
    location_id = fields.Many2one('stock.location', "Cost Center", tracking=True, states=READONLYSTATES,
                                  domain=[('is_cost_center', '=', True)])
    department_id = fields.Many2one('hr.department', 'Department', tracking=True, states=READONLYSTATES)
    journal_id = fields.Many2one('account.journal', string='Journal type', default=_get_default_journal_id,
                                 readonly=True, tracking=True)
    account_move_id = fields.Many2one('account.move', string='Invoice', readonly=True, copy=False,
                                      help="Link to the associated invoice when created.", tracking=True)
    igst_tax = fields.Float(string='IGST', compute='_compute_igst_amount', store=True, tracking=True)
    cgst_tax = fields.Float(string='CGST', compute='_compute_cgst_amount', store=True, tracking=True)
    sgst_tax = fields.Float(string='SGST', compute='_compute_sgst_amount', store=True, tracking=True)
    discount_total = fields.Float(string='Discount', compute='_compute_discount_total', store=True, digits=(16, 3),
                                  tracking=True)
    total_wo_tax = fields.Float(string='Untaxed Amount', compute='_compute_total_wo_tax', store=True, digits=(16, 3),
                                tracking=True)
    shipping_address_id = fields.Many2one('res.partner', string='Shipping Address', tracking=True,
                                          states=READONLYSTATES)
    terms = fields.Text(string='Terms & Conditions', tracking=True, states=READONLYSTATES)
    service_orders = fields.Integer(string='Service Order', compute='_compute_service_order')
    approval_level_1 = fields.Many2one(
        'res.users',
        string='Approver Level 1',
        domain="[('share', '=', False)]"
    )
    approval_level_2 = fields.Many2one(
        'res.users',
        string='Approver Level 2',
        domain="[('share', '=', False)]"
    )
    approval_level_3 = fields.Many2one('res.users', string='Approver Level 3', domain="[('share', '=', False)]",
                                       states=READONLYSTATES)
    show_approve_button = fields.Boolean(string='Show Approve Button', compute='_compute_show_approve_button',
                                         tracking=True)
    show_reject_button = fields.Boolean(string='Show Reject Button', compute='_compute_show_approve_button',
                                        tracking=True)

    # def action_reset_to_draft(self):
    #     for record in self:
    #         record.write({'state': 'draft'})
    #     return True

    @api.onchange('department_id')
    def _onchange_department_id(self):

        if self.department_id:
            self.approval_level_1 = self.department_id.approver1.id
            self.approval_level_2 = self.department_id.approver2.id
        else:
            self.approval_level_1 = False
            self.approval_level_2 = False

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

    def _compute_service_order(self):
        for rec in self:
            orders = self.env['service.order'].search_count(
                [('ask_confirm', '!=', True), ('state', '=', 'approve'), ('partner_id', '=', self.partner_id.id)])
            rec.service_orders = orders

    # Compute Total in the form based on service_completion_line_ids
    @api.depends('service_completion_line_ids.price_subtotal')
    def _compute_total_wo_tax(self):
        for order in self:
            order.total_wo_tax = sum(order.service_completion_line_ids.mapped('price_subtotal'))

    # Compute Total in the form based on service_completion_line_ids
    @api.depends('service_completion_line_ids.igst_tax')
    def _compute_igst_amount(self):
        for order in self:
            order.igst_tax = sum(order.service_completion_line_ids.mapped('igst_tax'))
        # Compute Total in the form based on service_completion_line_ids

    @api.depends('service_completion_line_ids.cgst_tax')
    def _compute_cgst_amount(self):
        for order in self:
            order.cgst_tax = sum(order.service_completion_line_ids.mapped('cgst_tax'))
        # Compute Total in the form based on service_completion_line_ids

    @api.depends('service_completion_line_ids.sgst_tax')
    def _compute_sgst_amount(self):
        for order in self:
            order.sgst_tax = sum(order.service_completion_line_ids.mapped('sgst_tax'))

    @api.depends('service_completion_line_ids.discounted_amount')
    def _compute_discount_total(self):
        for order in self:
            order.discount_total = sum(order.service_completion_line_ids.mapped('discounted_amount'))

    @api.onchange('service_order_id')
    def _onchange_service_order_id(self):
        if self.service_order_id:
            self.vendor_refernce = self.service_order_id.vendor_refernce
            self.partner_id = self.service_order_id.partner_id.id
            self.location_id = self.service_order_id.location_id.id
            self.department_id = self.service_order_id.department_id.id
            self.payment_terms_id = self.service_order_id.payment_terms_id.id
            self.transport = self.service_order_id.transport
            self.service_narration = self.service_order_id.service_narration
            self.expect_arrival = self.service_order_id.expect_arrival
            self.terms = self.service_order_id.terms
            self.original_bills = self.service_order_id.original_bills
            self.shipping_address_id = self.service_order_id.shipping_address_id.id
            self.service_completion_line_ids = [(5, 0, 0)]  # Clear existing lines
            lines = []
            for line in self.service_order_id.service_line_ids:
                vals = {
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'taxes_id': line.taxes_id,
                    'price_unit': line.price_unit,
                    'product_uom_id': line.product_uom_id.id,
                    'discount_type': line.discount_type,
                    'discount_amount': line.discount_amount,
                }
                lines.append((0, 0, vals))
            self.service_completion_line_ids = lines

    @api.model_create_multi
    def create(self, values_list):
        records = super(ServiceCompletion, self).create(values_list)

        for record in records:
            if record.name == _('New'):
                fiscal_years = self.env['account.fiscal.year'].search([])
                current_date = fields.Date.context_today(self)

                sequence = self.env['ir.sequence'].next_by_code('service.completion') or _('New')

                if fiscal_years:
                    for fiscal_year in fiscal_years:
                        start_date = fiscal_year.date_from
                        end_date = fiscal_year.date_to
                        if start_date <= current_date <= end_date:
                            sequence_number = sequence.split('/')[-1]
                            year_range = "{}-{}".format(start_date.strftime('%y'), end_date.strftime('%y'))
                            record.name = "SCO/{}/{}".format(year_range, sequence_number.zfill(4))
                            break
                    else:
                        # No fiscal year found for the current date, default to current year and month
                        sequence_number = sequence.split('/')[-1]
                        current_year_month = current_date.strftime('%m/%Y')
                        record.name = "SCO/{}/{}".format(current_year_month, sequence_number.zfill(4))
                else:
                    # No fiscal years available, default to current year and month
                    sequence_number = sequence.split('/')[-1]
                    current_year_month = current_date.strftime('%m/%Y')
                    record.name = "SCO/{}/{}".format(current_year_month, sequence_number.zfill(4))

        return records

    # @api.depends('service_order_approval_id.approver_ids.status', 'service_order_approval_id.approver_ids')
    # def _compute_approvers_names(self):
    #     for record in self:
    #         approver_1_name = False
    #         approver_2_name = False
    #         for approver in record.service_order_approval_id.approver_ids:
    #             if approver.status == 'approved':
    #                 if not approver_1_name:
    #                     approver_1_name = approver.user_id.name
    #                 else:
    #                     approver_2_name = approver.user_id.name
    #         record.approver_1 = approver_1_name
    #         record.approver_2 = approver_2_name

    # @api.depends('service_order_approval_id.request_status')
    # def _compute_approve_status(self):
    #     for record in self:
    #         if record.service_order_approval_id and record.service_order_approval_id.request_status == 'approved' and record.state == 'draft':
    #             record.service_approval_status = 'approve'
    #             record.write({'state':'approve'})
    #         else:
    #             record.service_approval_status = 'pending'

    def action_for_service_order_submit(self):
        approver_list = []

        if self.approval_level_1:
            approver_list.append(self.approval_level_1.id)
        if self.approval_level_2:
            approver_list.append(self.approval_level_2.id)
        if self.approval_level_3:
            approver_list.append(self.approval_level_3.id)

        for record in self:

            if not record.service_completion_line_ids:
                raise ValidationError(_("Please enter some service lines in the below section."))

            # if not record.request_owner_id or not record.category_id:
            #     raise UserError("Please fill in the required fields: Purchase No, Request Owner, and Category")
            # if record.reuse_button:
            #     raise ValidationError(_("The record is already Submitted, Please check the Service Order Approval Id"))

            # # Create an approval request
            # approval_request = record.env['approval.request'].create({
            #     'request_owner_id': record.request_owner_id.id,
            #     'category_id': record.category_id.id,
            #     'service_completion_id': record.id,
            # })

            # # Update the service_order_approval_id with the latest approval request ID
            # record.write({'service_order_approval_id': approval_request.id})
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

            # if record.service_order_approval_id:
            #     record.service_order_approval_id.action_confirm()
            # if record.service_order_approval_id:
            #     record.reuse_button = True
            self.sudo()._get_user_approval_activities(user=self.env.user)
            if approver_list:
                record._create_mail_activity_to_approval(approver_list[0])
                record.state = 'waiting1'

        return True

    # ................Total Amount.................
    @api.depends('service_completion_line_ids.price_tax_subtotal')
    def _compute_total_amount(self):
        for order in self:
            total_amount = sum(order.service_completion_line_ids.mapped('price_tax_subtotal'))
            order.update({'total_amount': total_amount})

    # indian currency words conversion method
    def convert_to_indian_currency_words(self, amount):
        """
        Convert amount to words using Indian numbering system and currency format.
        """
        # Convert amount to words using num2words with the Indian format
        words = num2words(amount, lang='en_IN')

        # Capitalize the first letter of the words
        words = words.capitalize()

        # Append 'Rupees only' at the end of the words
        words += " Rupees only"
        return words

    # /indian currency words conversion method

    # ..............Amount in words..........
    @api.depends('total_amount', 'currency_id')
    def _compute_amount_in_words(self):
        # for order in self:
        #     if order.total_amount:
        #         amount_words = order.currency_id.amount_to_text(order.total_amount)
        #         order.amount_in_words = amount_words.title()  # Capitalize the first letter
        #     else:
        #         order.amount_in_words = ""

        # indian currency words format conversion
        for order in self:
            if order.total_amount:
                # Convert the amount to words using the Indian currency format
                amount_words = self.convert_to_indian_currency_words(order.total_amount)
                order.amount_in_words = amount_words  # Amount in words with first letter capitalized
            else:
                order.amount_in_words = ""
        # /indian currency words format conversion

    # ..................Create Bill in Accounting...........

    def create_bill_in_account(self):
        action = {}
        for record in self:
            if not record.service_completion_line_ids:
                raise ValidationError(_("Please enter some service lines in the below section."))

            if record.service_completion_line_ids:
                if record.account_move_id:
                    action = {
                        'name': _('Service Invoice'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'account.move',
                        'view_mode': 'form',
                        'res_id': record.account_move_id.id,
                        'target': 'current',
                    }
                else:
                    new_invoice = self.env['account.move'].create({
                        'partner_id': record.partner_id.id,
                        'invoice_date': record.complete_date,
                        'journal_id': record.journal_id.id,
                        'move_type': 'in_invoice',
                        'company_id': record.company_id.id,
                        'original_bill': record.original_bills,
                        'invoice_origin': record.service_order_id.name
                    })

                    # Create invoice lines
                    invoice_line_ids = []
                    for product_line in record.service_completion_line_ids:
                        if product_line.discount_type and product_line.discount_amount:
                            discount_type = product_line.discount_type
                            discount_amount = product_line.discount_amount
                        else:
                            discount_type = False
                            discount_amount = 0.0

                        # Add partner taxes to the line taxes
                        line_taxes = product_line.taxes_id.ids + record.partner_id.taxes_id.ids

                        invoice_line_vals = {
                            'name': product_line.product_id.name,
                            'product_id': product_line.product_id.id,
                            'quantity': product_line.quantity,
                            'price_unit': product_line.price_unit,
                            'discount_type': discount_type,
                            'discount': discount_amount,
                            'tax_ids': [(6, 0, line_taxes)],
                            'move_id': new_invoice.id,
                        }
                        invoice_line = self.env['account.move.line'].create(invoice_line_vals)
                        invoice_line_ids.append(invoice_line.id)

                    new_invoice.write({'invoice_line_ids': [(6, 0, invoice_line_ids)]})
                    record.write({'account_move_id': new_invoice.id})
                    record.state = 'complete'

                    if record.service_order_id:
                        record.service_order_id.ask_confirm = True

                    action = {
                        'name': _('New Service Invoice'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'account.move',
                        'view_mode': 'form',
                        'res_id': new_invoice.id,
                        'target': 'current',
                    }

        return action

    def order_cancel(self):
        self.state = 'cancel'

    def order_draft(self):
        self.state = 'draft'

    def action_compute_service_orders(self):
        action = {
            'name': _('Service Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'service.order',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'view_mode': 'tree,form',
            'target': 'current',
        }
        return action

    def open_pdf_viewer(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=service.completion&id={}&field=original_bills'.format(self.id),
            'target': 'new',

        }

    def action_reject(self):
        for record in self:
            record.state = 'reject'
            # record._create_mail_activity_for_reject()
        self.sudo()._get_user_approval_activities(user=self.env.user).action_done()
        return True

    def action_approve(self):
        for record in self:
            if record.state == 'waiting1':
                # Logic for approval by level 1 approver
                if record.approval_level_2:
                    # Logic for approval by level 1 approver
                    record.state = 'waiting2'
                    record._create_mail_activity_to_approval(self.approval_level_2.id)
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
                'res_model_id': self.env.ref('service.model_service_completion').id,
                'res_id': self.id,
                'summary': 'Service Completion: %s' % self.name,
                'note': 'Service Completion: %s' % self.name,
                'display_name': 'Service Completion',
            })
            return activity
        return False

    def _get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'service.completion'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        print("############", activities)
        return activities


class ServiceCompletionLine(models.Model):
    _name = "service.completion.line"
    _description = 'Service Completion Lines'

    service_id = fields.Many2one("service.completion", string='Service completion ID')

    product_id = fields.Many2one("product.product", string="Product")
    description = fields.Text(string="Description")
    quantity = fields.Float(string="Quantity")
    last_purchase_cost = fields.Float(string="Last Purchase Cost", compute='_compute_last_purchase_cost')
    price_unit = fields.Float(string="Unit price", required=True, readonly=False, store=True,
                              compute='_compute_price_unit', default=0)
    taxes_id = fields.Many2many("account.tax", string="Taxes")
    price_subtotal = fields.Float(string='SubTotal', compute='_compute_price_subtotal', store=True)
    price_tax_subtotal = fields.Float(string='Subtotal (with Taxes)', compute='_compute_price_subtotal', store=True)
    currency_id = fields.Many2one("res.currency", string="Currency")

    discount_type = fields.Selection(
        [('fixed', 'Fixed'), ('percent', 'Percent')],
        string="Disc Type",
        default="percent")
    discount_amount = fields.Float(string="Discount", default=0.0)
    discounted_amount = fields.Float(string="Total Discount", compute='_compute_discounted_amount', store=True)

    igst_tax = fields.Float(string='IGST', compute='_compute_taxes', store=True)
    cgst_tax = fields.Float(string='CGST', compute='_compute_taxes', store=True)
    sgst_tax = fields.Float(string='SGST', compute='_compute_taxes', store=True)
    remaining_tax = fields.Float(string="Line Taxes", compute='_compute_taxes', store=True)
    product_uom_id = fields.Many2one(
        'uom.uom', string="Unit of Measure",
        compute="_compute_product_uom_id", store=True, readonly=False, precompute=True,
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    remarks = fields.Char(string='Remarks')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id,
                                 help='The default company for this user.', context={'user_preference': True},
                                 readonly=True)

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for line in self:
            line.product_uom_id = line.product_id.uom_id

    @api.onchange('product_id')
    def onchange_product_name(self):
        for rec in self:
            if rec.product_id:
                rec.description = rec.product_id.default_code
                rec.quantity = 1.0

            else:
                rec.description = ''
                rec.quantity = 0.0

    # ......unit price....
    @api.depends('product_id')
    def _compute_price_unit(self):
        for line in self:
            taxes_id = line.product_id.supplier_taxes_id
            line.taxes_id = taxes_id
            cost_price = line.product_id.standard_price
            sale_price = line.product_id.list_price
            line.price_unit = cost_price

    # ..........subtotal...........
    @api.depends('price_unit', 'taxes_id', 'quantity', 'discount_type', 'discount_amount')
    def _compute_price_subtotal(self):
        for line in self:
            currency = line.env['res.currency'].browse(line.env.user.company_id.currency_id.id)
            taxes = line.taxes_id.compute_all(line.price_unit, currency, line.quantity, product=line.product_id)
            line.price_subtotal = taxes['total_excluded']
            line.price_tax_subtotal = taxes['total_included']

            if line.discount_type == 'fixed':
                line.price_subtotal -= line.discount_amount
            elif line.discount_type == 'percent':
                line.price_subtotal -= (line.price_subtotal * line.discount_amount / 100)

            # Recalculate price_tax_subtotal based on price_subtotal and taxes_id
            taxes_total = sum(tax.amount for tax in line.taxes_id)
            line.price_tax_subtotal = line.price_subtotal * (1 + taxes_total / 100)

    # ..........last purchase cost.......
    @api.depends('product_id')
    def _compute_last_purchase_cost(self):
        for line in self:
            purchase_invoice_lines = self.env['account.move.line'].search([
                ('product_id', '=', line.product_id.id),
                ('move_id.move_type', '=', 'in_invoice'),
            ])

            sorted_invoice_lines = purchase_invoice_lines.sorted(key=lambda r: (r.move_id.date, r.id), reverse=True)

            purchase_invoice_line = sorted_invoice_lines[0] if sorted_invoice_lines else False

            if purchase_invoice_line:
                line.last_purchase_cost = purchase_invoice_line.price_unit
            else:
                line.last_purchase_cost = 0.0

    # ....... tax calculate.........
    @api.depends('taxes_id', 'price_subtotal')
    def _compute_taxes(self):
        for line in self:
            igst = cgst = sgst = gst = remaining_tax = 0.0

            for tax in line.taxes_id:
                if 'IGST' in tax.name.upper():
                    igst += line.price_subtotal * tax.amount / 100
                elif 'CGST' in tax.name.upper():
                    cgst += line.price_subtotal * tax.amount / 100
                elif 'SGST' in tax.name.upper():
                    sgst += line.price_subtotal * tax.amount / 100
                elif 'GST' in tax.name.upper():
                    gst += line.price_subtotal * tax.amount / 100
                else:
                    # Handle remaining taxes here
                    remaining_tax += line.price_subtotal * tax.amount / 100

            gst_split = gst / 2
            cgst += gst_split
            sgst += gst_split

            line.igst_tax = igst
            line.cgst_tax = cgst
            line.sgst_tax = sgst

            # Store the remaining_tax value in the field
            line.remaining_tax = remaining_tax

    @api.depends('price_unit', 'taxes_id', 'quantity', 'discount_type', 'discount_amount')
    def _compute_discounted_amount(self):
        for line in self:
            if line.discount_type == 'fixed':
                line.discounted_amount = line.discount_amount
            elif line.discount_type == 'percent':
                discount_amount = (line.price_unit * line.quantity * line.discount_amount) / 100
                line.discounted_amount = discount_amount
            else:
                # If neither 'fixed' nor 'percent', set discounted_amount to zero
                line.discounted_amount = 0.0


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.constrains('account_id', 'display_type')
    def _check_payable_receivable(self):
        for line in self:
            account_type = line.account_id.account_type
            # if line.move_id.is_sale_document(include_receipts=True):
            #     if (line.display_type == 'payment_term') ^ (account_type == 'asset_receivable'):
            #         raise UserError(_("Any journal item on a receivable account must have a due date and vice versa."))
            # if line.move_id.is_purchase_document(include_receipts=True):
            #     if (line.display_type == 'payment_term') ^ (account_type == 'liability_payable'):
            #         raise UserError(_("Any journal item on a payable account must have a due date and vice versa."))
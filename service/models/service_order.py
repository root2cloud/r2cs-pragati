from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from num2words import num2words


class ServiceOrder(models.Model):
    _name = 'service.order'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Service Order Model'

    def _get_default_category_id(self):
        domain = [('name', '=', "Service Order")]
        category_type = self.env['approval.category'].search(domain, limit=1)
        if category_type:
            return category_type.id
        return False

    READONLYSTATES = {
        'approve': [('readonly', True)]
    }

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, tracking=True,
                       default=lambda self: _('New'), states=READONLYSTATES)
    partner_id = fields.Many2one("res.partner", string="Vendor", required=True, tracking=True, states=READONLYSTATES)
    vendor_refernce = fields.Char(string="Vendor Reference", tracking=True, states=READONLYSTATES)
    order_date = fields.Date(string="Date", tracking=True, states=READONLYSTATES, default=fields.Datetime.now(),
                             required=True)
    transport = fields.Char(string="Transportation", tracking=True, states=READONLYSTATES)
    bill_reference = fields.Char(string="Bill Reference", tracking=True, states=READONLYSTATES)
    payment_terms_id = fields.Many2one("account.payment.term", string="Payment Terms", tracking=True,
                                       states=READONLYSTATES)
    service_narration = fields.Char(string="Service Narration", tracking=True, states=READONLYSTATES)
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
    expect_arrival = fields.Datetime(string="Expected Completion", tracking=True, states=READONLYSTATES,
                                     default=fields.Datetime.now())
    ask_confirm = fields.Boolean(string="Ask Confirmation", default=False, tracking=True, states=READONLYSTATES)
    state = fields.Selection([("draft", "Draft"), ("waiting1", "Waiting Level1"), ("waiting2", "Waiting Level2"),
                              ("waiting3", "Waiting Level3"), ("approve", "Approved"), ('reject', 'Approval Rejected'),
                              ("cancel", "Cancel")], default="draft", tracking=True)
    total_amount = fields.Monetary(string='Total Amount', compute="_compute_total_amount", store=True, tracking=True)

    advanced_amount = fields.Float(string='Advanced Amount', compute='_compute_advanced_amount', store=True,
                                   digits=(16, 3), tracking=True)

    service_line_ids = fields.One2many("service.order.line", "service_id", string="Service", states=READONLYSTATES,
                                       required=True)
    amount_in_words = fields.Char(string='Amount in Words', compute='_compute_amount_in_words', store=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id, tracking=True, readonly=True)
    approver_1 = fields.Char(string='Approver 1', store=True)
    approver_2 = fields.Char(string='Approver 2', store=True)
    approver_3 = fields.Char(string='Approver 2', store=True)
    reuse_button = fields.Boolean(default=False, tracking=True, states=READONLYSTATES)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id,
                                 help='The default company for this user.', context={'user_preference': True},
                                 readonly=True)
    location_id = fields.Many2one('stock.location', "Cost Center", tracking=True, states=READONLYSTATES,
                                  domain=[('is_cost_center', '=', True)])
    department_id = fields.Many2one('hr.department', 'Department', tracking=True, states=READONLYSTATES, required=True)
    igst_tax = fields.Float(string='IGST', compute='_compute_igst_amount', store=True, tracking=True)
    cgst_tax = fields.Float(string='CGST', compute='_compute_cgst_amount', store=True, tracking=True)
    sgst_tax = fields.Float(string='SGST', compute='_compute_sgst_amount', store=True, tracking=True)
    discount_total = fields.Float(string='Discount', compute='_compute_discount_total', store=True, digits=(16, 3),
                                  tracking=True)
    total_wo_tax = fields.Float(string='Untaxed Amount', compute='_compute_total_wo_tax', store=True, digits=(16, 3),
                                tracking=True)
    shipping_address_id = fields.Many2one('res.partner', string='Shipping Address', tracking=True)
    terms = fields.Text(string='Terms & Conditions', tracking=True)
    user_id = fields.Many2one('res.users', string='Responsible user',
                              default=lambda self: self.env.user)
    approval_level_1 = fields.Many2one('res.users', string='Approver Level 1', domain="[('share', '=', False)]",
                                       readonly=True)
    approval_level_2 = fields.Many2one('res.users', string='Approver Level 2', readonly=True,
                                       domain="[('share', '=', False)]", )
    approval_level_3 = fields.Many2one('res.users', string='Approver Level 3', readonly=True,
                                       domain="[('share', '=', False)]")
    show_approve_button = fields.Boolean(string='Show Approve Button', compute='_compute_show_approve_button',
                                         tracking=True)
    show_reject_button = fields.Boolean(string='Show Reject Button', compute='_compute_show_approve_button',
                                        tracking=True)

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

    @api.depends('service_line_ids.price_subtotal')
    def _compute_advanced_amount(self):
        for order in self:
            order.advanced_amount = sum(order.service_line_ids.mapped('price_subtotal'))

    def action_reset_to_draft(self):
        for record in self:
            record.write({'state': 'draft'})
        return True

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

    # Compute Total in the form based on service_line_ids
    @api.depends('service_line_ids.price_subtotal')
    def _compute_total_wo_tax(self):
        for order in self:
            order.total_wo_tax = sum(order.service_line_ids.mapped('price_subtotal'))

    # Compute Total in the form based on service_line_ids
    @api.depends('service_line_ids.igst_tax')
    def _compute_igst_amount(self):
        for order in self:
            order.igst_tax = sum(order.service_line_ids.mapped('igst_tax'))
        # Compute Total in the form based on service_line_ids

    @api.depends('service_line_ids.cgst_tax')
    def _compute_cgst_amount(self):
        for order in self:
            order.cgst_tax = sum(order.service_line_ids.mapped('cgst_tax'))
        # Compute Total in the form based on service_line_ids

    @api.depends('service_line_ids.sgst_tax')
    def _compute_sgst_amount(self):
        for order in self:
            order.sgst_tax = sum(order.service_line_ids.mapped('sgst_tax'))

    @api.depends('service_line_ids.discounted_amount')
    def _compute_discount_total(self):
        for order in self:
            order.discount_total = sum(order.service_line_ids.mapped('discounted_amount'))

    @api.model_create_multi
    def create(self, values_list):
        records = super(ServiceOrder, self).create(values_list)

        for record in records:
            if record.name == _('New'):
                fiscal_years = self.env['account.fiscal.year'].search([])
                current_date = fields.Date.context_today(self)

                sequence = self.env['ir.sequence'].next_by_code('service.order') or _('New')

                if fiscal_years:
                    for fiscal_year in fiscal_years:
                        start_date = fiscal_year.date_from
                        end_date = fiscal_year.date_to
                        if start_date <= current_date <= end_date:
                            sequence_number = sequence.split('/')[2] if sequence.startswith("SO/") else \
                                sequence.split('/')[0]
                            year_range = "{}-{}".format(start_date.strftime('%y'), end_date.strftime('%y'))
                            record.name = "SO/{}/{}".format(year_range, sequence_number.zfill(4))
                            break
                    else:
                        # No fiscal year found for the current date, default to current year and month
                        sequence_number = sequence.split('/')[2] if sequence.startswith("SO/") else sequence.split('/')[
                            0]
                        current_year_month = current_date.strftime('%m/%Y')
                        record.name = "SO/{}/{}".format(current_year_month, sequence_number.zfill(4))
                else:
                    # No fiscal years available, default to current year and month
                    sequence_number = sequence.split('/')[2] if sequence.startswith("SO/") else sequence.split('/')[0]
                    current_year_month = current_date.strftime('%m/%Y')
                    record.name = "SO/{}/{}".format(current_year_month, sequence_number.zfill(4))

        return records

    def order_cancel(self):
        self.state = 'cancel'

    def order_draft(self):
        self.state = 'draft'

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
            if not record.service_line_ids:
                raise ValidationError(_("Please enter some service lines in the below section."))

            # if not record.request_owner_id or not record.category_id:
            #     raise UserError("Please fill in the required fields: Purchase No, Request Owner, and Category")

            # if record.reuse_button:
            #     raise ValidationError(_("The record is already Submitted, Please check the Service Order Approval Id"))

            # # Create an approval request
            # approval_request = record.env['approval.request'].create({
            #     'request_owner_id': record.request_owner_id.id,
            #     'category_id': record.category_id.id,
            #     'service_order_sep_id': record.id,
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
    @api.depends('service_line_ids.price_tax_subtotal')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = sum(order.service_line_ids.mapped('price_tax_subtotal'))

    # new method to convert currency into indian currency words
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

    # /new method to convert currency into indian currency words
    # ..............Amount in words..........
    @api.depends('total_amount', 'currency_id')
    def _compute_amount_in_words(self):
        # for order in self:
        # if order.total_amount:
        #     amount_words = order.currency_id.amount_to_text(order.total_amount)
        #     order.amount_in_words = amount_words.title()  # Capitalize the first letter
        # else:
        #     order.amount_in_words = ""
        # amount in words in europe format converted to Indian format
        for order in self:
            if order.total_amount:
                # Convert the amount to words using the Indian currency format
                amount_words = self.convert_to_indian_currency_words(order.total_amount)
                order.amount_in_words = amount_words  # Amount in words with first letter capitalized
            else:
                order.amount_in_words = ""
        # /amount in words in europe format converted to Indian format

    def send_email_to_vendor(self):
        template = self.env.ref('service.email_template_edi_service')
        for rec in self:
            if rec.partner_id.email:
                template.send_mail(rec.id, force_send=True)

    def open_pdf_viewer(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=service.order&id={}&field=original_bills'.format(self.id),
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
                if record.approval_level_2:
                    # Logic for approval by level 1 approver
                    record.state = 'waiting2'
                    record._create_mail_activity_to_approval(self.approval_level_2.id)
                else:
                    record.state = 'approve'  # Move to the next state
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
                'res_model_id': self.env.ref('service.model_service_order').id,
                'res_id': self.id,
                'summary': 'Service Order: %s' % self.name,
                'note': 'Service Order: %s' % self.name,
                'display_name': 'Service Order',
            })
            return activity
        return False

    def _get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'service.order'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        print("############", activities)
        return activities


class ServiceOrderLine(models.Model):
    _name = "service.order.line"
    _description = 'Service Order Lines'
    service_id = fields.Many2one("service.order")

    service_id = fields.Many2one("service.order")
    product_id = fields.Many2one("product.product", string="Product", required=True)
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
                                 help='The default company for this user.', context={'user_preference': True})
    partner_id = fields.Many2one(related='service_id.partner_id', store=True, string='Partner')

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
    @api.depends('product_id', 'partner_id')
    def _compute_price_unit(self):
        for line in self:
            taxes_id = line.product_id.taxes_id
            tds_taxes = line.partner_id.taxes_id
            line.taxes_id = tds_taxes + taxes_id
            print("tacesssssssssssssssssss", line.taxes_id)
            cost_price = line.product_id.standard_price
            line.price_unit = cost_price

    # @api.depends('product_id')
    # def _compute_price_unit(self):
    #     for line in self:
    #         taxes_id = line.product_id.supplier_taxes_id
    #         line.taxes_id = taxes_id
    #         cost_price = line.product_id.standard_price
    #         sale_price = line.product_id.list_price
    #         line.price_unit = cost_price

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

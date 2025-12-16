from odoo import fields, models, Command, api, _
from odoo.exceptions import UserError, ValidationError
from num2words import num2words
from collections import defaultdict


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    pr_request_ids = fields.Many2many(
        'purchase.request',
        string='PR Links',
        domain="[('state', '=', 'approve')]",
        states=READONLY_STATES
    )

    def _get_default_category_id(self):
        domain = [('name', '=', "Purchase Order")]
        category_type = False
        # Get the current company
        company = self.env.company
        # Search for the approval category based on the current company
        if company:
            domain += [('company_id', '=', company.id)]
            category_type = self.env['approval.category'].search(domain, limit=1)
        # If category not found, fallback to the default company
        if not category_type:
            default_company = self.env['res.company'].search([], limit=1)
            if default_company:
                domain = [('name', '=', "Purchase Order"), ('company_id', '=', default_company.id)]
                category_type = self.env['approval.category'].search(domain, limit=1)
        if category_type:
            return category_type.id
        return False

    # def _get_default_user_id(self):
    #     domain = [('name', '=', "Managing Director"), ('login', '=', 'ajay@pragatigroup.com')]
    #     user_type = self.env['res.users'].search(domain, limit=1)
    #     if user_type:
    #         return user_type.id
    #     return False

    transport = fields.Char(string="Transportation")
    transport_bill = fields.Char(string="Bill Reference")
    delivery_terms_id = fields.Many2one('delivery.terms', string='Delivery Terms')
    approval_submit_id = fields.Many2one('approval.request', string='PO Approval ID')
    request_owner_id = fields.Many2one('res.users', string="Request Owner",
                                       check_company=True, domain="[('company_ids', 'in', company_id)]",
                                       default=lambda self: self.env.user)
    category_id = fields.Many2one('approval.category', string='category', default=_get_default_category_id)
    approve_status = fields.Selection([('pending', 'Pending'), ('approve', 'Approved')],
                                      string='Approval Status', default='pending')
    date_order = fields.Datetime('PO date', required=True, states=READONLY_STATES, index=True, copy=False,
                                 default=fields.Datetime.now,
                                 help="Depicts the date within which the Quotation should be confirmed and converted into a purchase order.")
    reuse_button = fields.Boolean(default=False, tracking=True, states=READONLY_STATES, )
    pr_completion = fields.Boolean(string='PR Completion?', default=False, tracking=True)
    narration = fields.Char(string=' PO Narration', )
    approver_1 = fields.Char(string='Approver 1', store=True)
    approver_2 = fields.Char(string='Approver 2', store=True)
    approver_3 = fields.Char(string='Approver 2', store=True)
    igst_tax = fields.Float(string='IGST', compute='_compute_igst_amount', store=True)
    cgst_tax = fields.Float(string='CGST', compute='_compute_cgst_amount', store=True)
    sgst_tax = fields.Float(string='SGST', compute='_compute_sgst_amount', store=True)
    amount_in_words = fields.Char(string='Amount in Words', compute='_compute_amount_in_words', store=True)
    warranty = fields.Char(string='Warranty')
    original_bill = fields.Binary(string='Original Bill', store=True, tracking=True)
    approval_level_1 = fields.Many2one('res.users', string='Approver Level 1', domain="[('share', '=', False)]",
                                       readonly=True)
    approval_level_2 = fields.Many2one('res.users', string='Approver Level 2', domain="[('share', '=', False)]",
                                       readonly=True)
    approval_level_3 = fields.Many2one('res.users', string='Approver Level 3', domain="[('share', '=', False)]",
                                       readonly=True, )
    original_bills = fields.Binary(string="Original Bill", attachment=True, tracking=True)
    state = fields.Selection(
        selection_add=[('draft', 'RFQ / Draft PO'), ("waiting1", "Waiting Level1"), ("waiting2", "Waiting Level2"),
                       ("waiting3", "Waiting Level3"), ("approve", "Approved"), ('reject', 'Rejected'), ('sent',)])

    department_id = fields.Many2one('hr.department', 'Department', tracking=True, states=READONLY_STATES)

    show_approve_button = fields.Boolean(string='Show Approve Button', compute='_compute_show_approve_button',
                                         tracking=True)
    show_reject_button = fields.Boolean(string='Show Approve Button', compute='_compute_show_approve_button',
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

    # @api.model
    # def create(self, vals):
    #     order = super().create(vals)
    #     if vals.get('pr_request_ids'):
    #         pr_ids = vals['pr_request_ids'][0][2]
    #         self.env['purchase.request'].browse(pr_ids).write({'is_used': True})
    #     return order
    #
    # def write(self, vals):
    #     res = super().write(vals)
    #     if vals.get('pr_request_ids'):
    #         pr_ids = vals['pr_request_ids'][0][2]
    #         self.env['purchase.request'].browse(pr_ids).write({'is_used': True})
    #     return res

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

    @api.depends('amount_total')
    def _compute_amount_in_words(self):
        for order in self:
            if order.amount_total:
                amount_words = order.currency_id.amount_to_text(order.amount_total)
                order.amount_in_words = amount_words.title()  # Capitalize the first letter
            else:
                order.amount_in_words = ""

    # Compute Total in the form based on order_line
    @api.depends('order_line.remaining_tax')
    def _compute_remaining_tax_total(self):
        for order in self:
            order.remaining_tax_total = sum(order.order_line.mapped('remaining_tax'))

    # Compute Total in the form based on order_line
    @api.depends('order_line.igst_tax')
    def _compute_igst_amount(self):
        for order in self:
            order.igst_tax = sum(order.order_line.mapped('igst_tax'))
        # Compute Total in the form based on order_line

    @api.depends('order_line.cgst_tax')
    def _compute_cgst_amount(self):
        for order in self:
            order.cgst_tax = sum(order.order_line.mapped('cgst_tax'))
        # Compute Total in the form based on order_line

    @api.depends('order_line.sgst_tax')
    def _compute_sgst_amount(self):
        for order in self:
            order.sgst_tax = sum(order.order_line.mapped('sgst_tax'))

    # @api.depends('approval_submit_id.approver_ids.status', 'approval_submit_id.approver_ids')
    # def _compute_approvers_names(self):
    #     for record in self:
    #         approver_1_name = False
    #         approver_2_name = False
    #         for approver in record.approval_submit_id.approver_ids:
    #             if approver.status == 'approved':
    #                 if not approver_1_name:
    #                     approver_1_name = approver.user_id.name
    #                 else:
    #                     approver_2_name = approver.user_id.name
    #         record.approver_1 = approver_1_name
    #         record.approver_2 = approver_2_name

    # craetinga a function for the stcok_name and schedule_date
    def action_create_invoice(self):
        res = super(PurchaseOrder, self).action_create_invoice()

        for invoice in self.invoice_ids:
            # if invoice.invoice_origin:
            # purchase_orders = self.env['purchase.order'].search([('name', '=', invoice.invoice_origin)])
            # for purchase_order in purchase_orders:
            invoice.write({
                'stock_name': self.picking_ids[0].name if self.picking_ids else '',
                'schedule_date': self.picking_ids[0].scheduled_date if self.picking_ids else '',
                'original_bill': self.picking_ids[0].original_bill,
                'bill_reference': self.transport_bill,
                # 'purchase_id':self.id
            })

        return res

    def call_approval_request_submit(self):
        approver_list = []

        if self.approval_level_1:
            approver_list.append(self.approval_level_1.id)
        if self.approval_level_2:
            approver_list.append(self.approval_level_2.id)
        if self.approval_level_3:
            approver_list.append(self.approval_level_3.id)

        if not self.request_owner_id or not self.category_id:
            raise UserError("Please fill in the required fields: Purchase No, Request Owner, and Category.")

        # if self.reuse_button:
        #     raise ValidationError(_("The record is already Submitted, Please check the PO Approval ID"))

        if not approver_list:
            raise UserError("Please assign at least one approver for approval.")

        # Create an approval request
        # approval_request = self.env['approval.request'].create({
        #     'purchase_no_id': self.id,
        #     'request_owner_id': self.request_owner_id.id,
        #     'category_id': self.category_id.id,
        # })

        # # Update the approval_submit_id with the latest approval request ID
        # self.write({'approval_submit_id': approval_request.id})

        # # Create approval approver records based on purchase order lines
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

        # if self.approval_submit_id:
        #     self.approval_submit_id.action_confirm()
        #     self.reuse_button = True
        # self.reuse_button = True
        self.sudo()._get_user_approval_activities(user=self.env.user)
        if approver_list:
            self._create_mail_activity_to_approval(approver_list[0])
            self.state = 'waiting1'
            print("@@@@@@@@@@@@@@@@@@@@@@@@@")

        return True

    # @api.depends('approval_submit_id.request_status')
    # def _compute_approve_status(self):
    #     for record in self:
    #         if record.approval_submit_id and record.approval_submit_id.request_status == 'approved':
    #             record.approve_status = 'approve'
    #         else:
    #             record.approve_status = 'pending'

    # def button_confirm(self):
    #     res = super(PurchaseOrder, self).button_confirm()
    #     for record in self:
    #         if record.pr_request_id:
    #             for po_order in record.order_line:
    #                 main_qty = po_order.product_qty

    #                 product_qtys_list = []
    #                 for pr_rec in record.pr_request_id:                        
    #                     for line in pr_rec.pr_request_line_ids:
    #                         # print(line.product_id.name,"PR id pr_productTTtttttttttttttt11111ttttttttttttttt")
    #                         if line.product_id.id == po_order.product_id.id:
    #                             product_qtys_list.append({'product_name':line.product_id.id,'pro_qty':line.quantity,'line_details':line})
    #                 sorted_product_qtys_list = sorted(product_qtys_list, key=lambda x: x['pro_qty'])

    #                 for each_product in sorted_product_qtys_list:
    #                     for each_line in each_product['line_details']:
    #                         if main_qty >0 and main_qty > each_line.quantity:
    #                             main_qty -= each_line.quantity
    #                             each_line.purchased_qty = each_line.quantity
    #                             each_line.quantity -=  each_line.purchased_qty
    #                         elif main_qty>0 and main_qty < each_line.quantity:
    #                             # main_qty = each_line.quantity-main_qty
    #                             each_line.purchased_qty = main_qty
    #                             each_line.quantity =  each_line.quantity - each_line.purchased_qty

    #         return res

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for record in self:
            if record.state in ['draft', 'sent', 'approve']:
                # Execute additional functionality only when the state is 'approve' or there is a 'pr_request_id'
                if record.state == 'approve' or record.pr_request_ids:
                    for po_order in record.order_line:
                        main_qty = po_order.product_qty
                        product_qtys_list = []
                        for pr_rec in record.pr_request_ids:
                            for line in pr_rec.pr_request_line_ids:
                                if line.product_id.id == po_order.product_id.id:
                                    product_qtys_list.append(
                                        {'product_name': line.product_id.id, 'pro_qty': line.quantity,
                                         'line_details': line})
                        sorted_product_qtys_list = sorted(product_qtys_list, key=lambda x: x['pro_qty'])

                        for each_product in sorted_product_qtys_list:
                            for each_line in each_product['line_details']:
                                if main_qty > 0 and main_qty > each_line.quantity:
                                    main_qty -= each_line.quantity
                                    each_line.purchased_qty = each_line.quantity
                                    each_line.quantity -= each_line.purchased_qty
                                elif main_qty > 0 and main_qty < each_line.quantity:
                                    each_line.purchased_qty = main_qty
                                    each_line.quantity = each_line.quantity - each_line.purchased_qty
                # Original functionality
                record.order_line._validate_analytic_distribution()
                record._add_supplier_to_product()
                # Deal with double validation process
                if record.state == 'approve' or record._approval_allowed():
                    record.button_approve()
                else:
                    record.write({'state': 'to approve'})
                if record.partner_id not in record.message_partner_ids:
                    record.message_subscribe([record.partner_id.id])
        return True

    def action_open_product_selection_wizard(self):
        # self.state = 'cancel'
        return {
            'name': _('Select Products from PR Links'),
            'view_mode': 'form',
            'res_model': 'product.selection.wizard',
            'view_id': self.env.ref('pragati_custom_module.product_selection_wizard_form_view').id,
            'type': 'ir.actions.act_window',
            # 'context': {'default_order_id': self.id},
            'target': 'new'
        }

    def open_pdf_viewer(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=purchase.order&id={}&field=original_bills'.format(self.id),
            'target': 'new',

        }

    def action_approve(self):

        for record in self:
            if record.state == 'waiting1':
                # Logic for approval by level 1 approver
                if record.approval_level_2:
                    record.state = 'waiting2'
                    record._create_mail_activity_to_approval(self.approval_level_2.id)
                    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")  # Move to the next state
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

    def action_reject(self):
        for record in self:
            record.state = 'reject'
            # record._create_mail_activity_for_reject()
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
                'res_model_id': self.env.ref('pragati_custom_module.model_purchase_order').id,
                'res_id': self.id,
                'summary': 'Purchase Order: %s' % self.name,
                'note': 'Purchase Order: %s' % self.name,
                'display_name': 'Purchase Order',
            })
            return activity
        return False

    def _get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'purchase.order'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        print("############", activities)
        return activities

    def action_rfq_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        print("%%%%%%%%%%%%%%%%%%%%%%%%")
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase')[2]
            else:
                template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase_done')[2]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'active_model': 'purchase.order',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
            'mark_rfq_as_sent': True,
        })

        # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
        # object. Therefore, we pass the model description in the context, in the language in which
        # the template is rendered.
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)
        if self.state in ['draft', 'approve']:  # Modified this line to include 'approved' state
            ctx['model_description'] = _('Request for Quotation')
            if self.state == 'approve':
                self.write({'state': 'sent'})  # Change state from 'approved' to 'sent'
        else:
            ctx['model_description'] = _('Purchase Order')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

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

    last_purchase_cost = fields.Float(string='Last Purchase Cost', compute='_compute_last_purchase_cost')
    approvers_id = fields.Many2one('res.users', string="User")
    required_approved = fields.Boolean(string='Required', default=False, compute='_compute_required_approved')
    igst_tax = fields.Float(string='IGST', compute='_compute_taxes', store=True)
    cgst_tax = fields.Float(string='CGST', compute='_compute_taxes', store=True)
    sgst_tax = fields.Float(string='SGST', compute='_compute_taxes', store=True)
    remaining_tax = fields.Float(string="Line Taxes", compute='_compute_taxes', store=True)

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

    @api.depends('approvers_id')
    def _compute_required_approved(self):
        for line in self:
            line.required_approved = bool(line.approvers_id)

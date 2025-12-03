from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Purchase Request Model'

    def _get_default_category_id(self):
        domain = [('name', '=', "Purchase Request")]
        category_type = self.env['approval.category'].search(domain, limit=1)
        if category_type:
            return category_type.id
        return False

    def _get_default_location_id(self):
        domain = [('name', '=', "Stock")]
        location = self.env['stock.location'].search(domain, limit=1)
        if location:
            return location.id
        return False

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, tracking=True,
                       default=lambda self: _('New'))
    order_date = fields.Date(string="PR Date", tracking=True, required=True, default=fields.Date.today())
    transport = fields.Char(string="Transportation", tracking=True)
    service_narration = fields.Char(string="PR Narration", tracking=True)
    purchase_request_approval_id = fields.Many2one("approval.request", string="PR Approval Id", tracking=True)
    request_approval_status = fields.Selection([('pending', 'Pending'), ('approve', 'Approved')],
                                               string='Approval Status', default='pending', tracking=True)
    request_owner_id = fields.Many2one('res.users', string="Request Owner",
                                       check_company=True, domain="[('company_ids', 'in', company_id)]",
                                       default=lambda self: self.env.user, tracking=True)
    category_id = fields.Many2one('approval.category', string='category', default=_get_default_category_id,
                                  tracking=True)
    expect_arrival = fields.Datetime(string="Expected Arrival", tracking=True, required=True)
    state = fields.Selection([("draft", "Draft"), ("waiting1", "Waiting Level1"), ("waiting2", "Waiting Level2"),
                              ("waiting3", "Waiting Level3"), ("approve", "Approved"), ('reject', 'Approval Rejected'),
                              ("cancel", "Cancel")], default="draft", tracking=True)

    # purchase_order_ids = fields.One2many('purchase.order', 'requisition_id', string="Purchase Orders")
    # newly added

    pr_request_line_ids = fields.One2many("purchase.request.line", "request_id", string="Service", tracking=True,
                                          required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id, tracking=True)
    approver_1 = fields.Char(string='Approver 1', store=True)
    approver_2 = fields.Char(string='Approver 2', store=True)
    approver_3 = fields.Char(string='Approver 3', store=True)
    reuse_button = fields.Boolean(default=False, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id,
                                 help='The default company for this user.', context={'user_preference': True})
    location_id = fields.Many2one('stock.location', "Cost Center", readonly=False, tracking=True)
    department_id = fields.Many2one('hr.department', 'Department', tracking=True)
    shipping_address_id = fields.Many2one('res.partner', string='Shipping Address', tracking=True, required=True)
    terms = fields.Text(string='Terms & Conditions', tracking=True)
    user_id = fields.Many2one('res.users', string='Responsible user',
                              default=lambda self: self.env.user, tracking=True)
    material_indent_id = fields.Many2one('material.indent', string='Material Reference Id',
                                         domain="[('close_indent', '=', False), ('state', '=', 'approve')]")
    pr_confirmation = fields.Boolean(string='PR Confirm', default=False, tracking=True,
                                     compute="_compute_true_all_pro_qty_zero", store=True)
    partner_id = fields.Many2one('res.partner', related='request_owner_id.partner_id', tracking=True)
    note = fields.Text(string='Remarks', tracking=True)
    location_dest_id = fields.Many2one('stock.location', "warehouse", default=_get_default_location_id, readonly=False,
                                       tracking=True)
    approval_level_1 = fields.Many2one('res.users', string="Approver Level 1", tracking=True, readonly=True)
    approval_level_2 = fields.Many2one('res.users', string="Approver Level 2", tracking=True, readonly=True)

    approval_level_3 = fields.Many2one('res.users', string='Approver Level 3', domain="[('share', '=', False)],",
                                       readonly=True)
    show_approve_button = fields.Boolean(string='Show Approve Button', compute='_compute_show_approve_button',
                                         tracking=True)
    show_reject_button = fields.Boolean(string='Show Reject Button', compute='_compute_show_approve_button',
                                        tracking=True)
    purchase_count = fields.Integer(compute="_compute_purchase_count")

    material_status = fields.Selection(related="material_indent_id.state", string="Material Status")

    delay_days = fields.Integer(string="Delay_Days")

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
    def _compute_purchase_count(self):
        for rec in self:
            purchase_order_ids = self.env['purchase.order'].search([('pr_request_ids', 'in', rec.id)])
            rec.purchase_count = len(purchase_order_ids)

    def view_purchase_order(self):
        purchase_order_ids = self.env['purchase.order'].search([('pr_request_ids', 'in', self.id)])
        return {
            'name': _('Purchase Order'),
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', purchase_order_ids.ids)],
        }

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

    @api.onchange('material_indent_id')
    def _onchange_material_indent_id(self):
        if self.material_indent_id:
            self.order_date = self.material_indent_id.complete_date
            self.request_owner_id = self.material_indent_id.request_owner_id.id
            self.location_id = self.material_indent_id.location_id.id
            self.department_id = self.material_indent_id.department_id.id
            self.transport = self.material_indent_id.transport
            self.service_narration = self.material_indent_id.service_narration
            self.expect_arrival = self.material_indent_id.expect_arrival
            self.terms = self.material_indent_id.terms
            self.note = self.material_indent_id.note
            self.shipping_address_id = self.material_indent_id.shipping_address_id.id

            # Update the product lines
            self.pr_request_line_ids = [(5, 0, 0)]  # Clear existing lines
            lines = []
            for line in self.material_indent_id.material_indent_line_ids:
                vals = {
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'product_uom_id': line.product_uom_id.id,
                    'remarks': line.remarks,
                }
                lines.append((0, 0, vals))

            self.pr_request_line_ids = lines
        if self.material_indent_id.stock_picking_id and self.material_indent_id.stock_picking_id.state == 'done':
            for line in self.pr_request_line_ids:
                l1 = []
                for stock_move in self.material_indent_id.stock_picking_id.move_ids.filtered(
                        lambda m: m.product_id == line.product_id):
                    issued = stock_move.quantity_done
                    l1.append(issued)
                    line.quantity -= issued
                    line.issued_quantity = l1[0]

    @api.model_create_multi
    def create(self, values_list):
        records = super(PurchaseRequest, self).create(values_list)

        for record in records:
            if record.name == _('New'):
                fiscal_years = self.env['account.fiscal.year'].search([])
                current_date = fields.Date.context_today(self)

                if fiscal_years:
                    for fiscal_year in fiscal_years:
                        start_date = fiscal_year.date_from
                        end_date = fiscal_year.date_to
                        if start_date <= current_date <= end_date:
                            sequence_number = self.env['ir.sequence'].next_by_code('purchase.request') or _('New')
                            year_range = "{}-{}".format(start_date.strftime('%y'), end_date.strftime('%y'))
                            record.name = "PR/{}/{}".format(
                                year_range, sequence_number.zfill(5)
                            )
                            break
                    else:
                        # No fiscal year found for the current date, default to current year and month
                        sequence_number = self.env['ir.sequence'].next_by_code('purchase.request') or _('New')
                        current_year_month = current_date.strftime('%m/%Y')
                        record.name = "PR/{}/{}".format(current_year_month, sequence_number.zfill(5))

                else:
                    # No fiscal years available, default to current year and month
                    sequence_number = self.env['ir.sequence'].next_by_code('purchase.request') or _('New')
                    current_year_month = current_date.strftime('%m/%Y')
                    record.name = "PR/{}/{}".format(current_year_month, sequence_number.zfill(5))

        return records

    def order_cancel(self):
        self.state = 'cancel'

    def order_draft(self):
        self.state = 'draft'

    # @api.depends('purchase_request_approval_id.approver_ids.status', 'purchase_request_approval_id.approver_ids')
    # def _compute_approvers_names(self):
    #     for record in self:
    #         approver_1_name = False
    #         approver_2_name = False
    #         for approver in record.purchase_request_approval_id.approver_ids:
    #             if approver.status == 'approved':
    #                 if not approver_1_name:
    #                     approver_1_name = approver.user_id.name
    #                 else:
    #                     approver_2_name = approver.user_id.name
    #         record.approver_1 = approver_1_name
    #         record.approver_2 = approver_2_name

    # @api.depends('purchase_request_approval_id.request_status')
    # def _compute_approve_status(self):
    #     for record in self:
    #         if record.purchase_request_approval_id and record.purchase_request_approval_id.request_status == 'approved' and record.state == 'draft':
    #             # record.request_approval_status = 'approve'
    #             print("%%%%%%%%%%%%%%%%%%%%%%%##################")
    #             record.write({'state':'approve', 'request_approval_status':'approve'})
    #             record.material_indent_id.write({'close_indent':True})

    #         else:
    #             record.request_approval_status = 'pending'

    def action_for_purchase_request_submit(self):
        approver_list = []

        if self.approval_level_1:
            approver_list.append(self.approval_level_1.id)
        if self.approval_level_2:
            approver_list.append(self.approval_level_2.id)
        if self.approval_level_3:
            approver_list.append(self.approval_level_3.id)

        for record in self:
            if not record.pr_request_line_ids:
                raise ValidationError(_("Please enter some PR lines in the below section."))

            # if not record.request_owner_id or not record.category_id:
            #     raise UserError("Please fill in the required fields: Purchase No, Request Owner, and Category")
            # if record.reuse_button:
            #     raise ValidationError(_("The record is already Submitted, Please check the PR Approval Id"))

            # # Create an approval request
            # approval_request = record.env['approval.request'].create({
            #     'request_owner_id': record.request_owner_id.id,
            #     'category_id': record.category_id.id,
            #     'purchase_request_id': record.id,
            # })

            # # Update the purchase_request_approval_id with the latest approval request ID
            # record.write({'purchase_request_approval_id': approval_request.id})

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

            # if record.purchase_request_approval_id:
            #     record.purchase_request_approval_id.action_confirm()
            # if record.purchase_request_approval_id:
            #     record.reuse_button = True
            self.sudo()._get_user_approval_activities(user=self.env.user)
            if approver_list:
                record._create_mail_activity_to_approval(approver_list[0])
                record.state = 'waiting1'
            if record.material_indent_id: record.material_indent_id.write({'close_indent': True})
        return True

    @api.depends('pr_request_line_ids')
    def _compute_true_all_pro_qty_zero(self):
        for rec in self:
            all_zero = all(line.quantity == 0 for line in rec.pr_request_line_ids)
            rec.pr_confirmation = all_zero

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
                'res_model_id': self.env.ref('material_and_pr_requistion.model_purchase_request').id,
                'res_id': self.id,
                'summary': 'Purchase Request: %s' % self.name,
                'note': 'Purchase Request: %s' % self.name,
                'display_name': 'Purchase Request',
            })
            return activity
        return False

    def _get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'purchase.request'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        print("############", activities)
        return activities


class PurchaseRequestLine(models.Model):
    _name = "purchase.request.line"
    _description = 'Purchase Request Lines'
    request_id = fields.Many2one("purchase.request")

    product_id = fields.Many2one("product.product", string="Product", required=True)
    po_numbers = fields.Char(string="PO Numbers", related='request_id.po_numbers')
    description = fields.Text(string="Description")
    quantity = fields.Float(string="Quantity")
    last_purchase_cost = fields.Float(string="Last Purchase Cost", compute='_compute_last_purchase_cost')
    currency_id = fields.Many2one("res.currency", string="Currency")

    product_uom_id = fields.Many2one(
        'uom.uom', string="Unit of Measure",
        compute="_compute_product_uom_id", store=True, readonly=False, precompute=True,
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    remarks = fields.Char(string='Remarks')
    issued_quantity = fields.Float(string='Issued Quantity')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id,
                                 help='The default company for this user.', context={'user_preference': True})
    purchased_qty = fields.Float(string='Purchased Qty')

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

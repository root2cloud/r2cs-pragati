from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_default_category_id(self):
        domain = [('name', '=', "MRN Order")]
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
                domain = [('name', '=', "MRN Order"), ('company_id', '=', default_company.id)]
                category_type = self.env['approval.category'].search(domain, limit=1)
        if category_type:
            return category_type.id
        return False

    name = fields.Char(
        'Reference', default='/',
        copy=False, index='trigram', readonly=True)
    approval_id = fields.Many2one('approval.request', string="MI Link")
    bill_date = fields.Datetime(string="Bill Date", default=lambda self: datetime.today())
    bill_ref_id = fields.Char(string="Bill Number", tracking=True)
    approval_submit_id = fields.Many2one('approval.request',string='MRN Approval ID', copy=False)
    category_id = fields.Many2one('approval.category',string='category',default=_get_default_category_id)
    request_owner_id = fields.Many2one('res.users', string="Request Owner",
        check_company=True, domain="[('company_ids', 'in', company_id)]", default=lambda self: self.env.user)
    approve_status = fields.Selection([('pending', 'Pending'), ('approve', 'Approved')],
        string='Approval Status', default='pending', compute='_compute_approve_status')
    custom_picking_type = fields.Char(string="Custom",related="picking_type_id.name")
    qr_code_label = fields.Binary(string='QR Code', readonly=True, copy=False)
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),("waiting1","Waiting Level1"),
        ("waiting2","Waiting Level2"),
        ("waiting3","Waiting Level3"),
        ("approve","Approved"),
        ('reject', 'Rejected'),
        ('done', 'Done'),
        ('sign', 'Customer Signed'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")

    approval_level_1 = fields.Many2one('res.users', string='Approver Level 1', domain="[('share', '=', False)]")
    approval_level_2 = fields.Many2one('res.users', string='Approver Level 2', domain="[('share', '=', False)]")
    approval_level_3 = fields.Many2one('res.users', string='Approver Level 3', domain="[('share', '=', False)]")
    
    show_approve_button = fields.Boolean(string='Show Approve Button', compute='_compute_show_approve_button', tracking=True)
    show_reject_button =  fields.Boolean(string='Show Approve Button', compute='_compute_show_approve_button', tracking=True)
    

    def action_reset_to_draft(self):
        for record in self:
            record.write({'state': 'draft'})
        return True

        
    @api.onchange('approval_level_1')
    def _onchange_approval_level_1(self):
        for record in self:
            if record.approval_level_1 and (record.approval_level_1 == record.approval_level_2 or record.approval_level_1 == record.approval_level_3):
                raise UserError("The same Approver is selected more than once. Please check and correct it.")

    @api.onchange('approval_level_2')
    def _onchange_approval_level_2(self):
        for record in self:
            if record.approval_level_2 and (record.approval_level_2 == record.approval_level_1 or record.approval_level_2 == record.approval_level_3):
                raise UserError("The same Approver is selected more than once. Please check and correct it.")

    @api.onchange('approval_level_3')
    def _onchange_approval_level_3(self):
        for record in self:
            if record.approval_level_3 and (record.approval_level_3 == record.approval_level_1 or record.approval_level_3 == record.approval_level_2):
                raise UserError("The same Approver is selected more than once. Please check and correct it.")


    
    def write(self, vals):
        if vals.get('picking_type_id') and any(picking.state != 'draft' for picking in self):
            raise UserError(_("Changing the operation type of this record is forbidden at this point."))

        # set partner as a follower and unfollow old partner
        if vals.get('partner_id'):
            for picking in self:
                if picking.location_id.usage == 'supplier' or picking.location_dest_id.usage == 'customer':
                    if picking.partner_id:
                        picking.message_unsubscribe(picking.partner_id.ids)
                    picking.message_subscribe([vals.get('partner_id')])

        res = super(StockPicking, self).write(vals)

        if vals.get('signature'):
            for picking in self:
                picking._attach_sign()
                picking.state = 'sign'  # Add this line to set the state to 'sign'

        # Change locations of moves if those of the picking change
        after_vals = {}
        if vals.get('location_id'):
            after_vals['location_id'] = vals['location_id']
        if vals.get('location_dest_id'):
            after_vals['location_dest_id'] = vals['location_dest_id']
        if 'partner_id' in vals:
            after_vals['partner_id'] = vals['partner_id']
        if after_vals:
            self.move_ids.filtered(lambda move: not move.scrapped).write(after_vals)

        if vals.get('move_ids'):
            self._autoconfirm_picking()
        if 'move_ids' in vals:
            self.compute_balance_quantity()
        return res


    
    original_bill = fields.Binary(string='Original Bill / DC', store=True, tracking=True)
    approver_1 = fields.Char(string='Approver 1', compute='_compute_approvers_names', store=True)
    approver_2 = fields.Char(string='Approver 2', compute='_compute_approvers_names', store=True)
    reuse_button = fields.Boolean(default=False, copy=False)

    @api.depends('approval_submit_id.approver_ids.status', 'approval_submit_id.approver_ids')
    def _compute_approvers_names(self):
        for record in self:
            approver_1_name = False
            approver_2_name = False
            for approver in record.approval_submit_id.approver_ids:
                if approver.status == 'approved':
                    if not approver_1_name:
                        approver_1_name = approver.user_id.name
                    else:
                        approver_2_name = approver.user_id.name
            record.approver_1 = approver_1_name
            record.approver_2 = approver_2_name

    def button_validate(self):
        for record in self:
            # if not record.state == 'approve' and record.custom_picking_type == 'Receipts':
            #     raise ValidationError(_("The record is not yet approved!!!, Please submit the record for Approval"))

            
            # Call the method to update the respective purchase order
            record.update_purchase_order()
            self.compute_balance_quantity()
        return super(StockPicking, self).button_validate()

    def update_purchase_order(self):
        for record in self:
            purchase_order = record.purchase_id  # Assuming 'purchase_id' is the field linking stock picking to purchase order
            if purchase_order:
                # Update the purchase order with the bill_ref_id and original_bill
                purchase_order.write({
                    'transport_bill': record.bill_ref_id,
                    'original_bill': record.original_bill,
                })
                
    def call_approval_request_submit_stock_picking(self):
        approver_list = []
        
        if self.approval_level_1:
            approver_list.append(self.approval_level_1.id)
        if self.approval_level_2:
            approver_list.append(self.approval_level_2.id)
        if self.approval_level_3:
            approver_list.append(self.approval_level_3.id)
        for record in self:

            if record.custom_picking_type == 'Receipts' and not (record.bill_ref_id and record.original_bill):
                raise UserError("Please Update the Bill Number and original_bill before Submitting.")

            if not record.request_owner_id or not record.category_id:
                raise UserError("Please fill in the required fields: Purchase No, Request Owner, and Category")
                
            # if record.reuse_button:
            #     raise ValidationError(_("The record is already Submitted, Please check the MRN Approval ID"))
            
            # if not approver_list:
            #     raise UserError("Please assign at least one approver for approval.")


            # Create an approval request
            approval_request = record.env['approval.request'].create({
                'stock_picking_id': record.id,
                'request_owner_id': record.request_owner_id.id,
                'category_id': record.category_id.id,
            })

            # Update the approval_submit_id with the latest approval request ID
            # record.write({'approval_submit_id': approval_request.id})
            approver_values = []

            # for line in approver_list:
            #     approver_values.append((0, 0, {
            #         'user_id': line,
            #         'required': True,
            #     }))
            # # Link approval request to the approval approvers
            # approval_request.write({
            #     'approver_ids': approver_values,
            # })

            # if record.approval_submit_id:
            #     record.approval_submit_id.action_confirm()
            # if record.name:
            # record.reuse_button = True

            self.sudo()._get_user_approval_activities(user=self.env.user)
            if approver_list:
                self._create_mail_activity_to_approval(approver_list[0])
                self.state = 'waiting1'
                print("@@@@@@@@@@@@@@@@@@@@@@@@@")

        return True


    @api.depends('approval_submit_id.request_status')
    def _compute_approve_status(self):
        for record in self:
            if record.approval_submit_id and record.approval_submit_id.request_status == 'approved':
                record.approve_status = 'approve'
            else:
                record.approve_status = 'pending'



    def compute_balance_quantity(self):
        for record in self:
            for move in record.move_ids:
                if move.location_id.usage in ['internal', 'transit'] and move.location_dest_id.usage not in ['internal', 'transit']:
                    # For deliveries
                    move.balance_qty = move.on_hand_qty - move.product_uom_qty
                    move.issued_qty = move.product_uom_qty

                    # For deliveries, calculate balance value based on sale price
                    move.balance_value = move.product_id.list_price * move.balance_qty

                    # Calculate average value based on sale price if balance_qty is not zero
                    if move.balance_qty != 0:
                        move.average_value = move.balance_value / move.balance_qty
                    else:
                        move.average_value = 0.0

                    if record.sale_id:
                        move.total_wo_tax = record.sale_id.amount_untaxed
                        move.total = record.sale_id.amount_total
                        move.partner_name = record.sale_id.partner_id.name

                elif move.location_id.usage not in ['internal', 'transit'] and move.location_dest_id.usage in ['internal', 'transit']:
                    # For receipts
                    move.balance_qty = move.on_hand_qty + move.product_uom_qty
                    move.received_qty = move.product_uom_qty

                    # For receipts, calculate balance value based on standard price
                    move.balance_value = move.product_id.standard_price * move.balance_qty

                    # Calculate average value based on standard price if received_qty is not zero
                    if move.received_qty != 0:
                        move.average_value = move.balance_value / move.received_qty
                    else:
                        move.average_value = 0.0

                    if record.purchase_id:
                        move.total_wo_tax = record.purchase_id.amount_untaxed
                        move.total = record.purchase_id.amount_total
                        move.partner_name = record.purchase_id.partner_id.name

                else:
                    # If neither delivery nor receipt, set balance quantity to 0
                    move.balance_qty = 0.0
                    move.received_qty = 0.0
                    move.issued_qty = 0.0

                    # Set balance value, average value, total, and total_wo_tax to 0.0
                    move.balance_value = 0.0
                    move.average_value = 0.0
                    move.total_wo_tax = 0.0
                    move.total = 0.0


    # def write(self, vals):
    #     res = super(StockPicking, self).write(vals)
    #     if 'move_ids' in vals:
    #         self.compute_balance_quantity()
    #     return res


    def open_pdf_viewer(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=stock.picking&id={}&field=original_bill'.format(self.id),
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
                record.show_reject_button = True
            elif record.state == 'waiting2' and record.approval_level_2 == self.env.user:
                record.show_approve_button = True
                record.show_reject_button = True
            elif record.state == 'waiting3' and record.approval_level_3 == self.env.user:
                record.show_approve_button = True
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
                'res_model_id': self.env.ref('pragati_custom_module.model_stock_picking').id,
                'res_id': self.id,
                'summary': 'Stock Picking Approval: %s' % self.name,
                'note': 'Stock Picking Approval: %s' % self.name,
                'display_name': 'Stock Picking Approval',
            })
            return activity
        return False
    
    def _get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'stock.picking'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        print("############",activities)
        return activities

class StockMove(models.Model):
    _inherit = 'stock.move'

    on_hand_qty = fields.Float(string='On Hand Quantity', compute='_compute_on_hand_qty')
    balance_qty = fields.Float(string='Balance Quantity')
    received_qty = fields.Float(string='Received Quantity')
    issued_qty = fields.Float(string='Issued Quantity')
    balance_value = fields.Float(string='Balance Value')
    average_value = fields.Float(string='Average Value')
    total_wo_tax = fields.Float(string='Untaxable Value')
    total = fields.Float(string='Total Value')
    partner_name = fields.Char(string='Partner Name')


    @api.depends('product_id')
    def _compute_on_hand_qty(self):
        for move in self:
            if move.product_id:
                product = move.product_id
                on_hand_qty = product.qty_available
                move.on_hand_qty = on_hand_qty
            else:
                move.on_hand_qty = 0.0

    # @api.onchange('product_uom_qty')
    # def _onchange_balance_qty(self):
    #     for rec in self:
    #         if rec.product_uom_qty and (rec.location_usage in ('internal','transit')) and (rec.location_dest_usage not in ('internal','transit')):
    #             rec.balance_qty = rec.on_hand_qty - rec.product_uom_qty

    #         elif rec.product_uom_qty and (rec.location_usage not in ('internal','transit')) and (rec.location_dest_usage in ('internal','transit')):
    #             rec.balance_qty = rec.on_hand_qty + rec.product_uom_qty

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    demand = fields.Float(string ="Demand", related="move_id.product_uom_qty", store=True)

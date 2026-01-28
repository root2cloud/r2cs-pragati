from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class CouponIssue(models.Model):
    _name = 'coupon.issue'
    _description = 'Coupon Issue'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )

    salesperson_id = fields.Many2one(
        'res.users',
        string="Salesperson",
        required=True
    )

    salespersons_name = fields.Char(
        string="Salesperson",
        required=True
    )

    # Customer Info
    customer_id = fields.Many2one('res.partner', string="Customer", required=True)
    mobile = fields.Char(string="Mobile Number")
    address = fields.Text(string="Address")

    # Coupon Details
    coupon_code = fields.Char(string="Coupon Code", required=True, copy=False)
    coupon_value = fields.Float(string="Coupon Value", required=True)
    issue_date = fields.Date(string="Issue Date", default=fields.Date.context_today)
    expiry_date = fields.Date(string="Expiry Date")

    # Company & Dept
    company_id = fields.Many2one(
        'res.company', string="Company",
        default=lambda self: self.env.company
    )
    company_name = fields.Char(string="Company")
    department_id = fields.Many2one('hr.department', string="Department", required=True)

    # Approvals - Make them required
    approval_1_id = fields.Many2one('res.users', string="Level 1 Approver", readonly=False, required=True)
    approval_2_id = fields.Many2one('res.users', string="Level 2 Approver", readonly=False)
    approval_3_id = fields.Many2one('res.users', string="Level 3 Approver", readonly=False)

    # Approval Dates
    approval_1_date = fields.Datetime(string="Level 1 Approval Date", readonly=True)
    approval_2_date = fields.Datetime(string="Level 2 Approval Date", readonly=True)
    approval_3_date = fields.Datetime(string="Level 3 Approval Date", readonly=True)
    rejection_date = fields.Datetime(string="Rejection Date", readonly=True)

    # Attachment
    attachment = fields.Binary(string="Attachment")
    attachment_name = fields.Char(string="Attachment Name")

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('level1', 'Waiting Level 1 Approval'),
        ('level2', 'Waiting Level 2 Approval'),
        ('level3', 'Waiting Level 3 Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='draft', tracking=True)

    # Constraints
    _sql_constraints = [
        ('coupon_code_unique', 'UNIQUE(coupon_code)', 'Coupon code must be unique!'),
    ]

    # @api.constrains('coupon_value')
    # def _check_coupon_value(self):
    #     for record in self:
    #         if record.coupon_value <= 0:
    #             raise ValidationError("Coupon value must be greater than zero!")

    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        for record in self:
            if record.expiry_date and record.expiry_date < record.issue_date:
                raise ValidationError("Expiry date cannot be before issue date!")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'coupon.issue.sequence'
            ) or 'New'

        # Auto-set approvers from department
        if 'department_id' in vals and vals['department_id']:
            department = self.env['hr.department'].browse(vals['department_id'])
            if department.approver1 and 'approval_1_id' not in vals:
                vals['approval_1_id'] = department.approver1.id
            if department.approver2 and 'approval_2_id' not in vals:
                vals['approval_2_id'] = department.approver2.id
            if department.approver3 and 'approval_3_id' not in vals:
                vals['approval_3_id'] = department.approver3.id

        return super().create(vals)

    def write(self, vals):
        # Auto-update approvers when department changes
        if 'department_id' in vals and vals['department_id']:
            department = self.env['hr.department'].browse(vals['department_id'])
            vals['approval_1_id'] = department.approver1.id if department.approver1 else False
            vals['approval_2_id'] = department.approver2.id if department.approver2 else False
            vals['approval_3_id'] = department.approver3.id if department.approver3 else False

        return super().write(vals)

    # ----------------------------------
    # ONCHANGE LOGIC
    # ----------------------------------
    @api.onchange('customer_id')
    def _onchange_customer(self):
        if self.customer_id:
            self.mobile = self.customer_id.mobile
            self.address = self.customer_id.contact_address

    @api.onchange('department_id')
    def _onchange_department(self):
        if self.department_id:
            self.approval_1_id = self.department_id.approver1
            self.approval_2_id = self.department_id.approver2
            self.approval_3_id = self.department_id.approver3

    # ----------------------------------
    # BUTTON ACTIONS - SIMPLIFIED
    # ----------------------------------
    def action_submit(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError("Only draft records can be submitted!")

        # Check if approver is set
        if not self.approval_1_id:
            raise UserError("Level 1 Approver is not set. Please save the record first or select a valid department!")

        # Move to Level 1 approval
        self.write({
            'state': 'level1',
        })

        # Send notification
        if self.approval_1_id:
            self.activity_schedule(
                activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                summary='Coupon Issue Approval Required - Level 1',
                note=f'Please review and approve/reject coupon issue {self.name}',
                user_id=self.approval_1_id.id,
            )

        return True

    def action_approve_level1(self):
        self.ensure_one()
        if self.state != 'level1':
            raise UserError("This record is not waiting for Level 1 approval!")

        if self.env.user != self.approval_1_id:
            raise UserError("You are not authorized to approve this level!")

        # Check if there's a level 2 approver
        if self.approval_2_id:
            self.write({
                'state': 'level2',
                'approval_1_date': fields.Datetime.now(),
            })
            # Notify level 2 approver
            self.activity_schedule(
                activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                summary='Coupon Issue Approval Required - Level 2',
                note=f'Please review and approve/reject coupon issue {self.name}',
                user_id=self.approval_2_id.id,
            )
        else:
            # No level 2 approver, approve directly
            self.write({
                'state': 'approved',
                'approval_1_date': fields.Datetime.now(),
            })

        return True

    def action_approve_level2(self):
        self.ensure_one()
        if self.state != 'level2':
            raise UserError("This record is not waiting for Level 2 approval!")

        if self.env.user != self.approval_2_id:
            raise UserError("You are not authorized to approve this level!")

        # Check if there's a level 3 approver
        if self.approval_3_id:
            self.write({
                'state': 'level3',
                'approval_2_date': fields.Datetime.now(),
            })
            # Notify level 3 approver
            self.activity_schedule(
                activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                summary='Coupon Issue Approval Required - Level 3',
                note=f'Please review and approve/reject coupon issue {self.name}',
                user_id=self.approval_3_id.id,
            )
        else:
            # No level 3 approver, approve directly
            self.write({
                'state': 'approved',
                'approval_2_date': fields.Datetime.now(),
            })

        return True

    def action_approve_level3(self):
        self.ensure_one()
        if self.state != 'level3':
            raise UserError("This record is not waiting for Level 3 approval!")

        if self.env.user != self.approval_3_id:
            raise UserError("You are not authorized to approve this level!")

        self.write({
            'state': 'approved',
            'approval_3_date': fields.Datetime.now(),
        })
        return True

    def action_reject(self):
        self.ensure_one()
        if self.state not in ['level1', 'level2', 'level3']:
            raise UserError("Only records in approval process can be rejected!")

        # Determine which approver should be rejecting
        current_approver = None
        if self.state == 'level1':
            current_approver = self.approval_1_id
        elif self.state == 'level2':
            current_approver = self.approval_2_id
        elif self.state == 'level3':
            current_approver = self.approval_3_id

        if self.env.user != current_approver:
            raise UserError("You are not authorized to reject this request!")

        self.write({
            'state': 'rejected',
            'rejection_date': fields.Datetime.now(),
        })
        return True

    def action_reset_to_draft(self):
        self.ensure_one()
        if self.state not in ['rejected', 'approved']:
            raise UserError("Only approved or rejected records can be reset to draft!")

        # Check if user has permission (admin or creator)
        if not (self.env.user.has_group('base.group_system') or self.create_uid == self.env.user):
            raise UserError("You are not authorized to reset this record!")

        self.write({
            'state': 'draft',
            'rejection_date': False,
            'approval_1_date': False,
            'approval_2_date': False,
            'approval_3_date': False,
        })
        return True

    # ----------------------------------
    # COMPUTE METHODS FOR BUTTON VISIBILITY
    # ----------------------------------
    def _compute_show_buttons(self):
        """Compute which buttons should be visible to current user"""
        for record in self:
            record.show_submit_button = record.state == 'draft'
            record.show_approve_level1_button = (
                    record.state == 'level1' and
                    self.env.user == record.approval_1_id
            )
            record.show_approve_level2_button = (
                    record.state == 'level2' and
                    self.env.user == record.approval_2_id
            )
            record.show_approve_level3_button = (
                    record.state == 'level3' and
                    self.env.user == record.approval_3_id
            )
            record.show_reject_button = (
                    record.state in ['level1', 'level2', 'level3'] and
                    (
                            (record.state == 'level1' and self.env.user == record.approval_1_id) or
                            (record.state == 'level2' and self.env.user == record.approval_2_id) or
                            (record.state == 'level3' and self.env.user == record.approval_3_id)
                    )
            )
            record.show_reset_button = (
                    record.state in ['rejected', 'approved'] and
                    (self.env.user.has_group('base.group_system') or record.create_uid == self.env.user)
            )

    # Button visibility fields
    show_submit_button = fields.Boolean(compute='_compute_show_buttons')
    show_approve_level1_button = fields.Boolean(compute='_compute_show_buttons')
    show_approve_level2_button = fields.Boolean(compute='_compute_show_buttons')
    show_approve_level3_button = fields.Boolean(compute='_compute_show_buttons')
    show_reject_button = fields.Boolean(compute='_compute_show_buttons')
    show_reset_button = fields.Boolean(compute='_compute_show_buttons')

    def name_get(self):
        """Display both sequence and coupon code in the dropdown"""
        result = []
        for record in self:
            name = f"{record.name} - {record.coupon_code}"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        """Search by both sequence (name) and coupon code"""
        if args is None:
            args = []

        # Search by sequence (name) OR coupon code
        domain = args + ['|', ('name', operator, name), ('coupon_code', operator, name)]

        # Only show approved coupons for redeem
        if self._context.get('default_state') == 'approved' or 'approved' in str(args):
            domain = args + ['|', ('name', operator, name), ('coupon_code', operator, name), ('state', '=', 'approved')]

        return self._search(domain, limit=limit, access_rights_uid=name_get_uid)

    has_attachment = fields.Boolean(compute='_compute_has_attachment')

    # Add this compute method
    def _compute_has_attachment(self):
        for record in self:
            record.has_attachment = bool(record.attachment)

    # Add this method to view attachment
    def action_view_attachment(self):
        self.ensure_one()
        if not self.attachment:
            raise UserError("No attachment found!")
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/coupon.issue/%s/attachment/%s' % (self.id, self.attachment_name),
            'target': 'new',
        }

    def action_export_excel(self):
        """Export coupons to Excel"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/coupon/export/excel/%s' % self.id,
            'target': 'self',
        }


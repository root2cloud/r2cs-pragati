from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class CouponRedeem(models.Model):
    _name = 'coupon.redeem'
    _description = 'Coupon Redeem'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'redeem_date desc'

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )

    # Link to original coupon issue
    coupon_issue_id = fields.Many2one(
        'coupon.issue',
        string="Coupon Reference",
        required=True,
        domain=lambda self: self._get_available_coupons_domain()
    )
    no_of_persons = fields.Integer(
        string="Number of Persons",
        default=1,
        required=True,
        help="Number of persons this coupon redemption applies to"
    )

    # Search by coupon code field
    coupon_code_search = fields.Char(
        string="Search by Coupon Code",
        help="Enter coupon code to search and auto-fill details"
    )

    # Customer Info (auto-filled from coupon issue)
    customer_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    mobile = fields.Char(string="Mobile Number", readonly=True)
    address = fields.Text(string="Address", readonly=True)

    # Coupon Details (auto-filled from coupon issue)
    coupon_code = fields.Char(string="Coupon Code", readonly=True)
    coupon_value = fields.Float(string="Coupon Value", readonly=True)
    issue_date = fields.Date(string="Issue Date", readonly=True)
    expiry_date = fields.Date(string="Expiry Date", readonly=True)

    # Company & Dept
    company_id = fields.Many2one('res.company', string="Company", readonly=True)
    company_name = fields.Char(string="Company", readonly=True)
    department_id = fields.Many2one('hr.department', string="Department", readonly=True)
    designation = fields.Char(string="Coupon Reedem Designation")
    coupon_redeem = fields.Char(string="Coupon Reedemeed BY")
    mobile_number = fields.Char(string="Coupon Reedemeed Mobile Number")
    no_of_adults = fields.Integer(
        string="No. of Adults",
        default=0
    )
    no_of_children = fields.Integer(
        string="No. of Children",
        default=0
    )

    # Redeem Details
    redeem_date = fields.Date(
        string="Redeem Date",
        default=fields.Date.context_today,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    redeem_by = fields.Many2one(
        'res.users',
        string="Redeemed By",
        default=lambda self: self.env.user,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    # New Remarks field
    remarks = fields.Text(
        string="Remarks",
        help="Additional remarks or comments about the redemption"
    )

    redeem_notes = fields.Text(string="Redeem Notes")

    # Attachment
    attachment = fields.Binary(string="Attachment")
    attachment_name = fields.Char(string="Attachment Name")

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('redeemed', 'Redeemed'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)

    # Constraints
    @api.constrains('coupon_issue_id')
    def _check_coupon_not_redeemed(self):
        """Check that coupon is not already redeemed"""
        for record in self:
            if record.coupon_issue_id:
                # Check if this coupon has been redeemed before
                existing_redeem = self.search([
                    ('coupon_issue_id', '=', record.coupon_issue_id.id),
                    ('state', '=', 'redeemed'),
                    ('id', '!=', record.id)
                ])
                if existing_redeem:
                    raise ValidationError(
                        f"Coupon '{record.coupon_issue_id.coupon_code}' has already been redeemed!"
                    )

    @api.constrains('expiry_date')
    def _check_coupon_expiry(self):
        """Check that coupon is not expired"""
        for record in self:
            if record.expiry_date and record.expiry_date < fields.Date.today():
                raise ValidationError("Cannot redeem an expired coupon!")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'coupon.redeem.sequence'
            ) or 'New'

        # If coupon issue is specified, auto-fill other fields
        if 'coupon_issue_id' in vals and vals['coupon_issue_id']:
            coupon_issue = self.env['coupon.issue'].browse(vals['coupon_issue_id'])

            # Auto-fill all fields from coupon issue
            auto_fields = [
                'customer_id', 'mobile', 'address', 'coupon_code',
                'coupon_value', 'issue_date', 'expiry_date', 'company_id',
                'company_name', 'department_id'
            ]

            for field in auto_fields:
                if hasattr(coupon_issue, field):
                    field_value = getattr(coupon_issue, field)
                    if isinstance(field_value, models.Model):
                        vals[field] = field_value.id if field_value else False
                    else:
                        vals[field] = field_value

        return super().create(vals)

    # ----------------------------------
    # ONCHANGE LOGIC
    # ----------------------------------
    @api.onchange('coupon_code_search')
    def _onchange_coupon_code_search(self):
        """Search and auto-fill when coupon code is entered"""
        if self.coupon_code_search and not self.coupon_issue_id:
            # Search for approved coupon with this code
            coupon_issue = self.env['coupon.issue'].search([
                ('coupon_code', '=', self.coupon_code_search),
                ('state', '=', 'approved')
            ], limit=1)

            if coupon_issue:
                self.coupon_issue_id = coupon_issue
                self._onchange_coupon_issue()
            else:
                warning = {
                    'title': 'Coupon Not Found',
                    'message': f"No approved coupon found with code '{self.coupon_code_search}'."
                }
                return {'warning': warning}

        # Clear the search field after use
        self.coupon_code_search = False

    @api.onchange('coupon_issue_id')
    def _onchange_coupon_issue(self):
        """Auto-fill all fields when coupon issue is selected"""
        if self.coupon_issue_id:
            # Fill all fields from the selected coupon issue
            self.customer_id = self.coupon_issue_id.customer_id
            self.mobile = self.coupon_issue_id.mobile
            self.address = self.coupon_issue_id.address
            self.coupon_code = self.coupon_issue_id.coupon_code
            self.coupon_value = self.coupon_issue_id.coupon_value
            self.issue_date = self.coupon_issue_id.issue_date
            self.expiry_date = self.coupon_issue_id.expiry_date
            self.company_id = self.coupon_issue_id.company_id
            self.company_name = self.coupon_issue_id.company_name
            self.department_id = self.coupon_issue_id.department_id
            # self.designation = self.coupon_issue_id.designation

            # Check if coupon is already redeemed
            existing_redeem = self.search([
                ('coupon_issue_id', '=', self.coupon_issue_id.id),
                ('state', '=', 'redeemed')
            ], limit=1)

            if existing_redeem:
                warning = {
                    'title': 'Coupon Already Redeemed!',
                    'message': f'This coupon has already been redeemed on {existing_redeem.redeem_date}.'
                }
                return {'warning': warning}

            # Check if coupon is expired
            if self.expiry_date and self.expiry_date < fields.Date.today():
                warning = {
                    'title': 'Coupon Expired!',
                    'message': 'This coupon has expired and cannot be redeemed.'
                }
                return {'warning': warning}

    # ----------------------------------
    # BUTTON ACTIONS
    # ----------------------------------
    def action_redeem(self):
        """Mark the coupon as redeemed"""
        for record in self:
            if record.state != 'draft':
                raise UserError("Only draft records can be redeemed!")

            if not record.coupon_issue_id:
                raise UserError("Please select a coupon first!")

            # Check if coupon is expired
            if record.expiry_date and record.expiry_date < fields.Date.today():
                raise UserError("Cannot redeem an expired coupon!")

            # Check if coupon is already redeemed
            existing_redeem = self.search([
                ('coupon_issue_id', '=', record.coupon_issue_id.id),
                ('state', '=', 'redeemed'),
                ('id', '!=', record.id)
            ], limit=1)

            if existing_redeem:
                raise UserError(f"This coupon was already redeemed on {existing_redeem.redeem_date}!")

            # Mark as redeemed
            record.write({
                'state': 'redeemed',
                'redeem_date': fields.Date.today(),
                'redeem_by': self.env.user.id,
            })

            # Create activity/log
            record.message_post(
                body=f"Coupon redeemed by {self.env.user.name} on {fields.Date.today()}\nRemarks: {record.remarks or 'No remarks'}",
                subject="Coupon Redeemed"
            )
        return True

    def action_cancel(self):
        """Cancel the redeem record"""
        for record in self:
            if record.state not in ['draft', 'redeemed']:
                raise UserError("Cannot cancel this record!")

            record.write({
                'state': 'cancelled',
            })

            record.message_post(
                body=f"Redeem cancelled by {self.env.user.name}\nRemarks: {record.remarks or 'No remarks'}",
                subject="Redeem Cancelled"
            )
        return True

    def action_reset_to_draft(self):
        """Reset cancelled record to draft"""
        for record in self:
            if record.state != 'cancelled':
                raise UserError("Only cancelled records can be reset to draft!")

            record.write({
                'state': 'draft',
            })
        return True

    # ----------------------------------
    # COMPUTE METHODS FOR BUTTON VISIBILITY
    # ----------------------------------
    def _compute_show_buttons(self):
        """Compute which buttons should be visible to current user"""
        for record in self:
            record.show_redeem_button = record.state == 'draft'
            record.show_cancel_button = record.state in ['draft', 'redeemed']
            record.show_reset_button = record.state == 'cancelled'

    # Button visibility fields
    show_redeem_button = fields.Boolean(compute='_compute_show_buttons')
    show_cancel_button = fields.Boolean(compute='_compute_show_buttons')
    show_reset_button = fields.Boolean(compute='_compute_show_buttons')

    def _compute_redeemed_coupon_ids(self):
        """Get IDs of all coupons that have been redeemed"""
        redeemed_records = self.env['coupon.redeem'].search([
            ('state', '=', 'redeemed')
        ])
        self.redeemed_coupon_ids = redeemed_records.mapped('coupon_issue_id.id')

    redeemed_coupon_ids = fields.Many2many(
        'coupon.issue',
        string="Redeemed Coupons",
        compute='_compute_redeemed_coupon_ids'
    )

    def _get_available_coupons_domain(self):
        """Get domain for available coupons (not redeemed)"""
        # Get all coupon issue IDs that have been redeemed
        redeemed_records = self.env['coupon.redeem'].search([
            ('state', '=', 'redeemed')
        ])
        redeemed_coupon_ids = redeemed_records.mapped('coupon_issue_id.id')

        # Return domain to exclude redeemed coupons
        return [('state', '=', 'approved'), ('id', 'not in', redeemed_coupon_ids)]


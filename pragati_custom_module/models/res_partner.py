from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ============================================
    # FIELDS
    # ============================================

    approver_1 = fields.Many2one(
        "res.users",
        string="Approver 1",
        readonly=True,
        help="First approver for vendor approval workflow (Vendors only)"
    )
    approver_2 = fields.Many2one(
        "res.users",
        string="Approver 2",
        readonly=True,
        help="Second approver for vendor approval workflow (Vendors only)"
    )

    is_current_user_approver = fields.Boolean(
        compute="_compute_is_current_user_approver",
        store=False,
        help="Check if current user is a vendor approver (Vendors only)"
    )

    state = fields.Selection([
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='waiting_approval', readonly=True, string="Approval Status",
       help="Approval workflow state - VENDORS ONLY")

    l10n_in_pan = fields.Char(
        required=True,
        help="PAN number for Indian vendors"
    )

    # ============================================
    # CREATE METHOD - ALL WORKFLOW HERE
    # ============================================

    @api.model_create_multi
    def create(self, vals_list):
        approver_1 = self.env['res.users'].search(
            [('login', '=', "anilkumar@pragatigroup.com")], limit=1
        )
        approver_2 = self.env['res.users'].search(
            [('login', '=', "hanumantharao.p@pragatigroup.com")], limit=1
        )

        for vals in vals_list:
            # Check for duplicate vendor names ONLY
            if vals.get('name'):
                existing_vendor = self.search([
                    ('name', '=', vals['name']),
                    ('supplier_rank', '>', 0)  # Only check vendors, not customers
                ], limit=1)
                if existing_vendor:
                    raise ValidationError(
                        f"Vendor with name '{vals['name']}' already exists. "
                        f"Please use a unique vendor name."
                    )

            # Auto-format PAN on create
            if 'l10n_in_pan' in vals and vals['l10n_in_pan']:
                vals['l10n_in_pan'] = vals['l10n_in_pan'].replace(' ', '').upper()

            # ===== VENDOR-ONLY WORKFLOW =====
            is_vendor = vals.get('supplier_rank', 0) > 0 or self.env.context.get('default_supplier_rank', 0) > 0

            if is_vendor:
                vals['approver_1'] = approver_1.id if approver_1 else False
                vals['approver_2'] = approver_2.id if approver_2 else False
                vals['state'] = 'waiting_approval'  # Directly to waiting approval
                vals['active'] = False  # Archive immediately
                _logger.info(f"✓ Vendor '{vals.get('name')}' created in WAITING APPROVAL (archived)")
            else:
                # For customers: directly active, no approval needed
                vals['state'] = 'approved'
                vals['active'] = True
                _logger.info(f"✓ Customer '{vals.get('name')}' created APPROVED")

        # Create partners
        partners = super(ResPartner, self).create(vals_list)

        # NOW: For vendors, create payable accounts and send activities
        for partner in partners:
            if partner.supplier_rank > 0:
                # Create payable account
                try:
                    partner._create_partner_payable_account()
                    _logger.info(f"✓ Payable account created for '{partner.name}'")
                except Exception as e:
                    _logger.error(f"Payable account creation failed: {str(e)}")

                # Create activities for approvers
                for approver in [partner.approver_1, partner.approver_2]:
                    if approver:
                        self.env['mail.activity'].create({
                            'res_model_id': self.env['ir.model']._get_id('res.partner'),
                            'res_id': partner.id,
                            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                            'summary': f"Vendor Approval: {partner.name}",
                            'note': f"<p>Please review and approve vendor: <strong>{partner.name}</strong></p>",
                            'user_id': approver.id,
                        })
                        _logger.info(f"✓ Activity created for {approver.name}")

        return partners

    # ============================================
    # COMPUTE METHODS
    # ============================================

    @api.depends()
    def _compute_is_current_user_approver(self):
        """Compute if current user is an approver"""
        user = self.env.user
        for rec in self:
            if rec.supplier_rank > 0:
                rec.is_current_user_approver = user in (rec.approver_1 | rec.approver_2)
            else:
                rec.is_current_user_approver = False

    # ============================================
    # VALIDATION METHODS
    # ============================================

    def _check_is_vendor(self):
        """Ensure this is a vendor record"""
        self.ensure_one()
        if self.supplier_rank <= 0:
            raise UserError("Action only available for vendors.")

    def _check_is_approver(self):
        """Ensure user is an approver"""
        self.ensure_one()
        if self.env.user not in (self.approver_1 | self.approver_2):
            raise UserError("You are not allowed to approve/reject.")

    # ============================================
    # APPROVAL ACTIONS
    # ============================================

    def action_approve(self):
        """Approve vendor - Unarchive + Approved"""
        self.ensure_one()
        self._check_is_vendor()
        self._check_is_approver()

        if self.state != 'waiting_approval':
            raise UserError("Can only approve vendors waiting for approval.")

        if self.activity_ids:
            self.activity_ids.action_done()

        # Unarchive and approve
        self.with_context(bypass_vendor_lock=True).write({
            'active': True,
            'state': 'approved'
        })
        self.env.cr.commit()

        _logger.info(f"✓ Vendor '{self.name}' APPROVED and unarchived")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Approved',
                'message': f"Vendor '{self.name}' approved and now active!",
                'type': 'success',
                'sticky': False,
            }
        }

    def action_reject(self):
        """Reject vendor - Delete payable account, keep archived"""
        self.ensure_one()
        self._check_is_vendor()
        self._check_is_approver()

        if self.state in ('approved', 'rejected'):
            raise UserError("Already processed.")

        if self.activity_ids:
            self.activity_ids.action_done()

        # Delete payable account
        if self.property_account_payable_id:
            try:
                self.property_account_payable_id.sudo().unlink()
                _logger.info(f"✓ Payable account deleted for rejected vendor")
            except Exception as e:
                _logger.warning(f"Could not delete account: {str(e)}")

        # Reject
        self.with_context(bypass_vendor_lock=True).write({
            'state': 'rejected',
            'property_account_payable_id': False
        })

        _logger.info(f"✓ Vendor '{self.name}' REJECTED")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Rejected',
                'message': f"Vendor '{self.name}' has been rejected.",
                'type': 'info',
                'sticky': False,
            }
        }

    # ============================================
    # PAYABLE ACCOUNT CREATION
    # ============================================

    def _create_partner_payable_account(self):
        """Create payable account on vendor creation"""
        self.ensure_one()

        company = self.company_id or self.env.company

        last_account = self.env['account.account'].search(
            [('company_id', '=', company.id)],
            order='code desc',
            limit=1
        )

        next_code_num = int(last_account.code) + 1 if last_account and last_account.code.isdigit() else 100001

        while True:
            next_code = str(next_code_num).zfill(6)

            existing = self.env['account.account'].search([
                ('code', '=', next_code),
                ('company_id', '=', company.id)
            ], limit=1)

            if not existing:
                try:
                    payable_account = self.env['account.account'].sudo().create({
                        'code': next_code,
                        'name': self.name,
                        'account_type': 'liability_payable',
                        'reconcile': True,
                        'company_id': company.id,
                    })

                    self.sudo().write({'property_account_payable_id': payable_account.id})
                    _logger.info(f"✓ Created payable account {next_code} for {self.name}")
                    return

                except Exception as e:
                    _logger.warning(f"Failed to create {next_code}: {e}")
                    next_code_num += 1
                    continue

            next_code_num += 1

    # ============================================
    # PAN CONSTRAINTS
    # ============================================

    @api.constrains('l10n_in_pan')
    def _check_pan_unique(self):
        """Ensure PAN is unique"""
        for rec in self:
            if rec.l10n_in_pan:
                pan = rec.l10n_in_pan.replace(' ', '').upper()
                dup = self.search([('l10n_in_pan', '=', pan), ('id', '!=', rec.id)], limit=1)
                if dup:
                    raise ValidationError(f'PAN already exists: {dup.name}')

    # ============================================
    # WRITE METHOD
    # ============================================

    def write(self, vals):
        """Auto-format PAN"""
        if 'l10n_in_pan' in vals and vals['l10n_in_pan']:
            vals['l10n_in_pan'] = vals['l10n_in_pan'].replace(' ', '').upper()

        # Block direct editing of approved/rejected vendors
        if not self.env.context.get('bypass_vendor_lock'):
            for rec in self:
                if rec.supplier_rank > 0 and rec.state == 'rejected':
                    if any(f in vals for f in ['name', 'l10n_in_pan']):
                        raise UserError("Cannot edit rejected vendors.")

        return super(ResPartner, self).write(vals)

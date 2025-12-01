from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ============================================
    # FIELDS
    # ============================================

    approver_1 = fields.Many2one("res.users", string="Approver 1", readonly=True)
    approver_2 = fields.Many2one("res.users", string="Approver 2", readonly=True)

    is_current_user_approver = fields.Boolean(
        # compute="_compute_is_current_user_approver",
        store=False
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', readonly=True, string="Approval Status")

    l10n_in_pan = fields.Char(
        required=True
    )

    # # ============================================
    # # CREATE METHOD
    # # ============================================
    #
    # @api.model_create_multi
    # def create(self, vals_list):
    #     approver_1 = self.env['res.users'].search([('login', '=', "anilkumar@pragatigroup.com")], limit=1)
    #     approver_2 = self.env['res.users'].search([('login', '=', "hanumantharao.p@pragatigroup.com")], limit=1)
    #
    #     for vals in vals_list:
    #         if vals.get('name'):
    #             existing_partner = self.search([('name', '=', vals['name'])], limit=1)
    #             if existing_partner:
    #                 raise ValidationError(
    #                     f"Contact with name '{vals['name']}' already exists. "
    #                     f"Please use a unique name."
    #                 )
    #
    #         vals['approver_1'] = approver_1.id if approver_1 else False
    #         vals['approver_2'] = approver_2.id if approver_2 else False
    #         vals['state'] = 'draft'
    #         vals['active'] = False
    #
    #         # Auto-format PAN on create
    #         if 'l10n_in_pan' in vals and vals['l10n_in_pan']:
    #             vals['l10n_in_pan'] = vals['l10n_in_pan'].replace(' ', '').upper()
    #
    #     partners = super(ResPartner, self).create(vals_list)
    #     return partners
    #
    # # ============================================
    # # COMPUTE METHODS
    # # ============================================
    #
    # @api.depends()
    # def _compute_is_current_user_approver(self):
    #     user = self.env.user
    #     for rec in self:
    #         rec.is_current_user_approver = user in (rec.approver_1 | rec.approver_2)
    #
    # # ============================================
    # # APPROVAL ACTIONS
    # # ============================================
    #
    # def _check_is_approver(self):
    #     self.ensure_one()
    #     if self.env.user not in (self.approver_1 | self.approver_2):
    #         raise UserError("You are not allowed to approve or reject this contact.")
    #
    # def action_submit(self):
    #     """Submit contact for approval"""
    #     self.ensure_one()
    #
    #     if self.state != 'draft':
    #         raise UserError("You can only submit from Draft state.")
    #
    #     self.state = 'waiting_approval'
    #
    #     # Create mail activity for approver_1
    #     if self.approver_1:
    #         activity_1 = self.env['mail.activity'].create({
    #             'res_model_id': self.env['ir.model']._get_id('res.partner'),
    #             'res_id': self.id,
    #             'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
    #             'summary': f"Contact Approval: {self.name}",
    #             'note': f"<p>Please review and approve the contact: <strong>{self.name}</strong></p>",
    #             'user_id': self.approver_1.id,
    #         })
    #         _logger.info(
    #             f"✓ Activity {activity_1.id} created for {self.approver_1.name} (User ID: {self.approver_1.id})")
    #
    #     # Create mail activity for approver_2
    #     if self.approver_2:
    #         activity_2 = self.env['mail.activity'].create({
    #             'res_model_id': self.env['ir.model']._get_id('res.partner'),
    #             'res_id': self.id,
    #             'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
    #             'summary': f"Contact Approval: {self.name}",
    #             'note': f"<p>Please review and approve the contact: <strong>{self.name}</strong></p>",
    #             'user_id': self.approver_2.id,
    #         })
    #         _logger.info(
    #             f"✓ Activity {activity_2.id} created for {self.approver_2.name} (User ID: {self.approver_2.id})")
    #
    #     _logger.info(f"Contact '{self.name}' (ID: {self.id}) submitted for approval")
    #
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': 'Submitted',
    #             'message': f"Contact '{self.name}' submitted for approval. Check your Activities!",
    #             'type': 'success',
    #             'sticky': True,
    #         }
    #     }
    #
    # def action_approve(self):
    #     self.ensure_one()
    #     self._check_is_approver()
    #
    #     # Can only approve if in waiting_approval state
    #     if self.state != 'waiting_approval':
    #         raise UserError("You can only approve contacts that are waiting for approval.")
    #
    #     if self.activity_ids:
    #         self.activity_ids.action_done()
    #
    #     self.write({'active': True, 'state': 'approved'})
    #     self.env.cr.commit()
    #
    #     # Create payable account
    #     try:
    #         self._create_partner_payable_account()
    #         message = f"Contact '{self.name}' approved and payable account created!"
    #         msg_type = 'success'
    #     except Exception as e:
    #         _logger.error(f"Account creation failed: {str(e)}")
    #         message = f"Contact approved, but account creation failed: {str(e)}"
    #         msg_type = 'warning'
    #
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': 'Approved',
    #             'message': message,
    #             'type': msg_type,
    #             'sticky': False,
    #         }
    #     }
    #
    # def action_reject(self):
    #     self.ensure_one()
    #     self._check_is_approver()
    #
    #     if self.state in ('approved', 'rejected'):
    #         raise UserError("This record is already processed.")
    #
    #     if self.activity_ids:
    #         self.activity_ids.action_done()
    #
    #     self.write({'active': False, 'state': 'rejected'})
    #
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': 'Rejected',
    #             'message': f"Contact '{self.name}' has been rejected.",
    #             'type': 'info',
    #             'sticky': False,
    #         }
    #     }
    #
    # # ============================================
    # # PAYABLE ACCOUNT CREATION (SIMPLE)
    # # ============================================
    #
    # def _create_partner_payable_account(self):
    #     """MUST create account - will keep trying until success"""
    #     self.ensure_one()
    #
    #     company = self.company_id or self.env.company
    #
    #     # Fetch ONLY the last account by code (descending)
    #     last_account = self.env['account.account'].search(
    #         [('company_id', '=', company.id)],
    #         order='code desc',
    #         limit=1
    #     )
    #
    #     # Get starting point
    #     if last_account and last_account.code and last_account.code.isdigit():
    #         next_code_num = int(last_account.code) + 1
    #     else:
    #         next_code_num = 100001
    #
    #     # INFINITE loop - keep trying until we create successfully
    #     while True:
    #         # Pad with zeros at the END to make it 6 digits
    #         next_code_str = str(next_code_num)
    #         if len(next_code_str) < 6:
    #             next_code = next_code_str + '0' * (6 - len(next_code_str))
    #         else:
    #             next_code = next_code_str
    #
    #         # Check if this code already exists
    #         existing = self.env['account.account'].search([
    #             ('code', '=', next_code),
    #             ('company_id', '=', company.id)
    #         ], limit=1)
    #
    #         if not existing:
    #             # Code is unique, try to create
    #             try:
    #                 payable_account = self.env['account.account'].sudo().create({
    #                     'code': next_code,
    #                     'name': self.name,
    #                     'account_type': 'liability_payable',
    #                     'reconcile': True,
    #                     'company_id': company.id,
    #                 })
    #
    #                 # Success! Assign to partner and exit
    #                 self.sudo().write({'property_account_payable_id': payable_account.id})
    #                 _logger.info(f"✓ Created account {next_code} - {self.name}")
    #                 return
    #
    #             except Exception as e:
    #                 # Creation failed (maybe race condition), try next code
    #                 _logger.warning(f"Failed to create code {next_code}: {e}")
    #                 next_code_num += 1
    #                 continue
    #
    #         # Code exists, try next one
    #         next_code_num += 1
    #
    # # ============================================
    # # PAN FIELD CONSTRAINTS
    # # ============================================
    #
    # @api.constrains('l10n_in_pan')
    # def _check_pan_unique(self):
    #     for rec in self:
    #         if rec.l10n_in_pan:
    #             # Format the PAN
    #             pan = rec.l10n_in_pan.replace(' ', '').upper()
    #
    #             # Check for duplicates
    #             duplicate = self.search([
    #                 ('l10n_in_pan', '=', pan),
    #                 ('id', '!=', rec.id)
    #             ], limit=1)
    #
    #             if duplicate:
    #                 raise ValidationError(
    #                     f'PAN Number already exists! '
    #                     f'This PAN is already assigned to: {duplicate.name}'
    #                 )
    #
    # # ============================================
    # # WRITE METHOD
    # # ============================================
    #
    # def write(self, vals):
    #     # Auto-format PAN on write
    #     if 'l10n_in_pan' in vals and vals['l10n_in_pan']:
    #         vals['l10n_in_pan'] = vals['l10n_in_pan'].replace(' ', '').upper()
    #     return super(ResPartner, self).write(vals)

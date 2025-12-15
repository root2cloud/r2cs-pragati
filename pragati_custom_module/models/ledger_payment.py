from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from decimal import Decimal

READONLY_STATES = {
    'post': [('readonly', True)],
    'recocile': [('readonly', True)],
    'cancel': [('readonly', True)],
}


class LedgerPayment(models.Model):
    _inherit = "ledger.payment"

    def _get_default_category_id(self):
        domain = [('name', '=', "Bank Receipt")]
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
                domain = [('name', '=', "Bank Receipt"), ('company_id', '=', default_company.id)]
                category_type = self.env['approval.category'].search(domain, limit=1)
        if category_type:
            return category_type.id
        return False

    def _get_default_user_id(self):
        domain = [('name', '=', "Managing Director"), ('login', '=', 'ajay@pragatigroup.com')]
        user_type = self.env['res.users'].search(domain, limit=1)
        if user_type:
            return user_type.id

    approval_level_1 = fields.Many2one('res.users', string='Approver Level 1', domain="[('share', '=', False)]",
                                       default=_get_default_user_id, states=READONLY_STATES)
    approval_level_2 = fields.Many2one('res.users', string='Approver Level 2', domain="[('share', '=', False)]",
                                       states=READONLY_STATES)
    approval_level_3 = fields.Many2one('res.users', string='Approver Level 3', domain="[('share', '=', False)]",
                                       states=READONLY_STATES, )
    approval_id = fields.Many2one('approval.request', string='Approval ID')

    request_owner_id = fields.Many2one('res.users', string="Request Owner",
                                       check_company=True, domain="[('company_ids', 'in', company_id)]",
                                       default=lambda self: self.env.user)
    category_id = fields.Many2one('approval.category', string='category', default=_get_default_category_id)
    approve_status = fields.Selection([('pending', 'Pending'), ('approve', 'Approved')],
                                      string='Approval Status', default='pending')

    is_approval_user = fields.Boolean('res.users', compute="_compute_is_approval_user")

    def _compute_is_approval_user(self):
        for lp in self:
            approver_list = []

            if lp.approval_level_1:
                approver_list.append(lp.approval_level_1.id)
            if lp.approval_level_2:
                approver_list.append(lp.approval_level_2.id)
            if lp.approval_level_3:
                approver_list.append(lp.approval_level_3.id)
            if lp.env.user.id in approver_list:
                lp.is_approval_user = True
            else:
                lp.is_approval_user = False

    def approve_bank_receipt(self):
        self.write({'state': 'approve'})

    def send_for_approval(self):
        self.write({'state': 'submit'})
        approver_list = []

        if self.approval_level_1:
            approver_list.append(self.approval_level_1.id)
        if self.approval_level_2:
            approver_list.append(self.approval_level_2.id)
        if self.approval_level_3:
            approver_list.append(self.approval_level_3.id)
        if not approver_list:
            raise ValidationError(_('Please Assign atleast one approver'))

        # for record in self:
        #
        #     if not record.request_owner_id or not record.category_id:
        #         raise UserError("Please fill in the required fields: Purchase No, Request Owner, and Category")
        #     # if record.reuse_button:
        #     #     raise ValidationError(_("The record is already Submitted, Please check the Account Approval Id"))
        #
        #     # Create an approval request
        #     approval_request = record.env['approval.request'].create({
        #         'request_owner_id': record.request_owner_id.id,
        #         'category_id': record.category_id.id,
        #         'ledger_payment_id': record.id,
        #     })
        #
        #     # Update the account_approval_id with the latest approval request ID
        #     record.write({'approval_id': approval_request.id})
        #     approver_values = []
        #     for line in approver_list:
        #         approver_values.append((0, 0, {
        #             'user_id': line,
        #             'required': True,
        #         }))
        #     # Link approval request to the approval approvers
        #     approval_request.write({
        #         'approver_ids': approver_values,
        #     })
        #
        #     approval_request.action_confirm()
        return True

    @api.depends('amount')
    def _compute_amount_in_words(self):
        for order in self:
            if order.amount:
                amount_words = order.currency_id.amount_to_text(order.amount)
                order.amount_in_words = amount_words.title()  # Capitalize the first letter
            else:
                order.amount_in_words = ""

    @api.constrains("amount", "source_acc")
    def _check_source_account_balance(self):

        for record in self:
            if record.source_acc and record.amount:
                AccountMoveLine = self.env['account.move.line']
                domain = [
                    ('account_id', '=', record.source_acc.id),
                    ('parent_state', '=', 'posted'),
                ]
                # SUM(debit) - SUM(credit) for this account
                results = AccountMoveLine.read_group(domain, ['debit', 'credit'], [])
                debit = Decimal(results[0]['debit']) if results and results[0]['debit'] else Decimal(0)
                credit = Decimal(results[0]['credit']) if results and results[0]['credit'] else Decimal(0)
                balance = debit - credit
                amount = Decimal(str(record.amount))

                if balance < amount:
                    raise ValidationError(
                        f"Insufficient balance in source account '{record.source_acc.name}'.\n\n"
                        f"Current Balance: {balance:,.2f}\n"
                        f"Requested Transfer: {amount:,.2f}")

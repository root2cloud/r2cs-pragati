from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from decimal import Decimal

READONLY_STATES = {
    'submit': [('readonly', True)],
    'approve': [('readonly', True)],
    'post': [('readonly', True)],
    'recocile': [('readonly', True)],
    'cancel': [('readonly', True)],
}


class LedgerPayment(models.Model):
    _inherit = "ledger.payment"

    # --- NEW: Department Field ---
    department_id = fields.Many2one('hr.department', string="Department", states=READONLY_STATES)

    def _get_default_category_id(self):
        domain = [('name', '=', "Bank Receipt")]
        category_type = False
        company = self.env.company
        if company:
            domain += [('company_id', '=', company.id)]
            category_type = self.env['approval.category'].search(domain, limit=1)
        if not category_type:
            default_company = self.env['res.company'].search([], limit=1)
            if default_company:
                domain = [('name', '=', "Bank Receipt"), ('company_id', '=', default_company.id)]
                category_type = self.env['approval.category'].search(domain, limit=1)
        if category_type:
            return category_type.id
        return False

    # --- 1. TRACKING FIELDS (Who has approved?) ---
    l1_done = fields.Boolean(string="Level 1 Approved", default=False, copy=False)
    l2_done = fields.Boolean(string="Level 2 Approved", default=False, copy=False)
    l3_done = fields.Boolean(string="Level 3 Approved", default=False, copy=False)

    # --- EXISTING FIELDS (Preserved) ---
    # Note: Readonly behavior is enforced in XML using force_save="1" so onchange works
    approval_level_1 = fields.Many2one('res.users', string='Approver Level 1', domain="[('share', '=', False)]",
                                       states=READONLY_STATES)
    approval_level_2 = fields.Many2one('res.users', string='Approver Level 2', domain="[('share', '=', False)]",
                                       states=READONLY_STATES)
    approval_level_3 = fields.Many2one('res.users', string='Approver Level 3', domain="[('share', '=', False)]",
                                       states=READONLY_STATES)

    request_owner_id = fields.Many2one('res.users', string="Request Owner",
                                       check_company=True, domain="[('company_ids', 'in', company_id)]",
                                       default=lambda self: self.env.user)
    category_id = fields.Many2one('approval.category', string='category', default=_get_default_category_id)
    approve_status = fields.Selection([('pending', 'Pending'), ('approve', 'Approved')],
                                      string='Approval Status', default='pending')

    is_approval_user = fields.Boolean('Is Approval User', compute="_compute_is_approval_user")

    amount_in_words = fields.Char(string="Amount in Words", compute='_compute_amount_in_words')

    # --- NEW: Auto-fill Approvers from Department ---
    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            # Maps hr.department fields (approver1, etc.) to this model
            # Using the field names you confirmed: approver1, approver2, approver3
            self.approval_level_1 = self.department_id.approver1
            self.approval_level_2 = self.department_id.approver2
            self.approval_level_3 = self.department_id.approver3

    def _compute_is_approval_user(self):
        for lp in self:
            approver_list = []
            if lp.approval_level_1: approver_list.append(lp.approval_level_1.id)
            if lp.approval_level_2: approver_list.append(lp.approval_level_2.id)
            if lp.approval_level_3: approver_list.append(lp.approval_level_3.id)

            if lp.env.user.id in approver_list:
                lp.is_approval_user = True
            else:
                lp.is_approval_user = False

    # --- 3. UPDATED: Approve Logic (The "Checklist") ---
    # --- UPDATED: 2. Approve Logic (THE CHAIN REACTION) ---
    def approve_bank_receipt(self):
        self.ensure_one()
        current_user = self.env.user

        # --- A. Mark Current User as Done (FIXED LOGIC) ---
        # We use 'and not self.l1_done' so if L1 is finished, it skips to check L2

        if self.approval_level_1 == current_user and not self.l1_done:
            self.l1_done = True

        elif self.approval_level_2 == current_user and not self.l2_done:
            # Only allow L2 if L1 is finished (Safety check)
            if not self.approval_level_1 or self.l1_done:
                self.l2_done = True

        elif self.approval_level_3 == current_user and not self.l3_done:
            # Only allow L3 if L2 is finished
            if not self.approval_level_2 or self.l2_done:
                self.l3_done = True

        # Close the notification (Activity) for THIS user
        my_activity = self.activity_ids.filtered(lambda a: a.user_id == current_user)
        if my_activity:
            my_activity.action_feedback(feedback="Approved")

        # --- B. Decide Who is Next? (Step-by-Step Logic) ---
        next_user = False

        # If Level 1 is done, check if we need Level 2
        if self.l1_done and self.approval_level_2 and not self.l2_done:
            next_user = self.approval_level_2

        # If Level 2 is done (or wasn't needed), check if we need Level 3
        elif (self.l2_done or not self.approval_level_2) and self.approval_level_3 and not self.l3_done:
            next_user = self.approval_level_3

        # --- C. Action: Trigger Next User OR Finish ---
        if next_user:
            # Create Activity for the NEXT person
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=next_user.id,
                summary=f"Approval Requested: {self.name}",
                note=f"Previous level approved. Now awaiting your approval."
            )
            # Post a message saying who is next
            self.message_post(body=_(f"<b>Step Completed.</b> Assigned to next approver: {next_user.name}"))

        else:
            # Check if all required levels are actually done
            all_required_done = True
            if self.approval_level_1 and not self.l1_done: all_required_done = False
            if self.approval_level_2 and not self.l2_done: all_required_done = False
            if self.approval_level_3 and not self.l3_done: all_required_done = False

            if all_required_done:
                self.write({'state': 'approve', 'approve_status': 'approve'})
                self.message_post(body=_("<b>FINAL APPROVAL:</b> All levels completed. Document Approved."))

        return True

    # --- UPDATED: Send for Approval + Notification ---
    def send_for_approval(self):
        self.ensure_one()

        # Check who is the FIRST approver needed
        first_user = False
        if self.approval_level_1:
            first_user = self.approval_level_1
        elif self.approval_level_2:
            first_user = self.approval_level_2
        elif self.approval_level_3:
            first_user = self.approval_level_3

        if not first_user:
            raise UserError(_('Please select a Department.'))

        # Update State
        self.write({'state': 'submit'})

        # Create Activity ONLY for the FIRST user
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=first_user.id,
            summary=f"Approval Requested: {self.name}",
            note=f"Please review and approve payment for {self.amount}."
        )
        return True

    @api.depends('amount')
    def _compute_amount_in_words(self):
        for order in self:
            if order.amount and order.currency_id:
                amount_words = order.currency_id.amount_to_text(order.amount)
                order.amount_in_words = amount_words.title()
            else:
                order.amount_in_words = ""

    # --- 2. UPDATED: Visibility Logic ---
    # This ensures the "Approve" button disappears ONLY for the user who already clicked it.
    @api.depends('approval_level_1', 'approval_level_2', 'approval_level_3', 'l1_done', 'l2_done', 'l3_done')
    def _compute_is_approval_user(self):
        current_user = self.env.user
        for rec in self:
            can_approve = False

            # Logic: You can only approve if:
            # 1. You are assigned
            # 2. You haven't approved yet
            # 3. The PREVIOUS level is done (Sequential enforcement)

            # Level 1: Can approve if assigned & not done
            if rec.approval_level_1 == current_user and not rec.l1_done:
                can_approve = True

            # Level 2: Can approve if assigned & not done AND (Level 1 is done OR Level 1 wasn't assigned)
            elif rec.approval_level_2 == current_user and not rec.l2_done:
                if not rec.approval_level_1 or rec.l1_done:
                    can_approve = True

            # Level 3: Can approve if assigned & not done AND (Level 2 is done...)
            elif rec.approval_level_3 == current_user and not rec.l3_done:
                # Check if previous levels are clear
                l1_ok = not rec.approval_level_1 or rec.l1_done
                l2_ok = not rec.approval_level_2 or rec.l2_done
                if l1_ok and l2_ok:
                    can_approve = True

            rec.is_approval_user = can_approve
    # I have kept your commented code here as you requested not to remove features
    # @api.constrains("amount", "source_acc")
    # def _check_source_account_balance(self):
    # ... (rest of your commented code)

    # @api.constrains("amount", "source_acc")
    # def _check_source_account_balance(self):
    #
    #     for record in self:
    #         if record.source_acc and record.amount:
    #             AccountMoveLine = self.env['account.move.line']
    #             domain = [
    #                 ('account_id', '=', record.source_acc.id),
    #                 ('parent_state', '=', 'posted'),
    #             ]
    #             # SUM(debit) - SUM(credit) for this account
    #             results = AccountMoveLine.read_group(domain, ['debit', 'credit'], [])
    #             debit = Decimal(results[0]['debit']) if results and results[0]['debit'] else Decimal(0)
    #             credit = Decimal(results[0]['credit']) if results and results[0]['credit'] else Decimal(0)
    #             balance = debit - credit
    #             amount = Decimal(str(record.amount))
    #
    #             if balance < amount:
    #                 raise ValidationError(
    #                     f"Insufficient balance in source account '{record.source_acc.name}'.\n\n"
    #                     f"Current Balance: {balance:,.2f}\n"
    #                     f"Requested Transfer: {amount:,.2f}")

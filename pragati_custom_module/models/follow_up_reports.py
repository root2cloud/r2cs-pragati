from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    approver_1 = fields.Many2one("res.users", string="Approver 1", readonly=True)
    approver_2 = fields.Many2one("res.users", string="Approver 2", readonly=True)

    is_current_user_approver = fields.Boolean(
        compute="_compute_is_current_user_approver",
        store=False
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', readonly=True)

    @api.model
    def create(self, vals):
        # Default approvers
        approver_1 = self.env['res.users'].search([('login', '=', "anilkumar@pragatigroup.com")], limit=1)
        approver_2 = self.env['res.users'].search([('login', '=', "hanumantharao.p@pragatigroup.com")], limit=1)

        vals['approver_1'] = approver_1.id if approver_1 else False
        vals['approver_2'] = approver_2.id if approver_2 else False

        vals['state'] = 'draft'
        vals['active'] = False  # inactive until approved

        return super().create(vals)

    @api.depends()
    def _compute_is_current_user_approver(self):
        user = self.env.user
        for rec in self:
            rec.is_current_user_approver = user in (rec.approver_1 | rec.approver_2)

    def _check_is_approver(self):
        if self.env.user not in (self.approver_1 | self.approver_2):
            raise UserError("You are not allowed to approve or reject this contact.")

    # ----------------------------------
    # BUTTONS
    # ----------------------------------

    def action_submit(self):
        if self.state != 'draft':
            raise UserError("You can only submit from Draft.")

        self.state = 'waiting_approval'

        # Create mail activity for approver_1
        if self.approver_1:
            self.env['mail.activity'].create({
                'res_model_id': self.env['ir.model']._get_id('res.partner'),
                'res_id': self.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': "Approval Required",
                'note': "Please review and approve the contact.",
                'user_id': self.approver_1.id,
            })

        # Create mail activity for approver_2
        if self.approver_2:
            self.env['mail.activity'].create({
                'res_model_id': self.env['ir.model']._get_id('res.partner'),
                'res_id': self.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': "Approval Required",
                'note': "Please review and approve the contact.",
                'user_id': self.approver_2.id,
            })

        return True

    def action_approve(self):
        self._check_is_approver()

        if self.state in ('approved', 'rejected'):
            raise UserError("This record is already processed.")

        self.active = True
        self.state = "approved"

        # Mark activities as done
        self.activity_ids.action_done()

        return True

    def action_reject(self):
        self._check_is_approver()

        if self.state in ('approved', 'rejected'):
            raise UserError("This record is already processed.")

        self.active = False
        self.state = "rejected"

        # Mark activities as done
        self.activity_ids.action_done()

        return True

    def _compute_for_followup(self):
        """
        Inherited and safely updated version to fix 'NoneType' issue on timedelta
        """
        for record in self:
            total_due = 0
            total_overdue = 0
            today = fields.Date.today()

            for am in record.invoice_list:
                if am.company_id == self.env.company:
                    amount = am.amount_residual
                    total_due += amount
                    is_overdue = today > (am.invoice_date_due or am.date)
                    if is_overdue:
                        total_overdue += amount

            min_date = record.get_min_date()
            action = record.action_after()
            date_reminder = today

            if min_date and action is not None:
                try:
                    date_reminder = min_date + timedelta(days=int(action))
                except Exception:
                    date_reminder = today

            record.next_reminder_date = date_reminder

            if total_overdue > 0 and date_reminder > today:
                followup_status = "with_overdue_invoices"
            elif total_due > 0 and date_reminder <= today:
                followup_status = "in_need_of_action"
            else:
                followup_status = "no_action_needed"

            record.total_due = total_due
            record.total_overdue = total_overdue
            record.followup_status = followup_status

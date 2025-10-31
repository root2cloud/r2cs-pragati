from datetime import timedelta
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

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

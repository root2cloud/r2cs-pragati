from odoo import models, fields, api
from datetime import date


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        for record in self:
            # Use the date field from the payment, NOT today's date
            # This ensures March 2026 entries get the 25-26 prefix
            p_date = record.date or date.today()

            # Logic: If month is Jan-Mar, it's the end of the previous fiscal year
            if p_date.month < 4:
                start_yr = p_date.year - 1
                end_yr = p_date.year
            else:
                start_yr = p_date.year
                end_yr = p_date.year + 1

            # Format: 25-26
            year_prefix = f"{str(start_yr)[2:]}-{str(end_yr)[2:]}"

            # Get sequence number and pass the date so it resets to 1 every April
            seq = self.env['ir.sequence'].next_by_code(
                'outbound.payment.sequence',
                sequence_date=p_date
            ) or '1'

            # Result: RF25-26/0001 or RF26-27/0001
            record.name = f"RF{year_prefix}/{seq.zfill(4)}"

            # Sync with the Journal Entry (Account Move)
            if record.move_id:
                record.move_id.name = record.name

        return super(AccountPayment, self).action_post()

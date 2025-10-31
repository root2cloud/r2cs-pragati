from odoo import models, fields, api
from datetime import date


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        for record in self:
            current_date = date.today()
            # Get the next sequence
            sequence = self.env['ir.sequence'].next_by_code('outbound.payment.sequence') or 'New'

            if current_date:
                current_year = current_date.year
                next_year = str(current_year + 1)
                year_range = f"{current_year}-{next_year}"
                print(year_range, "$$$$$$$$$$$$$$$$$")
                sequence_number = sequence
                record.name = "RF24-25/{}".format(sequence_number.zfill(4))

                # Ensure the Journal Entry's number matches the payment name
                if record.move_id and record.move_id.name and record.move_id.name != record.name:
                    record.move_id.name = record.name

        return super(AccountPayment, self).action_post()
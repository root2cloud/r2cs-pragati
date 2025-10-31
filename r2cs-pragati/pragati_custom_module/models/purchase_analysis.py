from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    name_of_record = fields.Char(
        string="Vendor Bill Number",
        compute="_compute_name_of_record",
        store=True,
        index=True,
    )

    @api.depends('move_id.name', 'move_id.state', 'move_id.move_type')
    def _compute_name_of_record(self):
        """
        Copy the Vendor Bill number into name_of_record field.
        Only for posted Vendor Bills (move_type = in_invoice).
        """
        for line in self:
            if line.move_id.move_type == 'in_invoice' and line.move_id.state == 'posted':
                line.name_of_record = line.move_id.name
            else:
                line.name_of_record = False

    @api.model
    def backfill_vendor_bills(self):
        """
        Backfill existing posted Vendor Bills into name_of_record.
        """
        posted_lines = self.search([
            ('move_id.move_type', '=', 'in_invoice'),
            ('move_id.state', '=', 'posted')
        ])
        posted_lines._compute_name_of_record()
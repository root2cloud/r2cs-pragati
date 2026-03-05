from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import re


class AccountSubSubGroup(models.Model):
    _name = 'account.sub.sub.group'
    _description = 'Account Sub-Sub Group'

    name = fields.Char(string='Name', required=True)


class AccountAccount(models.Model):
    _inherit = 'account.account'

    main_group = fields.Selection(
        [
            ('asset', 'ASSETS'),
            ('equity', 'EQUITY'),
            ('expense', 'EXPENSES'),
            ('liability', 'LIABILITIES'),
            ('income', 'REVENUE'),
        ],
        string="Main Group",
        store=True, required=True
    )

    sub_sub_group_id = fields.Many2one(
        'account.sub.sub.group',
        string='Sub-Sub Group',
        help='Select the Sub-Sub Group category', required=True
    )

    # When account_type changes - clear sub_sub_group_id
    @api.onchange('account_type')
    def _onchange_account_type(self):
        self.sub_sub_group_id = False

    # When main_group changes - clear account_type and sub_sub_group_id
    @api.onchange('main_group')
    def _onchange_main_group(self):
        self.account_type = False
        self.sub_sub_group_id = False

    @api.constrains('code')
    def _check_code_numeric_six_digits(self):
        for record in self:
            if record.code:
                # Regex explanation:
                # ^ matches start, \d{6} matches exactly 6 digits, $ matches end
                if not re.match(r'^\d{6}$', record.code):
                    raise ValidationError(_(
                        "The Account Code must be exactly 6 numeric digits (e.g., 103010). "
                        "Alphabets and special characters are not allowed."
                    ))

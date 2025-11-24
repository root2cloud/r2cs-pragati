from odoo import fields, models


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
        store=True,
    )

    sub_sub_group_id = fields.Many2one(
        'account.sub.sub.group',
        string='Sub-Sub Group',
        help='Select the Sub-Sub Group category',
    )

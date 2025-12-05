from odoo import fields, models, api


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

from odoo import models, fields


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    pos_name = fields.Char(string='POS Name', readonly=True)

    def _select(self):
        return super()._select() + ", pc.name AS pos_name"

    def _from(self):
        return super()._from() + """
            LEFT JOIN pos_order po ON po.account_move = move.id
            LEFT JOIN pos_session ps ON ps.id = po.session_id
            LEFT JOIN pos_config pc ON pc.id = ps.config_id
        """

    def _group_by(self):
        return super()._group_by() + ", pc.name"

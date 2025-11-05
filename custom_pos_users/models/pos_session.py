from odoo import models, api
from odoo.exceptions import AccessError


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def create(self, vals):
        session = super(PosSession, self).create(vals)
        user = self.env.user
        # Apply restriction only for non-admin users
        if not user.has_group('point_of_sale.group_pos_manager') and user.has_group('point_of_sale.group_pos_user'):
            partner = user.partner_id
            if partner.shop_of_pos_id and session.config_id != partner.shop_of_pos_id:
                raise AccessError("You are not allowed to access this POS shop.")
        return session
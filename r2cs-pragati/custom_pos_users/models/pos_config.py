from odoo import fields, models, api
from odoo.exceptions import AccessError

class PosConfig(models.Model):
    _inherit = 'pos.config'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        user = self.env.user
        # Check if the user is not an admin (i.e., does not have POS Manager group)
        if not user.has_group('point_of_sale.group_pos_manager') and user.has_group('point_of_sale.group_pos_user'):
            partner = user.partner_id
            if partner.shop_of_pos_id:
                args += [('id', '=', partner.shop_of_pos_id.id)]
            else:
                raise AccessError("No POS shop assigned to your partner profile.")
        return super(PosConfig, self).search(args, offset, limit, order, count)
# -*- coding: utf-8 -*-
#############################################################################
# Author: Fasil
# Email: fasilwdr@hotmail.com
# WhatsApp: https://wa.me/966538952934
# Facebook: https://www.facebook.com/fasilwdr
# Instagram: https://www.instagram.com/fasilwdr
#############################################################################
from odoo import api, fields, models, _


class LoyaltyCard(models.Model):
    _inherit = 'loyalty.card'

    def get_qr_code_url(self):
        self.ensure_one()
        return self.get_base_url() + '/reward/status/' + self.code


class SaleLoyaltyRewardWizard(models.TransientModel):
    _inherit = 'sale.loyalty.reward.wizard'

    def action_apply(self):
        claimable_rewards = self.order_id._get_claimable_rewards()
        res = super().action_apply()
        status = name = False
        for cpn, reward in claimable_rewards.items():
            status = cpn.points
            name = cpn.program_id.display_name
            break
        if status and name:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _(f'{name} - Status: {status}'),
                    'type': 'warning',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }
        return res

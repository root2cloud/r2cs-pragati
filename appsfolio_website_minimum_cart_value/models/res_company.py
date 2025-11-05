# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of appsfolio. (Website: www.appsfolio.in).                            #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    min_cart_value = fields.Float(
        string='Minimum Cart Value'
    )
    
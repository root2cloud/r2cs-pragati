# -*- coding: utf-8 -*-

##############################################################################
#
#    Weblytic Labs.
#    Copyright (C) 2023 Weblytic Labs (<https://weblyticlabs.com>).
#    Author: WeblyticLabs <support@weblyticlabs.com>
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    min_sale_qty = fields.Integer(string="Min Sale Qty")
    max_sale_qty = fields.Integer(string="Max Sale Qty")

    min_limit_of_product=fields.Integer(string="min Limit of product")
    max_limit_of_product=fields.Integer(string="max Limit of product")

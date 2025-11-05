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
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_uom_qty')
    def _check_min_max_order_item_quantity(self):
        for line in self:
            min_qty = line.product_id.min_sale_qty
            max_qty = line.product_id.max_sale_qty
            min_limit_product=line.product_id.min_limit_of_product
            max_limit_product=line.product_id.max_limit_of_product
            product_uom_qty = line.product_uom_qty
            if min_qty and product_uom_qty <= min_qty:
                message = "The minimum order quantity for " + line.product_id.name + " should be " + str(min_limit_product)+" grms"
                raise ValidationError(message)
            if max_qty and product_uom_qty > max_qty:
                message = "The maximum order quantity for " + line.product_id.name + " should be " + str(max_limit_product)+"Kgs"
                raise ValidationError(message)

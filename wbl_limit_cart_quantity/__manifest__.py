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

{
    'name': 'Limit Cart Quantity | Minimum Order Quantity | Maximum Order Quantity',
    'version': '16.0.1.0.0',
    'summary': """Now you can limit your customer from bulk orders of any individual product. 
    Add checkout restrictions based on product. so that customers can only order products in a quantity specified.""",
    'description': """Now you can limit your customer from bulk orders of any individual product. Add checkout restrictions 
    based on product. so that customers can only order products in a quantity specified.""",
    'category': 'eCommerce',
    'author': 'Weblytic Labs',
    'company': 'Weblytic Labs',
    'website': "https://store.weblyticlabs.com",
    'depends': ['base', 'website', 'website_sale', 'mail', 'account', 'sale'],
    'price': '15.00',
    'currency': 'USD',
    'data': [
        'views/product_views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'wbl_limit_cart_quantity/static/src/js/website_sale.js',
        ],
    },
    'images': ['static/description/banner.gif'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}

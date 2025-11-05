# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Product Approval Access',
    'version': '16.0.0.0',
    'category': 'Extra Tools',
    'summary': 'Product approval process product approve workflow product approval access by product manager product approval request in sale order product approved products in invoice inventory product approval in manufacturing product manager approval',
    'description': """

        Product Approval Odoo app helps users to create a product which need an approval. The product will be create default in draft stage then only product manager have access to approve the product with single click. Once approved product by product manager then the product will be available to create order like sale order, purchase order, manufacturing order etc.
    
    """,
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.com',
    'depends': ['base','sale_management','product','purchase','stock','mrp'],
    'data': [
            'security/base_groups.xml',
            'views/product_views.xml',
            'views/sale_order_form_view.xml',
    ],
    'license':'OPL-1',
    'installable': True,
    'auto_install': False,
}

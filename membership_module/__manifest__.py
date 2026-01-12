{
    "name": "membership_custom_module",
    'license': 'LGPL-3',
    "depends": ["base", "website", "portal", "sale", 'website_sale', 'product', "uom", ],
    "data": ['security/ir.model.access.csv', 'views/membership_menu_views.xml', 'views/membership_planning_views.xml',
             'views/slots_views.xml', 'views/inventory_slot_page_views.xml', 'views/respartner_views.xml',
             'views/saleorder_views.xml', 'views/membership_template_views.xml',
             'views/shop_configuration_template_views.xml', 'views/slots_portal_views.xml'],
    "assets": {
        "web.assets_frontend": [
            'membership_module/static/src/css/membership_styles.css',
            'membership_module/static/src/js/membership_plans_buy_add_to_cart.js',
            # 'membership_module/static/src/js/slot_data_edit.js',
            'membership_module/static/src/js/slot_portal_template_edit.js',
            'membership_module/static/src/js/slot_sale_order_creation.js',
            'membership_module/static/src/js/slot_deadline_popup.js',

            # 'membership_module/static/src/js/membership_plans_script.js',
            # 'membership_module/static/src/js/membership_plans_fetch_data.js',
            # 'membership_module/static/src/js/membership_plans_add_to_cart.js'
        ]
    }
}

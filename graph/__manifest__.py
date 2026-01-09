{
    'name': 'Graph Plotting',
    'license': 'LGPL-3',
    'depends': ['base', 'website', 'portal', 'web', 'agriculture_management_odoo', 'product', 'stock', 'website_sale'],
    'data': [
        'views/graph_plotting_views.xml',
        'views/check_greenhouse_openland_views.xml',
        'views/check_product_is_menure_views.xml',
        'views/add_menure_views.xml',
        'views/add_pest_views.xml',
        'views/add_harvest_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'graph/static/src/css/stock_location_styles.css',
            'graph/static/src/js/graph_plotting_info_beds.js',
            'graph/static/src/js/add_menure.js',
            'graph/static/src/js/add_pest.js',
            'graph/static/src/js/add_harvest.js',

        ],

    },

}

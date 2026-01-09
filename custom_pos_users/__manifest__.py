{
    'name': 'Custom POS Shop Restriction',
    'depends': ['base', 'point_of_sale', 'contacts'],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/pos_menu_access.xml',
        'views/custom_res_partners.xml',
    ],
    'installable': True,
    'application': False,
}

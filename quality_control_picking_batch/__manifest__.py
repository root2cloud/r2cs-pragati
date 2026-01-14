{
    'name': 'Quality - Batch Transfer',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Manufacturing/Quality',
    'summary': 'Support of quality control into batch transfers',
    'depends': [
        'quality_control',
        'stock_picking_batch',
    ],
    'data': [
        'views/stock_picking_batch_views.xml',
    ],
    'auto_install': True,
    'installable': True,
}

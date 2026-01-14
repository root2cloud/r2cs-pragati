{
    'name': 'MRP features for Quality Control with IoT',
    'license': 'LGPL-3',
    'summary': 'Quality Management with MRP and IoT',
    'depends': ['quality_mrp_workorder', 'quality_control_iot', 'mrp_workorder_iot'],
    'category': 'Manufacturing/Quality',
    'description': """
    Adds Quality Control to workorders with IoT.
""",
    "data": [
        'views/mrp_workorder_views.xml',
    ],
    'auto_install': True,
}

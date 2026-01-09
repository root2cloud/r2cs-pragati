{
    "name": "MRP Custom Workorder Module",
    "version": "16.0.1.0.0",
    'license': 'LGPL-3',
    "summary": "Custom Workorder Enhancements",
    "category": "Manufacturing",
    "depends": ["mrp", "hr", "stock", "account", "uom", "product"],
    "data": [
        "security/ir.model.access.csv",
        # "views/workorder.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True
}

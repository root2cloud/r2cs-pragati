{
   'name':'zip location',
   'license':'LGPL-3',
   'data':['security/ir.model.access.csv',
            'views/zip_template.xml',
            'views/zip_views.xml',
   ],
   'depends':['base','mail','contacts','auth_signup'],
   "assets": {
        "web.assets_frontend": [
            "my_zip_loc/static/src/js/zip_code.js"
        ]
    },
}
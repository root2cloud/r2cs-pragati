# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Auto Inactive Sessions Timeout Timer",
    'version': '16.0.0.3',
    "category" : "Extra Tools",
    'summary': 'Auto session timeout timer inactive sessions timeouts for inactive sessions system parameters track active sessions inactive session timeout parameter inactive sessions termination auto inactive sessions termination timer timeout for inactive session',
    "description": """

        Inactive Sessions Timeout Odoo App helps you to set limitation of timeout for the sessions(In Minute) which are inactive. Admin can easily manage and track the active sessions. Inactive session are timeout according to configure system parameters and login again to reactivate the session.

    """ , 
    'author': 'BrowseInfo',
    "price": 20,
    "currency": 'EUR',
    'website': 'https://www.browseinfo.com',
    'depends': ['bus'],
    'data': [
        'data/session_data.xml',  
    ],
    'license':'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/pAT2glK-iCM',
    "images":['static/description/Inactive-Sessions-Timeout.gif'],
}

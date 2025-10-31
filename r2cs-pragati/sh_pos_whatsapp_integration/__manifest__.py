# Part of Softhealer Technologies.
{
    "name": "POS WhatsApp Integration",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Point of sale",
    "license": "OPL-1",
    "summary": " Whatsapp Integration App,  POS To Customer Whatsapp Module, POS Order To Clients Whatsapp, Point Of Sale Whatsapp App, POS  Order Whatsapp, POS Whatsapp Odoo",
    "description": """Nowadays, WhatsApp is frequently used. Many communications take place on WhatsApp. Currently, in Odoo there is no feature where you can send POS(Point Of Sale) direct to partner's WhatsApp. Our module will provide that feature. You need to just one-time login in WhatsApp, after that, you can send POS to direct or manually to partner's WhatsApp. You can track sent messages in chatter.""",
    "version": "16.0.1",
    "depends": ['base', 'point_of_sale'],
    "application": True,
    "data": [
                "views/res_config_settings.xml",
                "views/res_users.xml",
             ],
    'assets': {
            'point_of_sale.assets': [

                'sh_pos_whatsapp_integration/static/src/js/Screens/receipt_screen.js',
                'sh_pos_whatsapp_integration/static/src/js/Screens/partner_list_screen.js',
                'sh_pos_whatsapp_integration/static/src/js/Popup/wapp_message_popup.js',

                'sh_pos_whatsapp_integration/static/src/xml/Screens/receipt_screen.xml',
                'sh_pos_whatsapp_integration/static/src/xml/Screens/partner_list_screen.xml',
                'sh_pos_whatsapp_integration/static/src/xml/Popup/wapp_message_popup.xml',

                'sh_pos_whatsapp_integration/static/src/scss/pos.scss',

                ],
              
               },
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "price": 50,
    "currency": "EUR"
}

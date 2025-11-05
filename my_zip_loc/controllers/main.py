from odoo import http
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home

class WebsiteZip(http.Controller):
    @http.route(['/get_zip_codes'], type='json', auth="public", website=True)
    def get_zip_codes(self):
        zip_codes = http.request.env['res.zip'].sudo().search_read([], ['location_field', 'zip_field'])
        return zip_codes

class OAuthLogin(Home):
    @http.route(['/web/signup'], type='http', auth="public", website=True)
    def web_auth_signup(self, *args, **kw):
        result = super(OAuthLogin, self).web_auth_signup(*args, **kw)
        if kw.get('login'):
            user = request.env['res.users'].sudo().search([('login', '=', kw.get('login'))])
            if kw.get('zip_code') and user:
                zip_code = kw.get('zip_code').split(" - ")[0]
                zip_id = request.env['res.zip'].sudo().search([('zip_field', '=', zip_code)], limit=1)
                if zip_id:
                    user.partner_id.zip_id = zip_id.id
                    user.partner_id.zip = zip_id.zip_field
        return result

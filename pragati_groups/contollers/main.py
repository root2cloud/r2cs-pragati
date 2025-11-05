# import logging
# from odoo.http import request
# from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home
#
# _logger = logging.getLogger(__name__)
#
# class OAuthLogin(Home):
#
#     def web_auth_signup(self, *args, **kw):
#         result = super(OAuthLogin, self).web_auth_signup(*args, **kw)
#         # result["providers"] = self.list_providers()
#         request.env.user.phone_number = kw.get('phone_number')
#         return result

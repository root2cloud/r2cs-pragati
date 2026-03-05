# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import http, _
from odoo.http import request

from odoo.addons.web.controllers.database import Database


class DatabaseInherit(Database):

    @http.route('/web/reset_by_master_pass/submit', type='http',
                methods=['POST'], auth="public", website=True, csrf=False)
    def change_password_by_master(self, **kw):
        """
        Handle the Forgot Password form submission.

        UPDATED: Now only requires two fields:
            - user_name       : the login/username of the account
            - change_password : the new password to set directly

        No new_password / confirm_new_password fields needed anymore.
        Password is changed immediately upon form submission.

        :param kw: POST fields from the forgot-password form.
        :return:   Redirect to /web/login on success, or re-render the
                   forgot_password template with an error on failure.
        """
        values = {}

        # ── Step 1: Make sure the change_password field is not empty ──────────
        if not kw.get('change_password'):
            values['error'] = _("Please Enter a New Password")
            return request.render(
                'password_reset_manager.forgot_password', values)

        # ── Step 2: Find the user by login/username ───────────────────────────
        user_valid = request.env['res.users'].sudo().search([
            ('login', '=', kw['user_name'])
        ], limit=1)

        # ── Step 3: If no user found, show an error ───────────────────────────
        if not user_valid:
            values['error'] = _("User Name Is Not Valid")
            return request.render(
                'password_reset_manager.forgot_password', values)

        # ── Step 4: Directly set the new password ─────────────────────────────
        user_valid.sudo().write({
            'password': kw['change_password']
        })

        # ── Step 5: Redirect to login with a success message ──────────────────
        return request.redirect('/web/login?message=%s' % _('Password Changed'))
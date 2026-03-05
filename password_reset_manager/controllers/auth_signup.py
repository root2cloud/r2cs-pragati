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
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import odoo
from odoo import http, _
from odoo.http import request, dispatch_rpc
from odoo.exceptions import UserError

from odoo.addons.web.controllers.database import Database
from odoo.addons.auth_signup.controllers.main import AuthSignupHome


# ──────────────────────────────────────────────────────────────────────────────
# PART 1 : Forgot-password reset (no master password required)
# ──────────────────────────────────────────────────────────────────────────────

class DatabaseInherit(Database):

    @http.route(
        '/web/reset_by_master_pass/submit',
        type='http',
        methods=['POST'],
        auth='public',
        website=True,
        csrf=False,
    )
    def change_password_by_master(self, **kw):
        """
        Handle the 'Forgot Password' form submission.

        CHANGED: Master password verification has been removed.
        Now any visitor can reset a user's password by supplying:
            • user_name           – the login/email of the target account
            • new_password        – the desired new password
            • confirm_new_password – must match new_password

        :param kw: POST fields from the forgot-password form.
        :return:   Redirect to /web/login on success, or re-render the form
                   with an error message on failure.
        """
        values = {}

        # ── Step 1: Make sure the two new-password fields match ───────────────
        if kw['confirm_new_password'] != kw['new_password']:
            values['error'] = _("Passwords Do Not Match")
            return request.render(
                'password_reset_manager.forgot_password', values)

        # ── Step 2: Look up the user by login name ────────────────────────────
        user_valid = request.env['res.users'].sudo().search([
            ('login', '=', kw['user_name'])
        ], limit=1)

        if not user_valid:
            # No account found with that username – show a friendly error
            values['error'] = _("User Name Is Not Valid")
            return request.render(
                'password_reset_manager.forgot_password', values)

        # ── Step 3: Update the password (sudo required for public route) ──────
        user_valid.sudo().write({
            'password': kw['confirm_new_password']
        })

        # ── Step 4: Redirect to login with a success banner ───────────────────
        return request.redirect('/web/login?message=%s' % _('Password Changed'))


# ──────────────────────────────────────────────────────────────────────────────
# PART 2 : Direct password change (user knows their old password)
# ──────────────────────────────────────────────────────────────────────────────

class AuthSignupHomeInherit(AuthSignupHome):

    @http.route(
        '/web/forgot_password',
        type='http',
        auth='public',
        website=True,
        sitemap=False,
        csrf=False,
    )
    def forgot_password(self):
        """
        Render the 'Forgot Password' page.
        (No master-password field is shown anymore – see updated template.)
        """
        qcontext = self.get_auth_signup_qcontext()
        return request.render(
            'password_reset_manager.forgot_password', qcontext)

    @http.route(
        '/web/reset_password/direct',
        type='http',
        auth='public',
        website=True,
        sitemap=False,
        csrf=False,
    )
    def web_auth_reset_password_direct(self):
        """
        Render the 'Change Password' page (user must supply their old password).
        """
        qcontext = self.get_auth_signup_qcontext()
        return request.render(
            'password_reset_manager.reset_password_direct', qcontext)

    @http.route(
        '/web/reset_password/submit',
        type='http',
        methods=['POST'],
        auth='public',
        website=True,
        csrf=False,
    )
    def change_password(self, **kw):
        """
        Handle the 'Change Password' form submission.

        The user must be authenticated with their old password first.
        Public users (portal / anonymous) are not allowed to change passwords
        through this endpoint.

        :param kw: POST fields: user_name, old_password, new_password,
                   confirm_new_password.
        :return:   Redirect to /web/login on success, or re-render the form
                   with an error message on failure.
        """
        values = {}

        # ── Step 1: Make sure the two new-password fields match ───────────────
        if kw['confirm_new_password'] != kw['new_password']:
            values['error'] = _("Password Not Match")
            return request.render(
                'password_reset_manager.reset_password_direct', values)

        try:
            # ── Step 2: Authenticate with the OLD password ────────────────────
            uid = request.session.authenticate(
                request.session.db,
                kw['user_name'],
                kw['old_password'],
            )

            # ── Step 3: Block public / anonymous users ────────────────────────
            is_user_public = request.env.user.has_group('base.group_public')
            if is_user_public:
                values['error'] = _("Public users can't change their password")
                return request.render(
                    'password_reset_manager.reset_password_direct', values)

            # ── Step 4: Write the new password ────────────────────────────────
            user = request.env['res.users'].browse(uid)
            user.sudo().write({'password': kw['confirm_new_password']})

            # ── Step 5: Redirect to login with a success banner ───────────────
            return request.redirect(
                '/web/login?message=%s' % _('Password Changed'))

        except odoo.exceptions.AccessDenied:
            # Old password was wrong
            values['error'] = _("Login or Password Is Incorrect")
            return request.render(
                'password_reset_manager.reset_password_direct', values)
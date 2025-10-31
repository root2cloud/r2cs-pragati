# -*- coding: utf-8 -*-
#############################################################################
# Author: Fasil
# Email: fasilwdr@hotmail.com
# WhatsApp: https://wa.me/966538952934
# Facebook: https://www.facebook.com/fasilwdr
# Instagram: https://www.instagram.com/fasilwdr
#############################################################################

from odoo import http, _, fields
from odoo.http import request
from werkzeug import urls
import re


class RewardController(http.Controller):

    @http.route('/reward/status/<string:cpn_code>', type='http', auth="public", methods=['POST', 'GET'], website=True)
    def reward_status(self, cpn_code, **kw):
        record = request.env['loyalty.card'].sudo().search([('code', '=', cpn_code)], limit=1)
        company = request.env.company
        base_url = request.httprequest.url_root.strip('/') or request.env.user.get_base_url()
        if record:
            values = {
                'is_valid': True,
                'code_for_reward': record.code,
                'description': record.program_id.display_name if record.program_id else False,
                'code_expiry': record.expiration_date,
                'balance': record.points,
                'partner_name': record.partner_id.name,
                'company_name': company.name,
                'company_email': company.email,
                'company_logo': urls.url_join(base_url, f'web/image/res.company/{company.id}/logo'),
                'company_details': company.company_details,
            }
        else:
            values = {
                'is_valid': False,
                'company_name': company.name,
                'company_email': company.email,
                'company_logo': urls.url_join(base_url, f'web/image/res.company/{company.id}/logo'),
                'company_details': company.company_details,
            }

        return request.render('pragati_coupon_scanner.gift_card_template', values)


class QRcodeController(http.Controller):

    @http.route('/pragati_coupon_scanner/scan', type='json', auth='user')
    def main_menu(self, qrcode, **kw):
        cpn_code = qrcode.split("/")[-1]
        record = request.env['loyalty.card'].sudo().search([('code', '=', cpn_code)], limit=1)
        if not record:
            pattern = r"Coupon No :([0-9a-zA-Z\-]+)"
            match = re.search(pattern, qrcode)
            coupon_number = match.group(1) if match else None
            record = request.env['loyalty.card'].sudo().search([('code', '=', coupon_number)], limit=1)
        values = None
        if record:
            if record.expiration_date and record.expiration_date < fields.Date.today():
                code_expiry = 'Expired'
            else:
                code_expiry = record.expiration_date if record.expiration_date else ''
            values = {
                'description': [x.description for x in record.program_id.reward_ids],
                'code_for_reward': record.code,
                'code_expiry': code_expiry,
                'partner_name': record.partner_id.name if record.partner_id else '',
                'points': record.points if record.points != 0.0 else 'Coupon has been used already !',
                'coupon_value': record.program_id.coupon_value,
            }
        if values:
            res = {'data': values}
        else:
            res = {'warning': f'{cpn_code} not a valid Code'}
        return res
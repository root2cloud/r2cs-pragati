# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.tools.translate import _
import base64


class AcsImageEditor(http.Controller):

    @http.route(['/my/acs/image/editor/<int:record>'], type='http', auth="user", website=True, sitemap=False)
    def acs_image_editor(self, model=False, record=False, **kwargs):
        record = request.env['ir.attachment'].browse([record])
        data = {
            'acs_doc': record,
            'acs_model': kwargs.get('acs_model'),
            'acs_rec_id': kwargs.get('acs_rec_id'),
            'acs_action_id': kwargs.get('acs_action_id')
        }
        return request.render("acs_hms_body_chart.acs_image_editor", data)

    @http.route(['/my/acs/image/<int:record>'], type="http", auth="user", methods=['post'], website=True, csrf=False, sitemap=False)
    def acs_image_editor_updateimage(self, record, **kwargs):
        attachment = request.env['ir.attachment'].browse([record])
        datas = list(kwargs.keys())[0]
        image_data = datas.split("base64,")[1].replace(' ','+')
        strImage = image_data + "=" * ((4 - len(image_data) % 4) % 4)
        attachment.write({
            'datas': strImage
        })
        return request.redirect('/my/acs/image/editor/%s' % record)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- coding: utf-8 -*-
# from odoo import http


# class PosExtension(http.Controller):
#     @http.route('/pos_extension/pos_extension', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_extension/pos_extension/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_extension.listing', {
#             'root': '/pos_extension/pos_extension',
#             'objects': http.request.env['pos_extension.pos_extension'].search([]),
#         })

#     @http.route('/pos_extension/pos_extension/objects/<model("pos_extension.pos_extension"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_extension.object', {
#             'object': obj
#         })

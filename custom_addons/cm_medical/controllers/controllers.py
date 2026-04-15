# -*- coding: utf-8 -*-
# from odoo import http


# class CmMedical(http.Controller):
#     @http.route('/cm_medical/cm_medical', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cm_medical/cm_medical/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cm_medical.listing', {
#             'root': '/cm_medical/cm_medical',
#             'objects': http.request.env['cm_medical.cm_medical'].search([]),
#         })

#     @http.route('/cm_medical/cm_medical/objects/<model("cm_medical.cm_medical"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cm_medical.object', {
#             'object': obj
#         })

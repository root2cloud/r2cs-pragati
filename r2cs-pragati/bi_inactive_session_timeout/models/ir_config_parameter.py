# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import json
import werkzeug
from lxml import etree
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from odoo.http import request

class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    def write(self, vals):
        res = super(IrConfigParameter, self).write(vals)
        self._session_timeout_delay.clear_cache(
            self.filtered(lambda rec_key: rec_key.key == 'session_timeout_time'),
        )
        return res


    @api.model
    @tools.ormcache("self.env.cr.dbname")
    def _session_timeout_delay(self):
        value=float(self.env["ir.config_parameter"].sudo().get_param('session_timeout_time',5000,))
        value=value*60
        return value
    

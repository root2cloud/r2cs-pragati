# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, tools,http
from odoo.tools.safe_eval import safe_eval
import operator
import logging
from odoo.http import request
from decorator import decorator
from time import time
from os import utime
from os.path import getmtime
from odoo.http import SessionExpiredException


_logger = logging.getLogger(__name__)

class Irhttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):
        res = super(Irhttp, cls)._authenticate(endpoint=endpoint)
        if request and request.session.uid and request.env.user.is_public == False:

            if not http.request:
                return
            session = http.request.session

            params = request.env["ir.config_parameter"]
            delay_time = params._session_timeout_delay()
            delay_time_exact= time() - delay_time

            session_expired = False
            if delay_time is not False:
                path = http.root.session_store.get_session_filename(session.sid)
                try:
                    session_expired = getmtime(path) < delay_time_exact
                except OSError:
                    _logger.exception(
                        "Exception reading session file modified time.",
                    )
                    session_expired = True

            session_terminated = False
            if session_expired:
                if session.db and session.uid:
                    session.logout(keep_db=True)
                    
                session_terminated = True

            if "/browseinfo/req/checked" not in locals():
                path = http.root.session_store.get_session_filename(session.sid)
            try:
                utime(path, None)
            except OSError:
                _logger.exception(
                    "Exception reading session file modified time.",
                )
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

    





    


        

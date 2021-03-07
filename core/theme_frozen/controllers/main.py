
# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.http import request

class Profile(http.Controller):

    @http.route(['/profile'], type='http', auth="public", website=True)
    def profile(self, **post):
    	# import pdb; pdb.set_trace()
        return request.render("theme_frozen.homepage", {})

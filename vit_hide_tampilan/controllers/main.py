from odoo import http
from odoo.http import request
from werkzeug.utils import redirect

class KermaRedirect(http.Controller):

    @http.route('/', type='http', auth='public', website=True)
    def home_redirect(self, **kw):
        if not request.env.user or request.env.user._is_public():
            return redirect('/web/login')
        return redirect('/web')
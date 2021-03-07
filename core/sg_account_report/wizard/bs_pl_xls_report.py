# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models, api, _


class bs_pl_xls_report(models.TransientModel):
    _name = "bs.pl.xls.report"


    file = fields.Binary("Click On Download Link To Download Xls File", readonly=True)
    name = fields.Char("Name", size=32, invisible=True, default='BS PL.xls')

    @api.multi
    def get_back_action(self):
        context = self.env.context
        return {
          'name': _('YTD Financial Reports'),
          'view_type': 'form',
          "view_mode": 'form',
          'res_model': 'account.wizard.report',
          'type': 'ir.actions.act_window',
          'target': 'new',
          'context': context,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
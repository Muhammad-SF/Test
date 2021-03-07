# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


from odoo import fields, models, exceptions, api
from odoo.tools.translate import _

class hr_timesheet_invoice_create(models.TransientModel):
    _name = 'hr.timesheet.invoice.create'
    _description = 'Create invoice from timesheet'

    date    = fields.Boolean('Date', help='The real date of each work will be displayed on the invoice', default=1)
    time    = fields.Boolean('Time spent', help='The time of each work done will be displayed on the invoice')
    name    = fields.Boolean('Description', help='The detail of each work done will be displayed on the invoice', default=1)
    price   = fields.Boolean('Cost',
                           help='The cost of each work done will be displayed on the invoice. You probably don\'t want to check this')
    product = fields.Many2one('product.product', 'Force Product',
                              help='Fill this field only if you want to force to use a specific product. Keep empty to use the real product that comes from the cost.')

    @api.model
    def view_init(self, fields_list):
        """ Override this method to do specific things when a form view is
        opened. This method is invoked by :meth:`~default_get`.
        """
        """
                This function checks for precondition before wizard executes
                @param self: The object pointer
                @param cr: the current row, from the database cursor,
                @param uid: the current user’s ID for security checks,
                @param fields: List of fields for default value
                @param context: A standard dictionary for contextual values
                """
        analytic_obj = self.env['account.analytic.line']
        data         = self.env.context.get('active_ids', [])
        for analytic in analytic_obj.browse(data):
            if analytic.invoice_id:
                raise exceptions.Warning(_('Invoice is already linked to some of the analytic line(s)!'))

    @api.multi
    def do_create(self):
        context = self.env.context
        data    = self.read()[0]
        lines   = self.env['account.analytic.line'].browse(context['active_ids'])
        # Create an invoice based on selected timesheet lines
        invs    = lines.invoice_cost_create(data)
        mod_obj = self.env['ir.model.data']
        mods    = mod_obj.search([('name', '=', 'action_invoice_tree1')], limit=1)
        for mod in mods:
            act_win = mod.res_id.read()
            act_win['domain'] = [('id','in',invs), ('type','=','out_invoice')]
            act_win['name']   = _('Invoices')
            return act_win
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
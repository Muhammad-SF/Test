# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://serpentcs.com>).
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
from odoo import fields, models


class HrLeaveConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    module_sg_bank_reconcile = fields.Boolean(string='Manage Bank Reconcilation and Bank Statements', 
                                            help="This help to Reconcile bank statement")
    module_sg_dbs_giro = fields.Boolean(string='Generate DBS GIRO file for Employee salary payments', 
                                            help="This help to generate Dbs giro file for salary payment upload to bank's site.")

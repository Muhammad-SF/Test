# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
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

from odoo import models, fields

class account_move(models.Model):
    _inherit = 'account.move'

    is_reconciled = fields.Boolean('Reconciled')

account_move()

class account_move_line(models.Model):
    _inherit='account.move.line'

    cleared_bank_account =  fields.Boolean('Cleared? ', help='Check if the transaction has cleared from the bank')
    bank_acc_rec_statement_id =  fields.Many2one('bank.acc.rec.statement', 'Bank Acc Rec Statement', help="The Bank Acc Rec Statement linked with the journal item")
    draft_assigned_to_statement = fields.Boolean('Assigned to Statement? ', help='Check if the move line is assigned to statement lines')

account_move_line() 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
from odoo import models, fields, api
from datetime import datetime
import logging
import pytz
from odoo.exceptions import  Warning

_logger = logging.getLogger(__name__)

class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    auto_reset = fields.Boolean(copy=False, string='Auto Reset', help="When auto reset is true, then it will automatically reset the sequence according to the period you choose \n"
                                                                      "- Daily, resets everyday at 00:00 \n"
                                                                    "- Monthly, resets every 00:00 on the first date of the new month \n"
                                                                    "- Yearly, resets every 00:00 on the first date of the new year")
    auto_reset_date = fields.Date(copy=False, string='Auto Reset Date')
    auto_reset_value = fields.Selection([('daily', 'Daily'), ('monthly', 'Monthly'), ('annual', 'Yearly')], copy=False, string='Value')

    @api.multi
    @api.constrains('auto_reset', 'auto_reset_value','prefix','suffix')
    def _check_prefix_sufix(self):
        prefix = self.prefix if self.prefix else ''
        suffix = self.suffix if self.suffix else ''
        if self.auto_reset and self.auto_reset_value == 'daily':
            if prefix or suffix:
                if '%(year)s' in prefix or '%(year)s' in suffix:
                    if not all(x in prefix for x in ['%(year)s','%(month)s','%(day)s']) and not all(x in suffix for x in ['%(year)s','%(month)s','%(day)s']):
                        raise Warning('Please put one of these in the Prefix or Suffix :\n %(year)s%(month)s%(day)s \n or \n %(y)s%(month)s%(day)s')
                else:
                    if not all(x in prefix for x in ['%(y)s','%(month)s','%(day)s']) and not all(x in suffix for x in ['%(y)s','%(month)s','%(day)s']):
                        raise Warning('Please put one of these in the Prefix or Suffix :\n %(year)s%(month)s%(day)s \n or \n %(y)s%(month)s%(day)s')
        if self.auto_reset and self.auto_reset_value == 'monthly':
            if prefix or suffix:
                if '%(year)s' in prefix or '%(year)s' in suffix:
                    if not all(x in prefix for x in ['%(year)s','%(month)s']) and not all(x in suffix for x in ['%(year)s','%(month)s']):
                        raise Warning('Please put one of these in the Prefix or Suffix :\n %(year)s%(month)s \n or \n %(y)s%(month)s')
                else:
                    if not all(x in prefix for x in ['%(y)s','%(month)s']) and not all(x in suffix for x in ['%(y)s','%(month)s']):
                        raise Warning('Please put one of these in the Prefix or Suffix :\n %(year)s%(month)s \n or \n %(y)s%(month)s')
                    
            
            
        if self.auto_reset and self.auto_reset_value == 'annual':
            if '%(year)s' not in prefix and '%(year)s' not in suffix:
                if '%(y)s' not in prefix and '%(y)s' not in suffix:
                    raise Warning('Please put one of these in the Prefix or Suffix :\n %(year)s \n or \n %(y)s')

    @api.onchange('auto_reset')
    def onchange_auto_reset(self):
        if self.auto_reset:
            self.use_date_range = False
        else:
            self.auto_reset_value = False

    @api.onchange('use_date_range')
    def onchange_use_date_range(self):
        if self.use_date_range:
            self.auto_reset = False
            self.auto_reset_value = False

    #Overriding the base comcept for auto reset the sequence
    @api.model
    def next_by_code(self, sequence_code):
        self.check_access_rights('read')
        company_ids = self.env['res.company'].search([]).ids + [False]
        seq_ids = self.search(['&', ('code', '=', sequence_code), ('company_id', 'in', company_ids)])
        if not seq_ids:
            _logger.debug(
                "No ir.sequence has been found for code '%s'. Please make sure a sequence is set for current company." % sequence_code)
            return False
        force_company = self._context.get('force_company')
        if not force_company:
            force_company = self.env.user.company_id.id
        preferred_sequences = [s for s in seq_ids if s.company_id and s.company_id.id == force_company]
        seq_id = preferred_sequences[0] if preferred_sequences else seq_ids[0]
        if seq_id and seq_id.auto_reset and seq_id.auto_reset_value:
            current_date = str(datetime.now(pytz.timezone(self._context.get('tz') or 'UTC')).date())
            current_date_obj = datetime.strptime(current_date, '%Y-%m-%d')
            if seq_id.auto_reset_date == current_date:
                return seq_id._next()
            else:
                if not seq_id.auto_reset_date:
                    seq_id.write({'number_next': 1})
                elif seq_id.auto_reset_value == 'daily':
                    seq_id.write({'number_next': 1})
                elif seq_id.auto_reset_value == 'weekly':
                    weekday = current_date_obj.weekday()
                    reset_date_weekday = datetime.strptime(str(seq_id.auto_reset_date), '%Y-%m-%d').weekday()
                    if weekday == 6:
                        seq_id.write({'number_next': 1})
                    elif current_date_obj > datetime.strptime(str(seq_id.auto_reset_date), '%Y-%m-%d'):
                        compare_date = current_date_obj - datetime.strptime(str(seq_id.auto_reset_date), '%Y-%m-%d')
                        if compare_date.days > 6:
                            seq_id.write({'number_next': 1})
                        elif weekday == 0 and compare_date.days > 1:
                            seq_id.write({'number_next': 1})
                        elif weekday == 1 and compare_date.days > 2:
                            seq_id.write({'number_next': 1})
                        elif weekday == 2 and compare_date.days > 3:
                            seq_id.write({'number_next': 1})
                        elif weekday == 3 and compare_date.days > 4:
                            seq_id.write({'number_next': 1})
                        elif weekday == 4 and compare_date.days > 5:
                            seq_id.write({'number_next': 1})
                        elif weekday == 5 and compare_date.days > 6:
                            seq_id.write({'number_next': 1})
                elif seq_id.auto_reset_value == 'monthly':
                    if current_date_obj > datetime.strptime(str(seq_id.auto_reset_date), '%Y-%m-%d'):
                        if current_date[5:7] != str(seq_id.auto_reset_date)[5:7]:
                            seq_id.write({'number_next': 1})
                elif seq_id.auto_reset_value == 'annual':
                    if current_date_obj > datetime.strptime(str(seq_id.auto_reset_date), '%Y-%m-%d'):
                        if current_date[:4] != str(seq_id.auto_reset_date)[:4]:
                            seq_id.write({'number_next': 1})
                seq_id.write({'auto_reset_date': current_date})
        return seq_id._next()

IrSequence()
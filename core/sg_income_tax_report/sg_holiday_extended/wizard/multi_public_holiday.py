from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError
from dateutil import parser


class multi_public_holiday(models.TransientModel):

    _name = 'multi.public.holiday'

    name = fields.Char('Holiday Name', required=True)
    start_date = fields.Date('From Date', help='Holiday date', required=True)
    end_date = fields.Date('To Date', help='Holiday date', required=True)

    @api.constrains('start_date', 'end_date')
    def _check_public_date(self):
        if self.start_date > self.end_date:
            raise ValidationError(_('The start date must be anterior to the end date.'))
        return True

    @api.multi
    def cerate_public_holiday(self):
        context = self.env.context
        res_day = ''
        cont_holiday = False
        daylist = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if context and context.get('active_id'):
            starting_date = self.start_date
            counter = 0
            while starting_date <= self.end_date:
                res = ((datetime.datetime.strptime(starting_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT))
                if starting_date:
                    parsed_date = parser.parse(starting_date)
                    day = parsed_date.weekday()
                    res_day = daylist[day]
                if counter == 0:
                    cont_holiday = False
                else:
                    cont_holiday = True
                result = {
                    'holiday_date':starting_date, 
                    'name':self.name or '', 
                    'holiday_id':context['active_id'],
                    'day':res_day or '',
                    'cont_holiday':cont_holiday,
                    }
                self.env['hr.holiday.lines'].create(result)
                starting_date = res
                counter = counter + 1
        return True

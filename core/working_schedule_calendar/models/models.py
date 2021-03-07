# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime as dt
from datetime import datetime

class working_schedule_calendar(models.Model):
	_name = 'working_schedule.calendar'
	_order = 'dayofweek, hour_from'
	_inherit = ["mail.thread", "ir.needaction_mixin"]

	contract_id = fields.Many2one('hr.contract',string="Contract")
	department_id = fields.Many2one('hr.department',string="Department")
	working_hours = fields.Many2one('resource.calendar', string='Working Schedule')
	employee_id = fields.Many2one('hr.employee',string="Employee")
	name = fields.Char(required=True)
	dayofweek = fields.Selection([
		('0', 'Monday'),
		('1', 'Tuesday'),
		('2', 'Wednesday'),
		('3', 'Thursday'),
		('4', 'Friday'),
		('5', 'Saturday'),
		('6', 'Sunday')
		], 'Day of Week', required=True, index=True, default='0')
	date_from = fields.Date(string='Starting Date')
	date_to = fields.Date(string='End Date')
	hour_from = fields.Float(string='Work from', required=True, index=True, help="Start and End time of working.")
	hour_to = fields.Float(string='Work to', required=True)
	date_from_orignal = fields.Char('Start')
	date_to_orignal = fields.Char('End')
	date_starting = fields.Datetime()
	date_ending = fields.Datetime()
	line_id = fields.Integer()


# class hr_contract(models.Model):
#
# 	_inherit = 'hr.contract'
#
#
# 	@api.model
# 	def create(self, value):
# 		rec = super(hr_contract, self).create(value)
# 		print "+++hr.contract+++r",rec
# 		vals={}
# 		if rec.working_hours:
# 				res_cal = self.env['resource.calendar'].browse(rec.working_hours.id)
# 				if res_cal.attendance_ids:
# 					print "++m+",res_cal.attendance_ids
# 					for attan in res_cal.attendance_ids:
# 						print attan.date_from
#
# 						print "tprakashttttttttt",type(attan.date_from)
# 						if not attan.date_to:
# 							a = dt.datetime.now() + dt.timedelta(days=4*365)
# 							print "*-*-*-*--*-*-*-*-*--*-*",a.date()
# 							attan.date_to = str(a.date())
#
# 						print attan.date_to
# 						td = dt.timedelta(hours=attan.hour_from)
# 						orignal_hour_from = (dt.datetime(2000,1,1)+td).strftime("%H:%M")
# 						print orignal_hour_from
# 						to = dt.timedelta(hours=attan.hour_to)
# 						orignal_hour_to = (dt.datetime(2000,1,1)+to).strftime("%H:%M")
# 						print "***********",type(orignal_hour_to)
#
# 						hour_from_temp = orignal_hour_from.split(':')
# 						hour_to_temp = orignal_hour_to.split(':')
#
# 						datetime_from = datetime.strptime(attan.date_from, '%Y-%m-%d')
# 						datetime_end = datetime.strptime(attan.date_to, '%Y-%m-%d')
#
# 						datetime_from = datetime_from.replace(hour=int(hour_from_temp[0]), minute=int(hour_from_temp[1]))
# 						datetime_end  = datetime_end.replace(hour=int(hour_to_temp[0]), minute=int(hour_to_temp[1]))
#
# 						print "d",datetime_from
# 						print "dd",datetime_end
#
#
# 						vals.update({'contract_id':rec.id,
# 							'department_id':rec.department_id and rec.department_id.id or False,
# 							'employee_id':rec.employee_id.id,
# 							'dayofweek':attan.dayofweek,
# 							'hour_from':attan.hour_from,
# 							'hour_to':attan.hour_to,
# 							'date_from':attan.date_from,
# 							'date_to':attan.date_to,
# 							'date_from_orignal':orignal_hour_from,
# 							'date_to_orignal':orignal_hour_to,
# 							'date_starting':datetime_from,
# 							'date_ending':datetime_end,
# 							'working_hours':rec.working_hours.id,
# 							'line_id':attan.id,
# 							'name':attan.name})
# 						re = self.env['working_schedule.calendar'].create(vals)
# 						print "creaaaaa",re
# 						vals.clear()
# 		return rec
#
#
# 	@api.multi
# 	def write(self, value):
# 		ret = super(hr_contract, self).write(value)
# 		print "+++++write calling++"
# 		#print "+++",vals
# 		vals={}
# 		for rec in self:
# 			if rec.id:
# 				sc = self.env['working_schedule.calendar'].search([('contract_id','=',rec.id)]).unlink()
#
#
# 			print "+working_hoursworking_hours++",rec.working_hours.id
# 			print "rec.state",rec.state
# 			if rec.working_hours and rec.state != 'close':
# 				res_cal = self.env['resource.calendar'].browse(rec.working_hours.id)
# 				if res_cal.attendance_ids:
# 					print "++m+",res_cal.attendance_ids
# 					for attan in res_cal.attendance_ids:
#
# 						print attan.date_from
# 						if not attan.date_to:
# 							a = dt.datetime.now() + dt.timedelta(days=4*365)
# 							print "*-*-*-*--*-*-*-*-*--*-*",a.date()
# 							attan.date_to = str(a.date())
#
#
# 						print "tttttttttt",type(attan.date_from)
# 						print attan.date_to
# 						td = dt.timedelta(hours=attan.hour_from)
# 						orignal_hour_from = (dt.datetime(2000,1,1)+td).strftime("%H:%M")
# 						print orignal_hour_from
# 						to = dt.timedelta(hours=attan.hour_to)
# 						orignal_hour_to = (dt.datetime(2000,1,1)+to).strftime("%H:%M")
# 						print "***********",type(orignal_hour_to)
#
# 						hour_from_temp = orignal_hour_from.split(':')
# 						hour_to_temp = orignal_hour_to.split(':')
#
# 						datetime_from = datetime.strptime(attan.date_from, '%Y-%m-%d')
# 						datetime_end = datetime.strptime(attan.date_to, '%Y-%m-%d')
#
# 						datetime_from = datetime_from.replace(hour=int(hour_from_temp[0]), minute=int(hour_from_temp[1]))
# 						datetime_end  = datetime_end.replace(hour=int(hour_to_temp[0]), minute=int(hour_to_temp[1]))
#
# 						print "d",datetime_from
# 						print "dd",datetime_end
#
# 						vals.update({'contract_id':rec.id,
# 							'department_id':rec.department_id and rec.department_id.id or False,
# 							'employee_id':rec.employee_id.id,
# 							'dayofweek':attan.dayofweek,
# 							'hour_from':attan.hour_from,
# 							'hour_to':attan.hour_to,
# 							'date_from':attan.date_from,
# 							'date_to':attan.date_to,
# 							'date_from_orignal':orignal_hour_from,
# 							'date_to_orignal':orignal_hour_to,
# 							'date_starting':datetime_from,
# 							'date_ending':datetime_end,
# 							'working_hours':rec.working_hours.id,
# 							'line_id':attan.id,
# 							'name':attan.name})
#
# 						re = self.env['working_schedule.calendar'].create(vals)
# 						vals.clear()
# 		return ret
#
#
# 	@api.multi
# 	def unlink(self):
# 		for con in self:
# 			sc = self.env['working_schedule.calendar'].search([('contract_id','=',con.id)]).unlink()
# 		ret = super(hr_contract, self).unlink()
# 		return ret
#
# class ResourceCalendarAttendance(models.Model):
#
# 	_inherit = "resource.calendar.attendance"
#
# 	date_from = fields.Date(string='Starting Date', required="1")
#
# 	@api.model
# 	def create(self, value):
# 		print "++++++creating"
# 		rec = super(ResourceCalendarAttendance, self).create(value)
# 		print "++++++r",rec
# 		return rec
#
#
# 	@api.multi
# 	def write(self, value):
# 		print "write calling"
# 		ret = super(ResourceCalendarAttendance, self).write(value)
# 		return ret
#
# class ResourceCalendar(models.Model):
#
# 	_inherit = "resource.calendar"
#
# 	@api.model
# 	def create(self, value):
# 		print "+++ResourceCalendar+++creating"
# 		rec = super(ResourceCalendar, self).create(value)
# 		print "++++++r",rec
# 		return rec
#
#
# 	@api.multi
# 	def write(self, value):
# 		vals={}
# 		ret = super(ResourceCalendar, self).write(value)
# 		for rec in self:
# 			print rec.id
# 			ws = self.env['working_schedule.calendar'].search([('working_hours','=',rec.id)])
# 			if ws:
# 				for res_att in rec.attendance_ids:
# 					print "line id",res_att.id
# 					wsline = self.env['working_schedule.calendar'].search([('line_id','=',res_att.id)])
# 					for line in wsline:
#
# 						print res_att.date_from
# 						if not res_att.date_to:
# 							a = dt.datetime.now() + dt.timedelta(days=4*365)
# 							print "*-*-*-*--*-*-*-*-*--*-*",a.date()
# 							res_att.date_to = str(a.date())
#
#
# 						print "tttttttttt",type(res_att.date_from)
# 						print res_att.date_to
# 						td = dt.timedelta(hours=res_att.hour_from)
# 						orignal_hour_from = (dt.datetime(2000,1,1)+td).strftime("%H:%M")
# 						print orignal_hour_from
# 						to = dt.timedelta(hours=res_att.hour_to)
# 						orignal_hour_to = (dt.datetime(2000,1,1)+to).strftime("%H:%M")
# 						print "***********",type(orignal_hour_to)
#
# 						hour_from_temp = orignal_hour_from.split(':')
# 						hour_to_temp = orignal_hour_to.split(':')
#
# 						datetime_from = datetime.strptime(res_att.date_from, '%Y-%m-%d')
# 						datetime_end = datetime.strptime(res_att.date_to, '%Y-%m-%d')
#
# 						datetime_from = datetime_from.replace(hour=int(hour_from_temp[0]), minute=int(hour_from_temp[1]))
# 						datetime_end  = datetime_end.replace(hour=int(hour_to_temp[0]), minute=int(hour_to_temp[1]))
#
# 						print "d",datetime_from
# 						print "dd",datetime_end
#
# 						vals.update({'contract_id':line.contract_id.id,
# 							'department_id':line.department_id and line.department_id.id or False,
# 							'employee_id':line.employee_id.id,
# 							'dayofweek':res_att.dayofweek,
# 							'hour_from':res_att.hour_from,
# 							'hour_to':res_att.hour_to,
# 							'date_from':res_att.date_from,
# 							'date_to':res_att.date_to,
# 							'date_from_orignal':orignal_hour_from,
# 							'date_to_orignal':orignal_hour_to,
# 							'date_starting':datetime_from,
# 							'date_ending':datetime_end,
# 							'working_hours':line.working_hours.id,
# 							'line_id':line.id,
# 							'name':res_att.name})
# 						print vals
# 						line.write(vals)
#
# 						print vals
# 						vals.clear()
#
# 			#attendance_ids
# 		return ret
#
# 	@api.multi
# 	def unlink(self):
# 		import pdb
# 		pdb.set_trace()
# 		for con in self:
# 			sc = self.env['working_schedule.calendar'].search([('line_id','=',con.id)]).unlink()
# 		ret = super(ResourceCalendar, self).unlink()
# 		return ret


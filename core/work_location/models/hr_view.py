from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class Employee(models.Model):

    _inherit = "hr.employee"
    
    work_location_for_employee=fields.Many2one('work.location',string="Work Location")
    work_location_history_ids = fields.One2many('work.location.history.lines','work_location_history_id',string="")
    
    @api.model
    def create(self, vals):
        ''' Method Overriden to update the History of  Work Location of an Employee...'''
        new_id =  super(Employee, self).create(vals)
        ## To Create the Work Location History ##    
        if vals.get('work_location_for_employee'):
            self.env['work.location.history.lines'].create({'work_location_history_id':new_id.id,'start_date':date.today(),'work_location_for_employee':vals['work_location_for_employee']})
        return new_id
       
    @api.multi
    def write(self, vals):
        ''' Method Overriden to update the History of  Work Location of an Employee....'''
        
        for obj in self:
            ## To Create/update the Work Location history lines. ##
            if vals.has_key('work_location_for_employee'):
                loc_obj = self.env['work.location.history.lines']
                loc_ids = loc_obj.search([('work_location_history_id','=',obj.id),('end_date','=',None)]) or False
                if not loc_ids :
                    loc_obj.create({'work_location_history_id':obj.id,'start_date':date.today(),'work_location_for_employee':vals['work_location_for_employee']})
                else:
                    loc_id = loc_ids[0].work_location_for_employee.id
                    if loc_id and loc_id != vals['work_location_for_employee']:
                        loc_ids.write({'work_location_history_id':obj.id,'end_date':date.today()})
                        loc_obj.create({'work_location_history_id':obj.id,'start_date':date.today(),'work_location_for_employee':vals['work_location_for_employee']})
        return super(Employee, self).write(vals)
    
class WorkLocationHistoryLines(models.Model):
    _name="work.location.history.lines"


    work_location_for_employee = fields.Many2one('work.location',string="Work Location")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    work_location_history_id = fields.Many2one("hr.employee",string="")
    
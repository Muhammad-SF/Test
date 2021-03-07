# -*- coding: utf-8 -*-
from odoo import fields,models,api
from odoo.tools.translate import _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import xlwt
import base64
import StringIO
import datetime

class sg_leave_export_summary_new(models.TransientModel):
    
    _name = "excel.sg.leave.summary.report.new"

    file = fields.Binary("Click On Download Link To Download Xls File", readonly = True)
    name = fields.Char("Name", default = 'generic summary.xls')
    

class evaluation_report_new(models.Model):
    _name="evaluation.report.new"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    department = fields.Many2one('hr.department',string='Department')
    note = fields.Text()

    @api.multi
    def eval_reporttt(self):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        borders = xlwt.Borders()
        border_style = xlwt.XFStyle()
        font = xlwt.Font()
        font.bold = True

        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        border_style = xlwt.XFStyle() 
        border_style.alignment = alignment
       
        header = xlwt.easyxf('font: bold 1, height 230')
        header1 = xlwt.easyxf('font: bold 1, height 230')
        header.alignment = alignment
        worksheet.write(1,4,'Report Employee Analysis',header)
        worksheet.col(0).width = 6000
        worksheet.col(1).width = 6000
        worksheet.col(5).width = 4000
        worksheet.col(6).width = 5000
        worksheet.write(3,0,'Period',header1)
        worksheet.write(4,0,'Company',header1)
        worksheet.write(5,0,'Department',header1)
        worksheet.write(7,0,'Job Position',header)
        worksheet.write(7,1,'Current Number of Employees',header1)
        worksheet.write(7,2,'Male',header)
        worksheet.write(7,3,'Female',header)
        worksheet.write(7,4,'Others',header)
        worksheet.write(7,5,'Average Age',header1)
        worksheet.write(7,6,'Total In',header)
        worksheet.write(7,7,'Total Out',header)
        worksheet.write(7,8,'Retention Rate (%)',header1)
        worksheet.write(7,9,'Average Salary',header1)

        if self.start_date and self.end_date:
            start = datetime.datetime.strptime(self.start_date, '%Y-%m-%d').strftime('%d/%m/%y')
            end = datetime.datetime.strptime(self.end_date, '%Y-%m-%d').strftime('%d/%m/%y')
            worksheet.write(3,1,str(start) + ' - ' + str(end) ,border_style)
     
        worksheet.write(4,1,self.env.user.company_id.name,border_style)

        if self.department:
            worksheet.write(5,1,self.department.name,border_style)
        else:
            worksheet.write(5,1,"All",border_style)

        job_posititon= False
        if self.department: 
            job_position = self.env['hr.job'].search([('department_id','=',self.department.id)])
        else:
            job_position = self.env['hr.job'].search([('company_id','=',self.env.user.company_id.id)])
        employees = False

        
        i = 9
        for position in job_position:
            worksheet.write(i,0,position.name)
            employees = self.env['hr.employee'].search([('job_id','=',position.id)])
            male_employees = self.env['hr.employee'].search([('job_id','=',position.id),('gender','=','male')])
            female_employees = self.env['hr.employee'].search([('job_id','=',position.id),('gender','=','female')])
            other_employees = self.env['hr.employee'].search([('job_id','=',position.id),('gender','=','other')])
            worksheet.write(i,1,len(employees),border_style)
            worksheet.write(i,2,len(male_employees),border_style)
            worksheet.write(i,3,len(female_employees),border_style)
            worksheet.write(i,4,len(other_employees),border_style)
            sum_age = 0
            sum_salary = 0
            avg_age = 0
            avg_salary = 0
            for employee in employees:
                sum_age += employee.age
                sum_salary += employee.current_salary
            if len(employees):    
                avg_age = sum_age/len(employees)
                avg_salary = sum_salary/ len(employees)
            worksheet.write(i,5,round(avg_age,2),border_style)
            
            employees_in = False
            if self.start_date and self.end_date:
                employees_in = self.env['hr.employee'].search([('job_id','=',position.id),('join_date','>=',self.start_date),('join_date','<=',self.end_date)])
            if employees_in:
                worksheet.write(i,6,len(employees_in),border_style)
            else:
                worksheet.write(i,6,'0',border_style)

            count=0
            employees_out = False
            if self.start_date and self.end_date:
                employees_out = self.env['hr.employee'].search([('job_id','=',position.id)])
                for emp in employees_out:
                    contract = self.env['hr.contract'].search([('employee_id','=',emp.id)],order= 'id desc')
                    if contract:
                        contract1 = contract[0]
                        
                        if self.start_date <= contract1.date_end and self.end_date >= contract1.date_end and emp.employment_status12 != 'active':
                            count += 1

            retention_rate = 0
            active_employee = self.env['hr.employee'].search([('job_id','=',position.id),('active','=',True)])
            if active_employee:
                retention_rate = ((len(active_employee) - count)/float(len(active_employee))) * 100
            worksheet.write(i,8,round(retention_rate,2),border_style)
                            
            if employees_out:
                worksheet.write(i,7,count,border_style)
            else:
                worksheet.write(i,7,'0',border_style)  
                       
            worksheet.write(i,9,round(avg_salary,2),border_style)
            i+=1
    

        fp = StringIO.StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        res = base64.encodestring(data)
        date = datetime.datetime.strptime(str(datetime.date.today()), '%Y-%m-%d').strftime('%d/%m/%y')
        module_rec = self.env['excel.sg.leave.summary.report.new'].create({'name': 'Employee Analysis Report '+str(date)+'.xls', 'file' : res})
        return {
          'name': _('Employee Analysis Report'),
          'res_id' : module_rec.id,
          'view_type': 'form',
          "view_mode": 'form',
          'res_model': 'excel.sg.leave.summary.report.new',
          'type': 'ir.actions.act_window',
          'target': 'new',
          # 'context': context,
          }    


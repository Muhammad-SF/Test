# -*- coding: utf-8 -*-

from openerp import models, api, _, fields
from openerp.exceptions import Warning

import time

class assignment_grade(models.Model):
    _name = 'assignment.grade'
    _description = 'Assignment Grade'
    _order = 'mark_to desc'
    
    name = fields.Char('Grade Name', required=True)
    mark_from = fields.Integer('From', required=True)
    mark_to = fields.Integer('To', required=True)
    
    @api.returns('self')
    def find(self, mark):
        grade_ids = self.search([('mark_from', '<=', mark), ('mark_to', '>=', mark)])
        return grade_ids and grade_ids[0].id or False
    
class class_assignment(models.Model):
    _name = 'class.assignment'
    _description = 'Class Assignment'
    _order = 'name desc'
    
    name = fields.Char('Reference')
    title = fields.Char('Title')
    description = fields.Text('Description')
    date_due = fields.Date('Due Date')
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent'), ('evaluated', 'Evaluated')], 'Status', default='draft')
    class_id = fields.Many2one('school.standard', 'Course')
    intake_id = fields.Many2one('academic.year', 'Intake')
    student_assign_ids = fields.One2many('student.assignment', 'assignment_id', 'Student Assignments')
    created_user_id = fields.Many2one('res.users', 'Created By', default=lambda self: self.env.user)
    created_date = fields.Date('Created On', default=time.strftime('%Y-%m-%d'))
    attachment = fields.Binary('Assignment File')
    file_name = fields.Char('File Name')
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('class.assignment') or 'New'
        return super(class_assignment, self).create(vals)
    
    @api.multi
    def action_evaluate(self):
        for line in self.student_assign_ids:
            if line.state == 'evaluated':
                continue
            if line.state != 'submitted':
                raise Warning("All students not submitted!")
            if line.marks <= 0:
                raise Warning("Enter Marks for %s!"%line.student_id.name)
            line.state = 'evaluated'
        self.state = 'evaluated'
        
    @api.onchange('class_id','intake_id')
    def _onchange_class(self):
        if self.class_id:
            student_list = []
            student_ids = self.env['student.student'].search([('standard_id','=',self.class_id.id),('state','=','done'),('year','=',self.intake_id.id)])
            if student_ids:
                for student in student_ids:
                    student_list.append((0, 1, {'student_id': student.id}))
                self.student_assign_ids = student_list
            else:
                self.student_assign_ids = False
        else:
            self.student_assign_ids = False
            
    @api.multi
    def action_send(self):
        if not self.attachment:
            raise Warning("Assignment not uploaded !")
        for assign in self.student_assign_ids:
            assign.state = 'sent'
        self.state = 'sent'
            
class student_assignment(models.Model):
    _name = 'student.assignment'
    _description = 'Student Assignment'
    _order = 'name desc'
    
    @api.one
    @api.depends('assignment_id', 'assignment_id.name', 'assignment_id.title', 'assignment_id.date_due', 'assignment_id.class_id',
        'assignment_id.attachment')
    def _get_assignment_details(self):
        self.name = self.assignment_id.name
        self.title = self.assignment_id.title
        self.description = self.assignment_id.description
        self.date_due = self.assignment_id.date_due
        self.class_id = self.assignment_id.class_id.id
        self.created_user_id = self.assignment_id.created_user_id.id
        self.created_date = self.assignment_id.created_date
        self.attachment = self.assignment_id.attachment
        self.file_name = self.assignment_id.file_name
        
    @api.multi
    def action_submit(self):
        if not self.attachment_result:
            raise Warning("Assignment Result not uploaded !")
        self.state = 'submitted'
        
    @api.one
    @api.depends('marks')
    def _find_grade(self):
        self.grade_id = self.env['assignment.grade'].find(self.marks)
        
    student_id = fields.Many2one('student.student', 'Student')
    assignment_id = fields.Many2one('class.assignment', 'Assignment')
    name = fields.Char('Reference', compute=_get_assignment_details, store=True)
    title = fields.Char('Title', compute=_get_assignment_details, store=True)
    description = fields.Text('Description', compute=_get_assignment_details, store=True)
    date_due = fields.Date('Due Date', compute=_get_assignment_details, store=True)
    class_id = fields.Many2one('school.standard', 'Course', compute=_get_assignment_details, store=True)
    created_user_id = fields.Many2one('res.users', 'Created By', compute=_get_assignment_details, store=True)
    created_date = fields.Date('Created On', compute=_get_assignment_details, store=True)
    marks = fields.Integer('Marks')
    grade_id = fields.Many2one('assignment.grade', 'Grade', compute=_find_grade)
    attachment = fields.Binary('Assignment File', compute=_get_assignment_details, store=True)
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent'), ('submitted', 'Submitted'),
        ('evaluated', 'Evaluated')], 'Status', default='draft')
    file_name = fields.Char('File Name', compute=_get_assignment_details, store=True)
    attachment_result = fields.Binary('Assignment Result')
    file_result = fields.Char('File Name result')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

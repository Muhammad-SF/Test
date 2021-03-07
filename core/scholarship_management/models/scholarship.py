# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.misc import formatLang

class Scholarship(models.Model):
    _name = 'scholarship'
    _inherit = 'mail.thread'
    _description = 'Scholarship'
    _order = 'id desc'

    @api.depends('quantity')
    def compute_available_qty(self):
        for record in self:
            application_ids = self.env['scholarship.application'].search([('scholarship_id','=',record.id),('state','=','approve')]).ids
            record.application_qty = len(application_ids)
            record.available_qty = record.quantity - len(application_ids)

    name = fields.Char('Name', required=True)
    provider = fields.Char('Provider')
    amount = fields.Monetary('Amount', track_visibility='always', currency_field='currency_id')
    quantity = fields.Float('Number of Scholarships Available', default=1.0)
    available_qty = fields.Float(compute='compute_available_qty', string='Availability')
    application_qty = fields.Float(compute='compute_available_qty', string='Application Count')
    currency_id = fields.Many2one('res.currency', 'Currency')
    duration = fields.Integer('Duration')
    duration_type = fields.Selection([('month','Month'),('year','Year')], 'Duration Type')
    document_ids = fields.One2many('scholarship.document', 'scholarship_id', string='Documents', copy=True)
    student_ids = fields.One2many('scholarship.student', 'scholarship_id', string='Students', copy=True)
    requirement_ids = fields.One2many('scholarship.requirement', 'scholarship_id', string='Requirements', copy=True)
    state = fields.Selection([('draft','Draft'),('progress','In Progress'),('cancel','Suspended')], string='Status', default='draft')

    @api.multi
    def button_progress(self):
        self.write({'state': 'progress'})

    @api.multi
    def button_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def button_resume(self):
        self.write({'state': 'progress'})

    @api.multi
    def action_view_applications(self):
        action = self.env.ref('scholarship_management.action_scholarship_application').read()[0]
        action['domain'] = [('scholarship_id','in',self.ids),('state','=','approve')]
        return action

Scholarship()

class ScholarshipDocument(models.Model):
    _name = 'scholarship.document'
    _description = 'Scholarship Document'

    name = fields.Char('Name', required=True)
    file = fields.Binary('Attachment')
    filename = fields.Char('Filename')
    scholarship_id = fields.Many2one('scholarship', string='Scholarship')
    application_id = fields.Many2one('scholarship.application', string='Scholarship Application')

ScholarshipDocument()

class ScholarshipStudent(models.Model):
    _name = 'scholarship.student'
    _description = 'Scholarship Student'

    scholarship_id = fields.Many2one('scholarship', string='Scholarship')
    student_id = fields.Many2one('student.student', string='Student')
    pid = fields.Char(related='student_id.pid', string="Student ID", readonly=True)
    standard_id = fields.Many2one('school.standard', related='student_id.standard_id', string="Course", readonly=True)
    year_id = fields.Many2one('academic.year', related='student_id.year', string="Intake", readonly=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

ScholarshipStudent()

class ScholarshipRequirement(models.Model):
    _name = 'scholarship.requirement'
    _description = 'Scholarship Requirement'

    scholarship_id = fields.Many2one('scholarship', string='Scholarship')
    type = fields.Selection([('attendance','Attendance'),('gpa','GPA')], string='Type')
    requirement = fields.Integer('Requirement')

    @api.onchange('type', 'requirement')
    def onchange_requirement(self):
        warning = {}
        if (self.type == 'attendance') and (self.requirement > 100 or self.requirement < 0):
            self.requirement = 0.0
            warning = {'title': 'Value Error!', 'message': 'Requirement value should be between 0 to 100'}
        return {'warning': warning}

ScholarshipRequirement()

class ScholarshipApplication(models.Model):
    _name = 'scholarship.application'
    _inherit = 'mail.thread'
    _description = 'Scholarship Application'
    _order = 'id desc'

    student_id = fields.Many2one('student.student', string='Student')
    pid = fields.Char(related='student_id.pid', string="Student ID", readonly=True)
    standard_id = fields.Many2one('school.standard', related='student_id.standard_id', string="Course", readonly=True)
    year_id = fields.Many2one('academic.year', related='student_id.year', string="Intake", readonly=True)
    scholarship_id = fields.Many2one('scholarship', string='Scholarship to Apply')
    currency_id = fields.Many2one('res.currency', related='scholarship_id.currency_id', string='Currency')
    amount = fields.Monetary(related='scholarship_id.amount', string="Scholarship Amount", currency_field='currency_id', readonly=True)
    document_ids = fields.One2many('scholarship.document', 'application_id', string='Documents', copy=True)
    state = fields.Selection([('draft','Draft'),('submit','Submitted'),('approve','Approved'),('reject','Rejected'),('cancel','Cancelled')], string='Status', default='draft')

    @api.onchange('scholarship_id')
    def onchange_scholarship_id(self):
        if self.scholarship_id:
            data_list = []
            for line in self.scholarship_id.document_ids:
                data_list.append((0,0,{'name': line.name}))
            self.document_ids = data_list

    @api.depends('scholarship_id','amount')
    def name_get(self):
        result = []
        for record in self:
            name = record.scholarship_id.name + ': ' + formatLang(self.env, record.amount, currency_obj=record.currency_id)
            result.append((record.id, name))
        return result

    @api.multi
    def button_submit(self):
        self.write({'state': 'submit'})

    @api.multi
    def button_approve(self):
        self.write({'state': 'approve'})

    @api.multi
    def button_reject(self):
        self.write({'state': 'reject'})

    @api.multi
    def button_cancel(self):
        self.write({'state': 'cancel'})

ScholarshipApplication()
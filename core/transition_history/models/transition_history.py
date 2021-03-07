# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TransitionHistoryInherited(models.Model):
    _inherit = 'hr.employee'

    transition_line = fields.One2many('transition.history', 'inv_transition')


class TransitionHistory(models.Model):
    _name = 'transition.history'
    transition = fields.Char('Transition')
    date_to = fields.Date('Date To')
    company_to = fields.Char('Company To')
    department_to = fields.Char('Department To')
    job_position = fields.Char('Job Position To')
    work_location = fields.Char('Work Location To')
    reason = fields.Char('Reason')
    inv_transition = fields.Many2one('hr.employee', "Employee")


class EmployeePromotion(models.Model):
    _inherit = 'employee.promotion'

    def action_approve12(self):
        # super(TransitionEmployee, self).action_approve12()
        train_list = []
        self.state = "approved"
        self.employee.cessation_date = self.promotion_time
        contracts = self.env['hr.contract'].search([('employee_id', '=', self.employee.id)])
        jobs = self.job_position_to_apply.training_required_ids.ids
        for line in jobs:
            training_line_obj = self.env['list.conducts'].search([('program_id','=', line),
                                                                ('employee_id','=', self.employee.id),
                                                                ])
            for training in training_line_obj:
                if training.status_list == 'success':
                    if line in jobs:
                        jobs.remove(line)
            if training_line_obj:
                train_list.append(line)
        if jobs:
            self.env['transition.training'].create({
                        'employee': self.employee.id,
                        'job_training' : self.job_position_to_apply.id,
                        'trainings_todo_ids' : [(6, 0, jobs)]
                        })
        for rec in contracts:
            if rec.state != 'close':
                rec.date_end = self.promotion_time

        obj = self.env["transition.history"].create({"job_position": self.job_position_to_apply.name.encode('ascii','ignore'),
                                                     "transition": "Promotion",
                                                     "department_to": self.department_to_apply.name,
                                                     # "work_location": self.work_location_promotion.name,
                                                     "date_to": self.promotion_time})
        self.employee.transition_line = [(4, obj.id)]


class EmployeeDemotion(models.Model):
    _inherit = 'employee.demotion'

    def action_approve12(self):
        self.state = "approved"
        self.employee.cessation_date = self.demotion_time
        contracts = self.env['hr.contract'].search([('employee_id', '=', self.employee.id)])
        for rec in contracts:
            if rec.state != 'close':
                rec.date_end = self.demotion_time
        obj = self.env["transition.history"].create({"job_position": self.job_position_to_demotion.name.encode('ascii','ignore'),
                                                     "transition": "Demotion",
                                                     "department_to": self.department_to_demotion.name,
                                                     # "work_location": self.work_location_demotion.name,
                                                     "date_to": self.demotion_time})
        self.employee.transition_line = [(4, obj.id)]


class EmployeeMutation(models.Model):
    _inherit = 'employee.mutation'

    def action_approve12(self):
        self.state = "approved"
        self.employee.cessation_date = self.mutation_time
        contracts = self.env['hr.contract'].search([('employee_id', '=', self.employee.id)])
        for rec in contracts:
            if rec.state != 'close':
                rec.date_end = self.mutation_time
        obj = self.env["transition.history"].create({"work_location": self.company_for_mutation.name.encode('ascii','ignore'),
                                                     "transition": "Mutation",
                                                     "department_to": self.department_to_mutation.name,
                                                     "job_position": self.department_to_mutation.name,
                                                     "date_to": self.mutation_time})
        self.employee.transition_line = [(4, obj.id)]


class EmployeeTermination(models.Model):
    _inherit = 'employee.termination'

    def action_approve12(self):
        self.state = "approved"
        self.employee.cessation_date = self.cessation_date
        contracts = self.env['hr.contract'].search([('employee_id', '=', self.employee.id)])
        for rec in contracts:
            if rec.state != 'close':
                rec.date_end = self.cessation_date
        history_ids = self.env['employee.history'].search([('history_id','=',self.employee.id)],order= 'id desc')
        if history_ids:
            history_id = history_ids[0]
            history_id.cessation_date = self.cessation_date
        obj = self.env["transition.history"].create({"work_location": "----",
                                                     "transition": "Termination",
                                                     "department_to": "----",
                                                     "reason": self.termination_reason,
                                                     "date_to": self.termination_date,
                                                     "job_position": "----",
                                                     "company_to": "----",
                                                     "work_location": "----"})
        self.employee.transition_line = [(4, obj.id)]


class EmployeeResignation(models.Model):
    _inherit = 'resignation.request'

    def action_approve_department_manager(self):
        super(EmployeeResignation, self).action_approve_department_manager()
        self.employee_id.cessation_date = self.cessation_date
        contracts = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
        for rec in contracts:

            if rec.state != 'close':
                rec.date_end = self.cessation_date 
        history_ids = self.env['employee.history'].search([('history_id','=',self.employee_id.id)],order= 'id desc')
        if history_ids:
            history_id = history_ids[0]
            history_id.cessation_date = self.cessation_date        
                
        obj = self.env["transition.history"].create({"work_location": "----",
                                                     "transition": "Resignation",
                                                     "department_to": "----",
                                                     "reason": self.resignation_note,
                                                     "date_to": self.resignation_date,
                                                     "job_position": "----",
                                                     "company_to": "----",
                                                     "work_location": "----"})
        self.employee_id.transition_line = [(4, obj.id)]





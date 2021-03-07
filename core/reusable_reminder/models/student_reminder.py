# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StudentReminder(models.Model):
    _inherit = 'student.reminder'

    @api.model
    def check_user(self):
        '''Method to get default value of logged in Student'''
        return self.env['student.student'].search([('user_id', '=',
                                                    self._uid)]).id

    intake_id = fields.Many2one('academic.year', 'Intake')
    course_id = fields.Many2one('school.standard', 'Course')
    attachment = fields.Binary('Attachment')
    file_name = fields.Char('File Name')
    url_fields = fields.Char('URL')
    teacher_id = fields.Many2one('hr.employee','Teacher', domain=[('is_school_teacher','=',True)])
    stu_id = fields.Many2one('student.student', 'Student Name', required=False,
                             default=check_user)
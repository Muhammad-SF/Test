# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class StudentReminderWizard(models.TransientModel):
    _name = 'student.reminder.wizard'

    all_student = fields.Boolean('All Students')
    all_teacher = fields.Boolean('All Teachers')
    student_ids = fields.Many2many('student.student', string='Student Name')
    name = fields.Char('Title')
    date = fields.Date('Date')
    description = fields.Text('Description')
    intake_id = fields.Many2one('academic.year', 'Intake')
    course_id = fields.Many2one('school.standard', 'Course')
    color = fields.Integer('Color Index', default=0)
    attachment = fields.Binary('Attachment')
    file_name = fields.Char('File Name')
    url_fields = fields.Char('URL')
    teacher_ids = fields.Many2many('hr.employee', domain=[('is_school_teacher','=',True)], string='Teacher')

    @api.onchange('intake_id','course_id')
    def onchange_course_intake_id(self):
        if self.intake_id or self.course_id:
            self.student_ids = False

    @api.multi
    def create_reminder(self, student_id, teacher_id):
        vals = {
                'date': self.date,
                'name':self.name,
                'intake_id':self.intake_id and self.intake_id.id,
                'course_id':self.course_id and self.course_id.id,
                'description':self.description,
                'attachment':self.attachment,
                'file_name':self.file_name,
                'url_fields':self.url_fields,
                'create_uid':self.env.uid,
            }
        if teacher_id:
            vals.update({'teacher_id':teacher_id.id,})
        if student_id:
            vals.update({'stu_id':student_id.id,})
        return self.env['student.reminder'].create(vals)

    @api.multi
    def send_reminder_mail(self, reminder_id, student_teacher_id, template, is_teacher):
        attachments = self.env['ir.attachment']
        email_vals = {
                        #'auto_delete':True,
                        'subject':reminder_id.name,
                        'email_from':self.env.user.partner_id.email or '',
                        'body_html':str(reminder_id.description)}
        email = self.env['mail.mail'].sudo().create(email_vals)
        if reminder_id.file_name and reminder_id.attachment:
            val = {'name': reminder_id.file_name,
                    'datas': reminder_id.attachment,
                    'datas_fname': reminder_id.file_name,
                    'res_id': reminder_id.id,
                    'res_model': 'student.reminder',
                    }
            attachment_id = attachments.sudo().create(val)
            email.sudo().attachment_ids = [(6, 0, [attachment_id.id])]
        if is_teacher:
            email.sudo().email_to = student_teacher_id.work_email
        if not is_teacher:
            email.sudo().email_to = student_teacher_id.email
        email.sudo().send()


    @api.multi
    def generate_student_reminder(self):
        student_template_id = self.env.ref('reusable_reminder.student_reminder_template')
        teacher_template_id = self.env.ref('reusable_reminder.teacher_reminder_template')
        # only all student not any thing else
        if self.all_student and not self.intake_id and not self.course_id and not self.student_ids and not self.teacher_ids and not self.all_teacher:
            student_ids = self.env['student.student'].search([('state','=','done')])
            for student in student_ids:
                reminder_id = self.create_reminder(student, False)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, student, student_template_id, is_teacher=False)

        # only intake is available and all student
        if self.intake_id and self.all_student and not self.course_id and not self.student_ids and not self.all_teacher and not self.teacher_ids:
            intake_student_ids = self.env['student.student'].search([('year','=',self.intake_id.id), ('state','=','done')])
            for student in intake_student_ids:
                reminder_id = self.create_reminder(student, False)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, student, student_template_id, is_teacher=False)

        # only intake is available and selected student
        if self.intake_id and self.student_ids and not self.course_id and not self.all_student and not self.all_teacher and not self.teacher_ids:
            for student in self.student_ids:
                reminder_id = self.create_reminder(student, False)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, student, student_template_id, is_teacher=False)
        
        # if intake and course and all student but not selected student
        if self.intake_id and self.course_id and self.all_student and not self.student_ids and not self.all_teacher and not self.teacher_ids:
            for student in self.course_id.student_ids:
                if student.state == 'done':
                    reminder_id = self.create_reminder(student, False)
                    if reminder_id:
                        self.send_reminder_mail(reminder_id, student, student_template_id, is_teacher=False)

        # only intake, course, selected student are available and not for all student
        if self.student_ids and self.intake_id and self.course_id  and not self.all_student and not self.all_teacher and not self.teacher_ids:
            for student in self.student_ids:
                reminder_id = self.create_reminder(student, False)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, student, student_template_id, is_teacher=False)

        # Teacher reminder
        # only all teacher not any thing else
        if self.all_teacher and not self.all_student and not self.intake_id and not self.course_id and not self.student_ids and not self.teacher_ids:
            teacher_ids = self.env['hr.employee'].search([('is_school_teacher','=',True)])
            for teacher in teacher_ids:
                reminder_id = self.create_reminder(False, teacher)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, teacher, teacher_template_id, is_teacher=True)
        
        # only intake is available and all student and all teacher
        if self.intake_id and self.all_student and not self.course_id and not self.student_ids and self.all_teacher and not self.teacher_ids:
            intake_student_ids = self.env['student.student'].search([('year','=',self.intake_id.id), ('state','=','done')])
            teacher_ids = self.env['hr.employee'].search([('is_school_teacher','=',True)])
            for student in intake_student_ids:
                reminder_id = self.create_reminder(student, False)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, student, student_template_id, is_teacher=False)
            for teacher in teacher_ids:
                reminder_id = self.create_reminder(False, teacher)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, teacher, teacher_template_id, is_teacher=True)

        # only intake is available and selected student and selected teacher
        if self.intake_id and self.student_ids and not self.course_id and not self.all_student and not self.all_teacher and self.teacher_ids:
            for student in self.student_ids:
                reminder_id = self.create_reminder(student, False)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, student, student_template_id, is_teacher=False)
            for teacher in self.teacher_ids:
                reminder_id = self.create_reminder(False, teacher)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, teacher, teacher_template_id, is_teacher=True)

        # if intake and course and all student and all teacher but not selected student and not selected teacher
        if self.intake_id and self.course_id and self.all_student and not self.student_ids and self.all_teacher and not self.teacher_ids:
            teacher_ids = self.env['hr.employee'].search([('is_school_teacher','=',True)])
            for student in self.course_id.student_ids:
                if student.state == 'done':
                    reminder_id = self.create_reminder(student, False)
                    if reminder_id:
                        self.send_reminder_mail(reminder_id, student, student_template_id, is_teacher=False)
            for teacher in teacher_ids:
                reminder_id = self.create_reminder(False, teacher)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, teacher, teacher_template_id, is_teacher=True)

        # only intake, course, selected student and selected teacher are available and not for all student and not for all teacher
        if self.student_ids and self.intake_id and self.course_id  and not self.all_student and not self.all_teacher and self.teacher_ids:
            for student in self.student_ids:
                reminder_id = self.create_reminder(student, False)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, student, student_template_id, is_teacher=False)
            for teacher in self.teacher_ids:
                reminder_id = self.create_reminder(False, teacher)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, teacher, teacher_template_id, is_teacher=True)

        # all student and all teacher not any thing else
        if self.all_student and self.all_teacher and not self.intake_id and not self.course_id and not self.student_ids and not self.teacher_ids:
            teacher_ids = self.env['hr.employee'].search([('is_school_teacher','=',True)])
            student_ids = self.env['student.student'].search([('state','=','done')])
            for teacher in teacher_ids:
                reminder_id = self.create_reminder(False, teacher)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, teacher, teacher_template_id, is_teacher=True)
            for student in student_ids:
                reminder_id = self.create_reminder(student, False)
                if reminder_id:
                    self.send_reminder_mail(reminder_id, student, student_template_id, is_teacher=False)



        return {
                'name': _('Reminder'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'student.reminder',
                'type': 'ir.actions.act_window',
                'domain': []}
        

class StudentStudent(models.Model):
    _inherit = 'student.student'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        student_list = []
        if self._context.get('student_reminder', False) and self._context.get('reminder_course_id', False):
            course_id = self.env['school.standard'].browse(self._context.get('reminder_course_id'))
            for student in course_id.student_ids:
                if student and student.state == 'done':
                    student_list.append(student.id)
        if self._context.get('student_reminder', False) and self._context.get('reminder_intake_id', False) and not self._context.get('reminder_course_id', False):
            intake_id = self.env['academic.year'].browse(self._context.get('reminder_intake_id'))
            student_ids = self.env['student.student'].search([('year','=',intake_id.id), ('state','=','done')])
            student_list = student_list + student_ids.ids
        domain = [('id', 'in', list(set(student_list)))]
        if student_list:
            recs = self.search(domain + args, limit=limit)
        else:
            recs = self.search(args, limit=limit)
        return recs.name_get()

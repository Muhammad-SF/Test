# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectTaskHM(models.Model):
    _inherit = 'project.task'

    @api.onchange('date_deadline')
    def onchange_date_deadline(self):
#         print "Onchanges date deadline------------------",self.date_deadline, self._ids, self._origin.id
        error = False
        notification_msg = ''
        if self.date_deadline:
            project_limit = self.env['ir.values'].get_default('project.config.settings', 'proj_limit')
            task_limit = self.env['ir.values'].get_default('project.config.settings', 'limit_task')
#             print "Project limit----------------",project_limit, task_limit
            if task_limit:
                task_objs = []
                domain = [('id', '!=', None),
                          ('date_deadline','!=', False)]
                
#                 print "self.id-----------------",self.id
                if self._origin.id:
                    domain.append(('id', '!=', self._origin.id))
                
                if project_limit == 'in_project':
                    domain.append(('project_id', '=', self.project_id.id))
                    notification_msg = """This task can’t use this date as Deadline.
                    The number of task’s limit with the same deadline in a project is reached %d. 
                    Choose other deadline or do changes to the number of Task’s limit in Deadline Management configuration"""
                     
                elif project_limit == 'cross_project':
                    notification_msg = """This task can’t use this date as Deadline. 
                    The number of task’s limit with the same deadline in Cross project is reached %d. 
                    Choose other deadline or do changes to the number of Task’s limit in Deadline Management configuration                     
                    """
                    
                task_objs = self.env['project.task'].search(domain)
#                 print "task objs---------------",domain, task_objs
                
                task_list = task_objs.filtered(lambda r:datetime.strptime(r.date_deadline, "%Y-%m-%d %H:%M:%S").date()
                                                             == datetime.strptime(self.date_deadline, "%Y-%m-%d %H:%M:%S").date())
#                 print "Task list--------------",task_list
                
                if task_list and len(task_list) >= int(task_limit):
                    error = True
                    self.date_deadline = False
                    notification_msg = notification_msg%int(task_limit)
#                         raise osv.except_osv(_('Invalid Action!'), _('You can not delete an invoice which is not cancelled. You should refund it instead.'))
               
        if error:
            return {'values':{'date_deadline':False}, 'warning': {'title': "Warning", 'message': notification_msg}}
        else:
            return



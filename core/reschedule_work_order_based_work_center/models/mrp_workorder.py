# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'


    @api.onchange('date_planned_start', 'date_planned_finished')
    def onchange_date_planeed(self):
        res = {}
        workorder_ids = self._origin.will_affect_to()
        if workorder_ids[0]:
            res['warning'] = {'title': _('Warning'), 'message': _(
                'Are you sure you want to reschedule work order ? It may affect these workorders.\n{}'.format(','.join(workorder_ids[0].mapped('workorder_id'))))}
        return res

    @api.one
    def will_affect_to(self):
        workorder_ids = self.search(
            [('id', '!=', self.id), ('workcenter_id', '=', self.workcenter_id.id), '|', '&',
             ('date_planned_start', '<=', self.date_planned_start),
             ('date_planned_finished', '>=', self.date_planned_start), '&',
             ('date_planned_start', '<=', self.date_planned_finished),
             ('date_planned_finished', '>=', self.date_planned_finished)])
        return workorder_ids


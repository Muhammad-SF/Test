# -*- coding: utf-8 -*-

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    member_ids = fields.Many2many('res.users', 'user_user_rel',
                                  'user_is', 'users_id', string="Members",
                                  compute="_compute_members")

    def _compute_members(self):
        for user in self:
            teams = self.env['timesheet.team'].search([('leader_ids', 'in', user.id)])
            all_member = []
            for team in teams:
                all_member.extend(team.member_ids.mapped('user_id').ids)
                if all_member:
                    user.member_ids = [(6, 0, all_member)]
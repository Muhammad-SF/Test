# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.exceptions import UserError


class TimesheetTeam(models.Model):
    _name = 'timesheet.team'
    _description = "Timesheet Team"

    name = fields.Char(string="Team Name", required=True)
    leader_ids = fields.Many2many('res.users', 'timesheet_team_user_rel',
                                  'tteam_id', 'user_id', string="Leader")
    members = fields.Many2many('res.users', 'team_member_user_rel', 'team_id', 'user_id', compute="_compute_members", string="Members", store=True)
    member_ids = fields.One2many('timesheet.member', 'timesheet_team_id', string="Members")

    @api.depends('member_ids.user_id')
    def _compute_members(self):
        for team in self:
            all_member = team.member_ids.mapped('user_id').ids
            if all_member:
                team.members = [(6, 0, all_member)]

    @api.model
    def create(self, vals):
        res = super(TimesheetTeam, self).create(vals)
        for leader in res.leader_ids:
            teams = self.env['timesheet.team'].search([('leader_ids', 'in', leader.id)])
            if teams:
                all_member = teams.mapped('member_ids').mapped('user_id').ids
                if all_member:
                    leader.write({'member_ids': [(6, 0, all_member)]})
        self.env['ir.rule'].clear_caches()
        return res

    @api.multi
    def write(self, vals):
        res = super(TimesheetTeam, self).write(vals)
        for leader in self.leader_ids:
            teams = self.env['timesheet.team'].search([('leader_ids','in', leader.id)])
            if teams:
                all_member = teams.mapped('member_ids').mapped('user_id')
                if all_member:
                    leader.write({'member_ids': [(6, 0, all_member.ids)]})
        self.env['ir.rule'].clear_caches()
        return res

    @api.multi
    def unlink(self):
        leaders = self.leader_ids
        super(TimesheetTeam, self).unlink()
        for leader in leaders:
            teams = self.env['timesheet.team'].search([('leader_ids', 'in', leader.id)])
            if teams:
                all_member = teams.mapped('member_ids').mapped('user_id')
                leader.write({'member_ids': [(6, 0, all_member.ids or [])]})
            else:
                leader.write({'member_ids': [(6, 0, [])]})
        self.env['ir.rule'].clear_caches()


class TimesheetMember(models.Model):
    _name = 'timesheet.member'
    _description = "Timesheet Member"

    user_id = fields.Many2one('res.users', string="User")
    role = fields.Char(string="Role")
    timesheet_team_id = fields.Many2one('timesheet.team')


# class AccountAnalyticLine(models.Model):
#     _inherit = 'account.analytic.line'
#
#     @api.model
#     def create(self, vals):
#         res = super(AccountAnalyticLine, self).create(vals)
#         admin = self.env.user.has_group('std_timesheet_access_rights.timesheet_admin')
#         manager = self.env.user.has_group('hr_timesheet.group_hr_timesheet_user')
#         if manager:
#             pass
#         if admin and not manager and self.user_id.id != self.env.user.id:
#             raise Warning(_("You don't have access to create record!\nPlease contact your system Administrator."))
#         return res
#
#     @api.multi
#     def write(self, vals):
#         res = super(AccountAnalyticLine, self).write(vals)
#         admin = self.env.user.has_group('std_timesheet_access_rights.timesheet_admin')
#         manager = self.env.user.has_group('hr_timesheet.group_hr_timesheet_user')
#         if manager:
#             pass
#         elif admin and not manager and self.user_id.id != self.env.user.id:
#             raise Warning(_("You don't have access to update record!\nPlease contact your system Administrator."))
#         return res
#
#     @api.multi
#     def unlink(self):
#         admin = self.env.user.has_group('std_timesheet_access_rights.timesheet_admin')
#         manager = self.env.user.has_group('hr_timesheet.group_hr_timesheet_user')
#         if manager:
#             pass
#         if admin and not manager and self.user_id.id != self.env.user.id:
#             raise Warning(_("You can't delete this record!\nPlease contact your system Administrator."))
#         return super(AccountAnalyticLine, self).unlink()


class HrTimesheetSheetSheet(models.Model):
    _inherit = 'hr_timesheet_sheet.sheet'

    # state2 = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed')], copy=False, default='draft',
    #                           string='Status')

    @api.model
    def create(self, vals):
        res = super(HrTimesheetSheetSheet, self).create(vals)
        admin = self.env.user.has_group('std_timesheet_access_rights.timesheet_admin')
        manager = self.env.user.has_group('hr_timesheet.group_hr_timesheet_user')
        if manager:
            pass
        if admin and not manager and self.user_id.id != self.env.user.id:
            raise Warning(_("You don't have access to create record!\nPlease contact your system Administrator."))
        return res

    @api.multi
    def write(self, vals):
        res = super(HrTimesheetSheetSheet, self).write(vals)
        admin = self.env.user.has_group('std_timesheet_access_rights.timesheet_admin')
        manager = self.env.user.has_group('hr_timesheet.group_hr_timesheet_user')
        if manager:
            pass
        elif admin and not manager and self.user_id.id != self.env.user.id:
            raise Warning(_("You don't have access to update record!\nPlease contact your system Administrator."))
        return res

    # def action_submit(self):
    #     self.write({'state2': 'confirm'})

    @api.multi
    def unlink(self):
        admin = self.env.user.has_group('std_timesheet_access_rights.timesheet_admin')
        manager = self.env.user.has_group('hr_timesheet.group_hr_timesheet_user')
        if manager:
            pass
        if admin and not manager and self.user_id.id != self.env.user.id:
            raise Warning(_("You can't delete this record!\nPlease contact your system Administrator."))
        return super(HrTimesheetSheetSheet, self).unlink()

    @api.multi
    def action_timesheet_done(self):
        if not self.env.user.has_group('hr_timesheet.group_hr_timesheet_user') and \
                not self.env.user.has_group('std_timesheet_access_rights.timesheet_leader'):
            raise Warning(_('Only an HR Officer or Manager can approve timesheets.'))
        if self.filtered(lambda sheet: sheet.state != 'confirm'):
            raise Warning(_("Cannot approve a non-submitted timesheet."))
        self.write({'state': 'done'})

    @api.multi
    def action_timesheet_draft(self):
        if not self.env.user.has_group('hr_timesheet.group_hr_timesheet_user') and \
                not self.env.user.has_group('std_timesheet_access_rights.timesheet_leader'):
            raise UserError(_('Only an HR Officer or Manager can refuse timesheets or reset them to draft.'))
        self.write({'state': 'draft'})
        return True


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    def _check_state(self):
        for line in self:
            if line.sheet_id and line.sheet_id.state in ('done'):
                raise UserError(_('You cannot modify an entry in a confirmed timesheet.'))
        return True


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _check(self):
        for att in self:
            if att.sheet_id and att.sheet_id.state in ('done'):
                raise UserError(_('You cannot modify an entry in a confirmed timesheet'))
        return True

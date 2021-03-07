# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Survey(models.Model):

    _inherit = 'survey.survey'

    
    @api.multi
    def action_survey_user_input(self):
        action_rec = self.env.ref('survey.action_survey_user_input_line')
        
        action = action_rec.read()[0]
        ctx = dict(self.env.context)
        ctx.update({'search_default_survey_id': self.ids[0],
                    'search_default_completed': 1})
        action['context'] = ctx
        return action


class SurveyUserInputLine(models.Model):

    _inherit = 'survey.user_input_line'

    partner = fields.Many2one(related='user_input_id.partner_id', string="Partner")
    state = fields.Selection(related='user_input_id.state', string="Status")
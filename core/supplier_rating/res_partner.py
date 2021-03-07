from odoo import api, models, fields, exceptions, tools, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):

    _inherit = 'res.partner'

    ratings_weightage_ids = fields.One2many('ratings.weightage.line', 'partner_id',string='Ratings and Weightage')

    @api.constrains('ratings_weightage_ids')
    def _check_ratings_weightage_ids(self):
       if not self.env.context.get('direct', False):
           for rec in self:
              if rec.supplier and not rec.customer and rec.ratings_weightage_ids:
                  total = 0
                  for line in rec.ratings_weightage_ids:
                     total += line.weightage
                     # import pdb; pdb.set_trace()
                     
                  if total != 100:
                    raise ValidationError(_('Total weightage should be equal to 100'))

class RatingsWeightageLine(models.Model):

    _name = 'ratings.weightage.line'

    partner_id = fields.Many2one('res.partner', 'Vendor')
    rating_id = fields.Many2one('rating.configuration', 'Rating')
    weightage = fields.Integer('Weightage')

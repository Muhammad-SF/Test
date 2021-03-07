from odoo import api, models, fields, exceptions, tools, _
import datetime


class SupplierRating(models.Model):
    _name = 'supplier.rating'

    @api.depends('rating_lines','rating_lines.rating_id')
    def _compute_average_rating(self):
        for rec in self:
            if rec.rating_lines:
                len_rating = 0
                value_ratings = 0.0
                rec_id = 0
                for rating in rec.rating_lines:
                    value_ratings += rating.value.value
                    len_rating += 1
                    rec_id = rating.rating_id.id
                rec.average_rating = value_ratings / len_rating
                average_rating_next = rec.average_rating / len_rating
                if rec_id:

                    self._cr.execute('UPDATE supplier_rating SET average_rating_next=%s WHERE id = %s',
                                     (average_rating_next, rec_id,))

            else:
                rec.average_rating = 0
                rec.average_rating_next = 0

    @api.depends('rating_lines', 'rating_lines.value')
    def _compute_total_score(self):
        for rec in self:
            total = 0.0
            for rating in rec.rating_lines:
                total += rating.score
            rec.total_score = total

    name = fields.Char(string="Supplier Rating", index=True, default='New', copy=False)
    date_rating = fields.Datetime('Rating Date', default=fields.Date.today)
    partner_id = fields.Many2one('res.partner', 'Vendor')
    # rating_lines = fields.One2many('ratings.lines', 'rating_id', 'Ratings', default=_get_rating_lines)
    rating_lines = fields.One2many('ratings.lines', 'rating_id', 'Ratings', copy=True)
    state = fields.Selection([
        ('draft', 'Draft'), ('validate', 'Validate')], default='draft')
    average_rating = fields.Float('Average Rating', compute='_compute_average_rating')
    average_rating_next = fields.Float('Average Rating')
    total_score = fields.Float('Total Score', compute='_compute_total_score')

    @api.onchange('partner_id')
    def onchange_partner(self):
        for rec in self:
            list_lines = []
            for line in rec.partner_id.ratings_weightage_ids:
                list_lines.append((0, 0, {'name': line.rating_id.name,
                                          'description': line.rating_id.description,
                                          'config_id': line.rating_id.id,
                                          'compulsory': line.rating_id.compulsory,
                                          'weightage': line.weightage,
                                          }))
            rec.rating_lines = list_lines


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_supp_rate = self.env['ir.sequence'].next_by_code('supplier.rating') or _('New')
            vals['name'] = seq_supp_rate[:2] + str(datetime.datetime.now().year)[-2:] + seq_supp_rate[-3:]
        result = super(SupplierRating, self).create(vals)
        self._cr.commit()
        list_line = []
        for line in result.rating_lines:
            list_line.append(line.config_id.id)
        list_config = self.env['rating.configuration'].search([]).ids
        diff_list = list(set(list_line) - set(list_config))
        if not diff_list:
            diff_list = list(set(list_config) - set(list_line))
        if diff_list:
            rec_config = self.env['rating.configuration'].search([('id','in', diff_list),
                                                                  ('compulsory','=',True)])
            if rec_config:
                for rec in rec_config:
                    result.write({'rating_lines': [(0,0,{'name': rec.name,
                                    'description': rec.description,
                                    'config_id': rec.id,
                                    'compulsory': rec.compulsory})]})
                    self._cr.commit()
                raise exceptions.Warning(_(rec.name + ' is Compulsory!'))
        return result

    @api.multi
    def validate_rating(self):
        for rec in self:
            for line in rec.rating_lines:
                if not line.value:
                    raise exceptions.Warning(_('Please enter Ratings Value for %s')%line.name)
                else:
                    rec.state = 'validate'



class RatingLines(models.Model):
    _name = 'ratings.lines'
    _rec_name = 'value'

    @api.onchange('value')
    def onchange_value(self):
        if self.value:
            self.value_value = self.value.value

    rating_id = fields.Many2one('supplier.rating', 'Rating')
    config_id = fields.Many2one('rating.configuration', 'Rating Name')
    name = fields.Char('Name')
    value = fields.Many2one('rating.value', 'Rating')
    value_value = fields.Float('Rating Value')
    rating_value = fields.Float('Rating Value', related='value.value')
    description = fields.Text('Description')
    compulsory = fields.Boolean('Compulsory')
    weightage = fields.Integer('Weightage')
    score = fields.Float('Score',compute='_get_score')
    score_one = fields.Float('Score One')

    @api.depends('value','config_id','score','score_one')
    def _get_score(self):
        for rec in self:
            if rec.config_id.id:
                self._cr.execute("""
                            select max(value) from rating_value where rating_config_id = %s""", (rec.config_id.id,))
                res = self._cr.fetchone()
                if res[0] and rec.value.value and rec.weightage:
                    rec.score = (rec.value.value/res[0]) * rec.weightage

                    if rec.id:
                        self._cr.execute("""update ratings_lines set score_one = %s where rating_id = %s and id = %s""",
                                     (rec.score,rec.rating_id.id, rec.id))

    @api.multi
    def unlink(self):
        if self.config_id.compulsory:
            raise exceptions.Warning(_(self.config_id.name + ' is Compulsory!'))
        return super(RatingLines, self).unlink()

    @api.multi
    def write(self, values):
        if values.get('value', False):
            values.update({'value_value':self.env['rating.value'].browse(values.get('value')).value})
        res = super(RatingLines, self).write(values)
        for rating_rec in self:
            rating = 0
            for rec in rating_rec.rating_id.rating_lines:
                if rec.value:
                    rating += rec.value.value
            rating_rec.rating_id.average_rating = rating/len(rating_rec.rating_id.rating_lines)
        return res

from odoo import api, models, fields


class RatingValues(models.Model):
    _name = 'rating.value'
    _rec_name = 'value'
    _order = 'value asc'

    rating_config_id = fields.Many2one('rating.configuration', 'Rating Config')
    name = fields.Char('Rating Name', required=1)
    value = fields.Float('Value')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if self._context.get('rating_lines', False):
            domain = [('rating_config_id', '=', self._context.get('rating_lines'))]
        if domain:
            recs = self.search(domain + args, limit=limit)
        else:
            recs = self.search(args, limit=limit)
        return recs.name_get()

    @api.multi
    def name_get(self):
        result = []
        for each in self:
            name = str(each.value) + ' ' + each.name
            result.append((each.id, name))
        return result

class RatingConfiguration(models.Model):
    _name = 'rating.configuration'

    name = fields.Char('Rating Name', required=1)
    compulsory = fields.Boolean('Compulsory')
    vendor_ids = fields.Many2many('res.partner','rating_conf_partner_rel','rating_config_id','partner_id',string='Vendors')
    rating_values = fields.One2many('rating.value', 'rating_config_id', string='Ratings')
    description = fields.Text('Description')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "This name already exists !"),
    ]

    @api.model
    def create(self, vals):
        res = super(RatingConfiguration, self).create(vals)
        line_obj = self.env['ratings.weightage.line']
        conf_rec = self.env['rating.configuration'].search([('name', '=', res.name)], limit=1)
        linerec = line_obj.search([('partner_id', 'not in', res.vendor_ids.ids),('rating_id', '=', conf_rec.id)])
        for line in linerec:
            self._cr.execute("""delete from ratings_weightage_line where id = %s""", (line.id,))
        for vendor in res.vendor_ids:
            line_rec = line_obj.search([('partner_id','=', vendor.id), ('rating_id', '=', conf_rec.id)])
            if not line_rec:
                vendor.write({'ratings_weightage_ids': [(0, 0, {'rating_id': conf_rec.id,
                                                                    'partner_id':vendor.id})]})
        return res

    @api.multi
    def write(self, vals):
        res = super(RatingConfiguration, self).write(vals)
        for rec in self:
            line_obj = self.env['ratings.weightage.line']
            conf_rec = self.env['rating.configuration'].search([('name', '=', rec.name)], limit=1)
            linerec = line_obj.search([('partner_id', 'not in', rec.vendor_ids.ids),('rating_id', '=', conf_rec.id)])
            for line in linerec:
                self._cr.execute("""delete from ratings_weightage_line where id = %s""", (line.id,))
            for vendor in rec.vendor_ids:
                line_rec = line_obj.search([('partner_id','=', vendor.id), ('rating_id', '=', conf_rec.id)])
                if not line_rec:
                    vendor.with_context({'direct': True}).write({'ratings_weightage_ids': [(0, 0, {'rating_id': conf_rec.id,
                                                                    'partner_id':vendor.id})]})
        return res







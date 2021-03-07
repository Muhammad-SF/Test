# -*- coding: utf-8 -*-


from openerp import api, exceptions, fields, models, _


class ScrapMatrix(models.Model):
    _name = 'scrap.matrix'
    _description = 'Scrap Matrix'

    name = fields.Char(string='Name', size=64, help='Name.', required=True, )
    scrap_line_ids = fields.One2many(
        comodel_name='scrap.matrix.line',
        inverse_name='scrap_matrix_id', string='Scrap Line',
        help='Add employee for the matrix.')

    @api.model
    def create(self, vals):
        self_ids = self.search([])
        if len(self_ids.ids) >= 1:
            raise exceptions.UserError(_("You can not create multiple record for employee matrix."))
        return super(ScrapMatrix, self).create(vals)


ScrapMatrix()


class ScrapMatrixLine(models.Model):
    _name = 'scrap.matrix.line'
    _description = 'Scrap Matrix Line'
    _order = 'sequence asc'

    scrap_matrix_id = fields.Many2one(
        comodel_name='scrap.matrix',
        string='Scrap Matrix', help='ref of scrap matrix')
    employee_ids = fields.Many2many(
        comodel_name='hr.employee', string='Approver',
        help='Add multiple Approver', required=True, )
    sequence = fields.Integer(
        string='Sequence', help='Ordered Sequence.', default=10 ,required=True, )


ScrapMatrixLine()

from odoo import api, fields, models, _

class MrpBomLines(models.Model):
    _inherit = 'mrp.bom.line'

    is_wip = fields.Boolean(string='Is WIP', readonly=True)

    # @api.onchange('product_id')
    # def routing_finished(self):
    #     finished = self.env['mrp.routing.workcenter'].search([])
    #     for fin in finished:
    #         # print(fin)
    #         # print('FIN', fin.finished_product)

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # finished_product_id = []

    @api.onchange('routing_id')
    def onchange_routing_id(self):
        values = self.onchange_routing_id_values(self.routing_id if self.routing_id else False)
        return values

    def onchange_routing_id_values(self, routing_id):
        bom_ids = []
        res = {}

        if (not routing_id):
            return res

        res = {'value': {
            'bom_line_ids': [],
            }
        }

        operations = routing_id.operation_ids

        for routing in operations:
            if routing.finished_product:
                product = routing.finished_product
                if product:
                    bom_lines = {
                        'product_id': product.id,
                        'product_qty': 1,
                        'product_uom_id': product.uom_id and product.uom_id.id or False,
                        'is_wip': True,
                    }
                    bom_ids += [bom_lines]

        res['value'].update({
            'bom_line_ids': bom_ids,
        })
        return res

    # @api.model
    # def create(self, vals):

        # for line in self.bom_line_ids:
        #     line.operation_id = False



        # if fin.finished_product == True:


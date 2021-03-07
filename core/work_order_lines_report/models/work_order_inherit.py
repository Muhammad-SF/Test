from odoo import models,fields,api,_
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
import math
from odoo import tools


class WorkOrderCosumption(models.Model):
    _name = 'workorder.consumption.line'
    _auto = False


    # @api.depends('workorder_id.material_consumed_id', 'workorder_id.material_consumed_line_id', 'product_id', 'product_qty', 'workorder_id.consumption_lines')
    # def calc_qty_loss_qty(self):
    #     for rec in self:
    #         lost_quantity = 0.0
    #         consumed_quantity = 0.0
    #         for res in rec.workorder_id.material_consumed_line_id:
    #             if rec.product_id == res.product_id:
    #                 lost_quantity += res.lost_quantity
    #                 consumed_quantity += res.quantity
    #         rec.update({'lost_quantity': lost_quantity, 'consumed_quantity': consumed_quantity})

    workorder_id = fields.Char(string="Workorder")
    product_qty = fields.Float(string='Quantity To Consumed', default=1.0, digits=dp.get_precision('Product Unit of Measure'))
    consumed_quantity = fields.Float(string="Quantity Consumed", compute=False, store=True)
    lost_quantity = fields.Float(string="Quantity Loss", compute=False, store=True)
    material_date_planned = fields.Datetime(string="Date")
    product_id = fields.Many2one('product.product', string="Product")
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', readonly=True)
    categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    lost_good_qty = fields.Float('Lost Goods Quantity')
    finish_good_qty = fields.Float('Finished Goods Quantity')
    material_consumed_date = fields.Datetime('Material Consumed Date')


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(WorkOrderCosumption, self).read_group(domain=domain, fields=fields, groupby=groupby, offset=offset,limit=limit, orderby=orderby, lazy=lazy)
        if len(groupby) == 1:
            if groupby[0] not in ['workorder_id','material_date_planned']:
                for record in res:
                    record.update({'finish_good_qty':0,'lost_good_qty':0})
        elif len(groupby) > 1:
            for record in res:
                if any('workorder_id' in x for x in (record.get('__domain'))):
                    record.update({'finish_good_qty': 0, 'lost_good_qty': 0})
        return res


    # @api.model
    # def create(self, vals):
    #     res = super(WorkOrderCosumption, self).create(vals)
    #     res.calc_qty_loss_qty()
    #     return res

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
select table_1.id,
     table_1.product_id, 
     product_uom, 
     (table_1.quantity) as product_qty, 
     (table_1.consumed_quantity) as consumed_quantity, 
     (table_1.lost_quantity) as lost_quantity,
     (table_1.finished_goods) as finish_good_qty, 
     (table_1.lost_goods) as lost_good_qty,
     table_1.name as workorder_id, 
	 table_1.date as material_date_planned, categ_id, consumed.date as material_consumed_date
    from (
    	(SELECT min(consumed_line.id) as id,
    	    consumed_line.product_id as product_id,
    		t.uom_id as product_uom,
    		0 as quantity,
    		sum(consumed_line.quantity) as consumed_quantity,
    		sum(consumed_line.lost_quantity) as lost_quantity,
    		consumed.finished_goods as finished_goods,
    		consumed.lost_goods as lost_goods,
    		consumed.date as material_consumed_date,
    		count(*) as nbr,
    		workorder.workorder_id as name,
    		workorder.date_planned_start as date,
    		t.categ_id as categ_id,
    		p.product_tmpl_id
    		FROM ( 
    			mrp_material_consumed_line consumed_line
    			join mrp_workorder workorder on (consumed_line.workorder_id=workorder.id)
    			left join mrp_material_consumed consumed on (consumed_line.material_consumed_id = consumed.id)
    			left join mrp_production production on (workorder.production_id=production.id)
    			left join product_product p on (consumed_line.product_id=p.id)
    			left join product_template t on (p.product_tmpl_id=t.id)
    		)    
    		WHERE consumed_line.state = 'approved'
    		GROUP BY consumed_line.product_id,
    				t.uom_id,
    				t.categ_id,
    				workorder.name,
		 			consumed.date,
		 			workorder.workorder_id,
		 			consumed.finished_goods,
    				consumed.lost_goods,
    				workorder.date_planned_start,
    				p.product_tmpl_id
    )UNION (
    	SELECT min(mrp_bomlines.id) as id,
    	        (mrp_bomlines.name) as product_id,
    			product_temp.uom_id as product_uom,
    			sum(mrp_bomlines.product_qty * production.product_qty) as quantity,
    			0 as consumed_quantity,
    			0 as lost_quantity,
    			0 as finished_goods,
    		    0 as lost_goods,
    		    null as material_consumed_date,
    			count(*) as nbr,
    			workorder.workorder_id as name,
    			workorder.date_planned_start as date,
    			product_temp.categ_id as categ_id,
    			product.product_tmpl_id
    FROM ( 
    	mrp_workorder_bomlines mrp_bomlines
    	join mrp_workorder workorder on (mrp_bomlines.work_order_id=workorder.id)
    	left join mrp_production production on (workorder.production_id=production.id)
    	left join product_product product on (mrp_bomlines.name=product.id)
    	left join product_template product_temp on (product.product_tmpl_id=product_temp.id)
    	left join product_uom u on (u.id=product_temp.uom_id)
    	left join product_uom u2 on (u2.id=product_temp.uom_id)
    )             
    GROUP BY mrp_bomlines.name,
    		product_temp.uom_id,
    		product_temp.categ_id,
    		workorder.name,
			workorder.workorder_id,
    		workorder.date_planned_start,
    		product.product_tmpl_id
    )) as table_1 
		join mrp_workorder workorder on (table_1.name=workorder.workorder_id)
		left join mrp_material_consumed consumed on (consumed.workorder_id = workorder.id)
		left join mrp_material_consumed_line consumed_line on (consumed_line.product_id = table_1.product_id and consumed_line.material_consumed_id = consumed.id)
		group by table_1.id, table_1.product_id,table_1.quantity, 
		table_1.consumed_quantity, table_1.lost_quantity, table_1.finished_goods, 
		table_1.lost_goods, product_uom, table_1.name, table_1.date, consumed.date, categ_id 
		order by table_1.name
                """
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
                    %s
                    )""" % (self._table, sql))

# class WorkOrderBomLinesInherit(models.Model):
#     _inherit = 'mrp.workorder.bomlines'
#
#     @api.model
#     def create(self, vals):
#         res = super(WorkOrderBomLinesInherit, self).create(vals)
#         create_data = {'product_id': res.name.id,
#                        'product_qty': res.product_qty,
#                        'workorder_id': res.work_order_id.id}
#         wcl = self.env['workorder.consumption.line'].create(create_data)
#         wcl.calc_qty_loss_qty()
#         return res
#
#     @api.multi
#     def write(self, vals):
#         res = super(WorkOrderBomLinesInherit, self).write(vals)
#         for line in self.work_order_id.consumption_lines:
#             line.calc_qty_loss_qty()
#         return res
#
#     product_qty = fields.Float(string='Quantity To Consumed', default=1.0, digits=dp.get_precision('Product Unit of Measure'))
#     consumed_quantity = fields.Float(string="Quantity Consumed")
#     lost_quantity = fields.Float(string="Quantity Loss")
#     material_date_planned = fields.Datetime(string="Date")
#
#
# class WorkOrderInherit(models.Model):
#     _inherit = 'mrp.workorder'
#
#     consumption_lines = fields.One2many('workorder.consumption.line', 'workorder_id', string="Consumption Lines")
#
#     @api.multi
#     def write(self, vals):
#         res = super(WorkOrderInherit, self).write(vals)
#         for line in self.consumption_lines:
#             line.material_date_planned = self.date_planned_start
#             line.calc_qty_loss_qty()
#         return res
#
#
# class MaterialConsumedInherit(models.Model):
#     _inherit = 'mrp.material.consumed'
#
#     @api.multi
#     def button_approved(self):
#         for line in self.approving_matrix_line_ids.filtered(lambda r: not r.approved):
#             if line.employee_ids and len(line.employee_ids) > 0:
#                 user_ids = line.employee_ids.mapped('user_id').ids
#                 if self._uid in user_ids:
#                     for consumed_line in self.line_ids:
#                         for lines in consumed_line.workorder_id:
#                             for bom_line in lines.consumption_lines:
#                                 if consumed_line.product_id.id == bom_line.product_id.id:
#                                     bom_line.write({'consumed_quantity': consumed_line.quantity,
#                                                     'lost_quantity': consumed_line.lost_quantity})
#                                 else:
#                                     create_data = {'product_id': consumed_line.product_id.id,
#                                                    'product_qty': 0.0,
#                                                    'material_date_planned': consumed_line.material_consumed_id.workorder_id.date_planned_start,
#                                                    'consumed_quantity': consumed_line.quantity,
#                                                    'lost_quantity': consumed_line.lost_quantity,
#                                                    'workorder_id': consumed_line.material_consumed_id.workorder_id.id}
#                                     wcl = self.env['workorder.consumption.line'].create(create_data)
#                                     wcl.calc_qty_loss_qty()
#                     line.write({'approved': True})
#                     self.button_to_approve()
#                     break
#                 else:
#                     # self.button_to_approve()
#                     raise UserError(_("You don't have access to approve this!"))
#             else:
#                 raise UserError(_("Only Administrator can approve this!"))
#         else:
#             self.state = 'approved'
#             return True
#
#
# class mrp_material_consumed_line(models.Model):
#     _inherit = 'mrp.material.consumed.line'
#
#     @api.onchange('state', 'material_consumed_id', 'product_id', 'quantity', 'lost_quantity')
#     def onchange_line(self):
#         for line in self.workorder_id.consumption_lines:
#             line.calc_qty_loss_qty()
#
#     @api.multi
#     def write(self, vals):
#         res = super(mrp_material_consumed_line, self).write(vals)
#         for line in self.workorder_id.consumption_lines:
#             line.calc_qty_loss_qty()
#         return res
#
#     @api.model
#     def create(self, vals):
#         result = super(mrp_material_consumed_line, self).create(vals)
#         for line in result.workorder_id.consumption_lines:
#             line.calc_qty_loss_qty()
#         return result

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _,SUPERUSER_ID
from odoo.exceptions import UserError,ValidationError
from odoo.addons.base.res.res_users import get_selection_groups
from lxml import etree


class ResUsers(models.Model):
   _inherit = 'res.users'

   
   @api.multi
   def write(self, vals):
      group_obj = self.env['res.groups']
      groups_by_application = group_obj.get_groups_by_application()
      def find_implied(group):
         # Recusively find all implied groups
         res = []
         for implied in group.implied_ids:
            res.append(implied)
            for item in implied:
               res += find_implied(item)
         return res

      def update_implied(implied):
         res = {}
         for item in implied:
            for category, ttype, groups in groups_by_application:  # pylint: disable=W0612
               if ttype == 'boolean' and \
                  item.id in [g.id for g in groups]:
                  res.update({'in_group_%s' % item.id: False})
         return res

      to_upd = {}
      for key, value in vals.items():  # pylint: disable=W0612
         if key.startswith('in_group_'):
            groups = self.get_selection_groups_1(key)
            for group in group_obj.browse(groups):
               implied = find_implied(group)
               to_upd.update(update_implied(implied))
      vals.update(to_upd)
      return super(ResUsers, self).write(vals)
   
   def get_selection_groups_1(self,key):
      local = map(int, key[9:].split('_'))
      return local

class SaleOrder(models.Model):
   _inherit = 'sale.order'

   is_direct_state= fields.Selection([
      ('default', 'default'),
      ('sale', 'sale'),
      ('direct', 'direct')], string="Tracking", default='default')
   is_direct_sale = fields.Boolean(string='Is Direct Sale', default=False)
   is_sale_order = fields.Boolean(string='Is Sale Order', default=False)
   project_id = fields.Many2one('account.analytic.account', copy=True)

   @api.multi
   def write(self, vals):
      res = super(SaleOrder, self).write(vals)
      for record in self:
         if record.user_has_groups('standard_sales_access_right.group_sales_team_mngr') == False \
               and record.user_has_groups('sales_team.group_sale_manager') == False:
            if record.user_has_groups('standard_sales_access_right.group_sales_team_docs') \
                  or record.user_has_groups('sales_team.group_sale_salesman_all_leads') \
                  or record.user_has_groups('sales_team.group_sale_salesman'):
               if record.user_id.id != record.env.user.id:
                  if  record.user_has_groups('standard_sales_access_right.group_sales_team_docs') or record.user_has_groups('sales_team.group_sale_salesman'):
                     raise ValidationError(_(
                        "The requested operation cannot be completed due to security restrictions. Please contact your system administrator. "))
                  if record.user_has_groups('sales_team.group_sale_salesman_all_leads') or record.user_has_groups('sales_team.group_sale_salesman'):
                     raise ValidationError(_(
                        "The requested operation cannot be completed due to security restrictions. Please contact your system administrator. "
                     ))
      return res

   # @api.multi
   # @api.depends('team_id', 'team_id.member_ids')
   # def compute_is_direct_sale(self):
   #    print"compute_is_direct_sale "
   #    for record in self:
   #       if record.user_id.id != self.env.user.id and record.team_id.member_ids:
   #          for team in record.team_id.member_ids:
   #             if team.id == self.env.user.id:
   #                record.is_direct_state = 'direct'
   #                record.is_direct_sale = True
   #
   # @api.multi
   # def compute_is_order_sale(self):
   #    for record in self:
   #       if self.user_has_groups('standard_sales_access_right.group_sales_team_docs'):
   #          if record.user_id.id == self.env.user.id:
   #             record.is_direct_state = 'sale'
   #             record.is_sale_order = True

   @api.model
   def search(self, args, offset=0, limit=None, order=None, context=None, count=False):
      if not args:
         args = []
      sale_team_id = self.env.user.sale_team_id
      user = self.env.user
      if user and user.id != SUPERUSER_ID:
         if self.user_has_groups('standard_sales_access_right.group_sales_team_mngr'):
            args += [('user_id', 'in', sale_team_id.member_ids.ids), ('team_id', '=', sale_team_id.id)]

         elif self.user_has_groups('standard_sales_access_right.group_sales_team_docs'):
           args += [('user_id','in',sale_team_id.member_ids.ids),('team_id','=',sale_team_id.id)]
      res = super(SaleOrder,self).search(args, offset, limit, order, count=count)
      return res

   @api.model
   def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
      res =  super(SaleOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,submenu=submenu)
      if (view_type == 'form' or view_type == 'tree' or view_type == 'kanban') and self.env.user.id == SUPERUSER_ID :
         doc = etree.XML(res['arch'])
         for node in doc.xpath("//form"):
            node.set('create', 'true')
            node.set('edit', 'true')
            node.set('delete', 'true')
         for node in doc.xpath("//tree"):
            node.set('create', 'true')
            node.set('edit', 'true')
            node.set('delete', 'true')
         for node in doc.xpath("//kanban"):
            node.set('create', 'true')
            node.set('edit', 'true')
            node.set('delete', 'true')

         res['arch'] = etree.tostring(doc)
      return res



class CrmLead(models.Model):
   _inherit = 'crm.lead'

   @api.multi
   def write(self, vals):
      res = super(CrmLead, self).write(vals)
      for record in self:
         # if Sales: All Docs  or Sales: Team Docs is enable need to hide to show warning
         if record.user_has_groups('standard_sales_access_right.group_sales_team_mngr') == False \
               and record.user_has_groups('sales_team.group_sale_manager') == False:
            if record.user_has_groups('standard_sales_access_right.group_sales_team_docs') \
                  or record.user_has_groups('sales_team.group_sale_salesman_all_leads') \
                  or record.user_has_groups('sales_team.group_sale_salesman'):
               if record.user_id.id != record.env.user.id:
                  if  record.user_has_groups('standard_sales_access_right.group_sales_team_docs') or record.user_has_groups('sales_team.group_sale_salesman'):
                     raise ValidationError(_(
                        "The requested operation cannot be completed due to security restrictions. Please contact your system administrator. "))
                  if record.user_has_groups('sales_team.group_sale_salesman_all_leads') or record.user_has_groups('sales_team.group_sale_salesman'):
                     raise ValidationError(_(
                        "The requested operation cannot be completed due to security restrictions. Please contact your system administrator. "
                     ))
      return res

   @api.model
   def search(self, args, offset=0, limit=None, order=None, context=None, count=False):
      if not args:
         args = []
      sale_team_id = self.env.user.sale_team_id
      user = self.env.user
      if self.user_has_groups('standard_sales_access_right.group_sales_team_mngr'):
         args += [('user_id','in',sale_team_id.member_ids.ids),('team_id','=',sale_team_id.id)]
      elif self.user_has_groups('standard_sales_access_right.group_sales_team_docs'):
         args += [('user_id','in',sale_team_id.member_ids.ids),('team_id','=',sale_team_id.id)]
      return super(CrmLead,self).search(args, offset, limit, order, count=count)





class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResPartner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,submenu=submenu)
        if (view_type == 'form' or view_type == 'tree' or view_type == 'kanban') and self.env.user.has_group('sales_team.group_sale_salesman') and self.env.user.id != SUPERUSER_ID and not self.env.user.has_group('standard_sales_access_right.group_allow_customer') :
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//form"):
                node.set('create', 'false')
                node.set('edit', 'false')
            for node in doc.xpath("//tree"):
                node.set('create', 'false')
                node.set('edit', 'false')
            for node in doc.xpath("//kanban"):
                node.set('create', 'false')
                node.set('edit', 'false')

            res['arch'] = etree.tostring(doc)
        return res



    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, context=None, count=False):
       # sale_team_id = self.env.user.sale_team_id
       # user = self.env.user
       # if self.env.user.has_group('sales_team.group_sale_salesman') and not self.env.user.has_group('sales_team.group_sale_salesman_all_leads') :
       #    args += ['|',('user_id', '=', user.id),('create_uid','=',user.id)]
         
       # return super(ResPartner,self).search(args, offset, limit, order, count=count)



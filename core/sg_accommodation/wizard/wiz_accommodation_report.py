# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt.Ltd. (<http://www.serpentcs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _


class acc_report(models.TransientModel):
    _name = 'acc.report'

    group_type = fields.Selection([('by_location', 'By Location'), ('by_country', 'By Country')], string="Group By Filter")
    dummy = fields.Char('Dummy')


    @api.multi
    def print_report(self):
        cr, uid, context = self.env.args
        companies = {}
        bed_obj = self.env['beds.beds']
        loc_ids = self.env['res.partner'].search([('location', '=', True)])
        cr.execute('select distinct(v.nationality_id),c.name from visa_quota v, res_country c where v.nationality_id=c.id')
        res = cr.fetchall()
        country_ids = [tpl[0] for tpl in res]
        countries = dict([(tpl[0], tpl[1]) for tpl in res])
        company_ids = self.env['res.company'].search([('tenant', '=', True)])
        if company_ids.ids:
            companies = dict([(comp.id, comp.rml_header1) for comp in company_ids])
        for acc_report in self:
            if acc_report.group_type == 'by_location':
                loc_dict = {}
                locs = []
                comp = []
                lst = []
                new_lst = []
                for loc in loc_ids:
                    acc_ids = self.env['accommodation.accommodation'].search([('address_id', '=', loc.id)])
                    new_dict = {'sr_no' : loc.name + ', ' + str(loc.contact_address).replace("\n", ", "),
                            'acc_name' : '',
                            'country':[],
                            'landlord':'',
                            'tenant':'',
                            'max':'',
                            'occupied':'',
                            'available':'',
                            'location' : 1}
                    if acc_ids:
                        new_lst.append(new_dict)
                    count = 0
                    count_bed_filled = 0
                    for accom in acc_ids:
                        count += 1
                        visa_dict = {}
    #                    accom_lst = []
                        for visa in accom.visa_quota_ids:
                            acco_address = accom.address_id.name
                            company_dict = {}
                            country_comp_total = 0
                            for company_id in company_ids.ids:
                                args = [
                                    ('room_id.accommodation_id', '=', accom.id),
                                    ('employee_id', '!=', False),
                                    ('employee_id.company_id', '=', company_id),
                                    ('employee_id.emp_country_id', '=', visa.nationality_id.id)
                                ]
                                bed_ids_filled = bed_obj.search(args, count=True)
                                if bed_ids_filled:
                                    count_bed_filled = bed_ids_filled
#                                country_comp_total += bed_ids_filled
                                country_comp_total += count_bed_filled
                                company_dict[companies.get(company_id)] = bed_ids_filled
                            company_dict['total'] = country_comp_total
                            visa_dict[visa.nationality_id.name] = company_dict
                        country_lst = []
                        for key, val in visa_dict.iteritems():
                            country_dict = {}
                            country_dict['country'] = key
                            country_dict.update(val)
                            country_lst.append(country_dict)
                        new_dict = {
                            'sr_no' : count,
                            'acc_name' : accom.name,
                            'country':country_lst,
                            'landlord':accom.land_lord_id.name,
                            'tenant':accom.paying_comp_id.rml_header1,
                            'max':accom.maximum_capacity,
                            'occupied':accom.stay_capacity,
                            'available':accom.occupied,
                            'location' : 0
                            }
                        new_lst.append(new_dict)
                ret_dict = {'loc_dict1' : new_lst}
                res = {'ids': self.ids, 'model':'acc.report', 'form': ret_dict}
                return self.env['report'].get_action(self, 'sg_accommodation.view_location_report',data=res)
            elif acc_report.group_type == 'by_country':
                country_dict = {}
                for country in self.env['res.country'].browse(country_ids):
                    loc_dict = {}
                    country_id = country.id
                    visa_ids = self.env['visa.quota'].search([('nationality_id', '=', country_id)])
                    for visa in visa_ids:
                        loc_name = visa.accommodation_id.address_id.name
                        acc_dict = {}
                        company_dict = {}
                        visa_total = visa.number_of_quota
                        visa_avail = visa.quota_available
                        visa_occupied = visa_total - visa_avail
                        country_comp_total = 0
                        count_occupied = 0
                        for company in company_ids:
                            company_id = company.id
                            args = [
                                ('employee_id.company_id', '=', company_id),
                                ('employee_id', '!=', False),
                                ('employee_id.emp_country_id', '=', visa.nationality_id.id),
                                ('room_id.accommodation_id', '=', visa.accommodation_id.id)
                            ]
                            occupied_beds = bed_obj.search(args, count=True)
                            if occupied_beds:
                                count_occupied = occupied_beds
                            country_comp_total += count_occupied
                            company_dict[company.rml_header1] = occupied_beds
                            company_dict.update({'acc_name' : visa.accommodation_id.name})
                        company_dict['total'] = country_comp_total
                        if loc_name in loc_dict.keys():
                            loc_dict[loc_name]['acc_list'].append(company_dict)
                            loc_dict[loc_name]['max'] += visa_total
                            loc_dict[loc_name]['occupied'] += visa_occupied
                            loc_dict[loc_name]['available'] += visa_avail
                        else:
                            loc_dict[loc_name] = {'acc_list':[company_dict], 'max':visa_total, 'occupied':visa_occupied, 'available':visa_avail}
                    country_dict[country.name] = loc_dict
                final_dict = {}
                final_list = []
                for con_key, con_val in country_dict.iteritems():
                    final_dict = {
                        'sr_no':con_key,
                        'max':'',
                        'loc' : '',
                        'occupied':'',
                        'available':'',
                        'acc_list':[],
                        'country' : 1
                    }
                    final_list.append(final_dict)
                    counter = 0
                    for loc_key, loc_val in con_val.iteritems():
                        counter += 1
                        final_dict = {
                        'sr_no':counter,
                        'max':loc_val.get('max', 0),
                        'loc' : loc_key,
                        'occupied':loc_val.get('occupied', 0),
                        'available':loc_val.get('available', 0),
                        'acc_list':loc_val.get('acc_list', []),
                        'country' : 0
                        }
                        final_list.append(final_dict)
                ret_dict = {'loc_dict' : loc_dict, 'loc_dict1' : final_list}
                res = {'ids': self.ids, 'model':'acc.report', 'form': ret_dict}
#                return self.pool['report'].get_action(cr, uid, [], 'sg_accommodation.view_nationality_report', data=res, context=context)
                return self.env['report'].get_action(self, 'sg_accommodation.view_nationality_report', data=res)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
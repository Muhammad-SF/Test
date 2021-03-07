# -*- coding: utf-8 -*-

def uninstall_hook(cr, registry):
    cr.execute("UPDATE ir_act_window "
               "SET domain=''"
               "WHERE name ILIKE 'Chart of Analytic Accounts' and res_model='account.analytic.account' and search_view_id is not null""")


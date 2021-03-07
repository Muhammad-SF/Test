# -*- coding: utf-8 -*-
{
    'name': "user_access_grouping",

    'summary': """
        user_access_grouping""",

    'description': """
       Objective: Allowing easier set up of access rights

Current flow:
- On the form view of user, we can assign them the different groups of access rights

To change to:
- Create a new function called "Access Type" after the Groups function in the sidebar
- Access Type is a combination of different groups, where user can create a new Acess Type consisting of multiple groups
- On the form view, instead of assigning groups, we are assigning Access Type

Keypoints:
- Access Type replaces the way we assign access rights to users, by creating a middle layer for easier management
- Access Type also consists of the access right assigned from the tickbox

Custom Module dependency (if depends on other customized modules):
---

Case study:
- I create a new Access Type, called "General Manager", it consists of groups:
Accounting: Financial Manager
Warehouse: Manager
Sales: Manager
Ticked Manage Push & Pull Inventory Flow, Technical Features
- When I assign the Access Type "General Manager" to user A, user A will automatically have all those rights from General Manager

    """,

    'author': "HashMicro / Vu",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'account',
    ],

    # always loaded
    'data': [
        'data/group_category.xml',
        'views/res_users.xml',
        'views/access_grouping_views.xml',
        'security/user_access_grouping.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
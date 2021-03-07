# -*- coding: utf-8 -*-
# Part of Synconics. See LICENSE file for full copyright and licensing details.
{
    "name": "Drag & Drop Multi Attachments", 
    "version": "1.1.1", 
    'author': 'Synconics Technologies Pvt. Ltd.',
    'website': 'https://www.synconics.com',
    "category": "Social Network",
    "summary": "Drag & Drop multiple attachments in the form view at once",
    "description": """
    This module enables the feature to Drag & Drop multiple attachments in the form view of any objects.
 
    The attachments which are selected can simply drag &amp; drop to the form view and will be available at the "Attachments" dropdown box on the top of the form view.
 
    To attach the files in the Odoo object, You have to open the form view, explore the file(s), select the file(s) and drag & drop them into the “Drop your files here” area of the form view.
    
    Dropped files will be available in the “Attachments” dropdown box on the top of the form view.
    """,
    "depends": ["document"],
    'data': ["views/drag_drop_attach_view.xml"],
    'qweb': ['static/src/xml/*.xml'],
    "price": 35,
    "currency": "EUR", 
    "installable": True, 
    "auto_install": False
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
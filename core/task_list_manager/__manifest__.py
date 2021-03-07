{
    'name': 'Task List Manager',
    'description': 'Schedule activity feature in the form views',
    'category': 'Project',
    'version': '1.1.1',
    'author': 'HashMicro / MP Technolabs(Chankya)',
    'website': 'www.hashmicro.com',
    'depends': ['sale','mail','account_voucher'],
    'data': [
            'data/mail_activity.xml',
            'views/mail_templates.xml',
            'views/mail_activity_views.xml',
            'views/sale_view.xml',
            'views/res_partner_view.xml',
            'security/ir.model.access.csv',
    ],
    'installable': True,
    'qweb': [
        'static/src/xml/chatter.xml',
        'static/src/xml/activity.xml',
        'static/src/xml/systray.xml',
    ],
}
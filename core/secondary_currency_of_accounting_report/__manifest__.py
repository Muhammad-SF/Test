{
    'name':"Secondary Currency in Report",
    'summary': """Secondary currency -  value updates besed on selected the other currency.""",
    'description': 'There is separate option to select the currency whatever active in currency master. Then the all report value has been changed based on currency.',
    'category': 'Accounting',
    'version':'1.2.12',
    'author': "HashMicro / AntsyZ - Mareeswaran",
    'website':"http://www.hashmicro.com",
    'depends': [ 'base','account', 'enterprise_accounting_report'],
    'data': [
        'views/template.xml',
    ],
    'qweb': [
    'static/src/xml/account_report_changed_backend.xml',
    ],
    'installable': True,
    'application': True,
}

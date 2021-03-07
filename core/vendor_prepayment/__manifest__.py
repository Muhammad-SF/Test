{
    'name': "Vendor PrePayment",
    'description': "Generate journal entry for vendor bill payment",
    'author': "Hashmicro",
    'website': "Hashmicro",
    'category': "Accouting",
    'version': "1.1.2",
    'depends': [
        'base',
         'account',
         'acc_recurring_entries'
    ],

    'data': [
        'data/invoice_sequence_data.xml',     
        'views/account_invoice_inherit_view.xml',
    ],
    
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}

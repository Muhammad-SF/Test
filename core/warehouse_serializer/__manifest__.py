{
    'name': 'Warehouse Serializer',
    'description': 'To auto generate SKU, serial and lot number based on sequence',
    'category': 'Serializer',
    'version': '1.1.1',
    'author': 'Inventory Standardization / Janbaz Aga',
    'website': 'www.hashmicro.com',
    'depends': ['stock'],
    'data': [
        'wizard/serial_lot_number.xml',
        'views/product_sku_serializer.xml',
        'views/lot_number_serializer.xml',
        'views/stock_picking.xml',
        'views/barcode_number.xml',
        'data/lable_size_data.xml',
        'views/label_size_view.xml',
        'reports/existing_barcode.xml',
        'reports/forecast_barcode.xml',
        'reports/report.xml',

    ],
    'application': True,
    'installable': True,
}

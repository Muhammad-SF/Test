{
	"name": "Return Account Internal Category",
	"version": "1.1.1", 
	"author": "hashmicro/Jaydeep",
	"category": "Account",
	'website': 'http://www.hashmicro.com',
	"description": """
		add return account in product category
	""",
	"depends": [
		'account','credit_debit_note','stock','product'
	],
	"data": [
		"view/product_category_view.xml"
	],
	"installable": True,
	"auto_install": False,
    "application": True,
}

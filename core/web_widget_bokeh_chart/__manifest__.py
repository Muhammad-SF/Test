# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).#

{
    "name": "Web Widget Bokeh Chart",
    "category": "Hidden",
    "summary": "This widget allows to display charts using Bokeh library.",
    "author": "Eficent, "
              "Odoo Community Association (OCA)",
    "version": "1.1.1",
    "website": "https://github.com/OCA/web",
    "depends": ["web"],
    "data": [
        "views/web_widget_bokeh_chart.xml",
    ],
    "external_dependencies": {
        "python": ['bokeh'],
    },
    "auto_install": False,
    "license": "AGPL-3",
}

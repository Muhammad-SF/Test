from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError

class WorkLocation(models.Model):

    _name = "work.location"
    
    name=fields.Char("Work Location Name",required="True")
    work_location_parent=fields.Many2one('work.location',string="Work Location Parent")
    company_id=fields.Many2one('res.company',string="Company")
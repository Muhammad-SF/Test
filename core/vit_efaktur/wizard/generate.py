from odoo import api, fields, models, _

class efaktur_wizard(models.TransientModel):
    _name = 'vit.generate_efaktur'
    
    start = fields.Char("Start")
    end   = fields.Char("End")
    year  = fields.Integer("Year")

    # @api.onchange('start')
    # def _onchange_start(self):
    #     for record in self:
    #         if record.start:
    #             rec_3=record.start[0:3]
    #             rec_4=record.start[3:5]
    #             rec_6=record.start[5:]
    #             FormatedStr=str(rec_3)+'-'+str(rec_4)+'-'+str(rec_6)
    #             record.start=FormatedStr
    #
    # @api.onchange('end')
    # def _onchange_end(self):
    #     for record in self:
    #         if record.end:
    #             rec_3=record.end[0:3]
    #             rec_4=record.end[3:5]
    #             rec_6=record.end[5:]
    #             FormatedStr=str(rec_3)+'-'+str(rec_4)+'-'+str(rec_6)
    #             record.end = FormatedStr
    @api.multi
    def confirm_button(self):
        start = self.start
        end = self.end
        
        #017-17-34018714
        a = start.split("-")
        b = end.split("-")
        for i in range(int(a[2]), int(b[2])+1):
            nomor = "%s-%s-%08d" % (a[0],a[1],i)
            data = {
                'year': self.year,
                'name': nomor,
            }
            self.env['vit.efaktur'].create(data)
        
        return
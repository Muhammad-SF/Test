from odoo import api, fields, models, _
import time
import csv
from odoo.modules import get_modules, get_module_path
from odoo.exceptions import UserError

class efaktur_pm_wizard(models.TransientModel):
    _name = 'vit.efaktur_pm'

    @api.multi
    def confirm_button(self):
        """
        export pm yang is_efaktur_exported = False
        update setelah export
        :return: 
        """
        cr = self.env.cr

        headers = [
            'FM',
            'KD_JENIS_TRANSAKSI',
            'FG_PENGGANTI',
            'NOMOR_FAKTUR',
            'MASA_PAJAK',
            'TAHUN_PAJAK',
            'TANGGAL_FAKTUR',
            'NPWP',
            'NAMA',
            'ALAMAT_LENGKAP',
            'JUMLAH_DPP',
            'JUMLAH_PPN',
            'JUMLAH_PPNBM',
            'IS_CREDITABLE'
        ]


        mpath = get_module_path('vit_efaktur')

        csvfile = open(mpath + '/static/fpm.csv', 'wb')
        csvwriter = csv.writer(csvfile, delimiter=',')
        csvwriter.writerow([h.upper() for h in headers])

        onv_obj = self.env['account.invoice']
        invoices = onv_obj.search([('is_efaktur_exported','=',False),
                                   ('state','=','open'),
                                   ('efaktur_masukan','!=', ''),
                                   ('type','=','in_invoice')])


        i=0
        for invoice in invoices:
            self.baris2(headers, csvwriter, invoice)
            invoice.is_efaktur_exported=True
            invoice.date_efaktur_exported=time.strftime("%Y-%m-%d %H:%M:%S")
            i+=1

        cr.commit()
        csvfile.close()

        raise UserError("Export %s record(s) Done!" % i)

    def baris2(self, headers, csvwriter, inv):
        if not inv.partner_id.npwp:
            raise UserError("Harap masukkan NPWP Supplier %s" % inv.partner_id.name)

        if not inv.efaktur_masukan:
            raise UserError("Harap masukkan Nomor Seri Faktur Pajak Masukan Invoice Nomor %s" % inv.number)

        # yyyy-mm-dd to dd/mm/yyyy
        d  = inv.date_invoice.split("-")
        date_invoice = "%s/%s/%s" %(d[2],d[1],d[0])
        npwp = inv.partner_id.npwp.replace(".","").replace("-","")
        #faktur = inv.efaktur_masukan.replace(".","").replace("-","")
        Label = ''
        key_val_dict = dict(inv._fields['transaction_code'].selection)  # here 'type' is field name
        for key, val in key_val_dict.items():
            if key == inv.transaction_code:
                Label = val

        data = {
            'FM': 'FM',
            'KD_JENIS_TRANSAKSI': Label and "" + Label or '01',
            'FG_PENGGANTI':'0',
            'NOMOR_FAKTUR': "" + inv.efaktur_masukan,
            'MASA_PAJAK': inv.masa_pajak or '',
            'TAHUN_PAJAK': inv.tahun_pajak or '',
            'TANGGAL_FAKTUR': date_invoice,
            'NPWP': "" + npwp,
            'NAMA': inv.partner_id.name or '',
            'ALAMAT_LENGKAP': inv.partner_id.alamat_lengkap or '',
            'JUMLAH_DPP': int(round(inv.amount_untaxed)) or 0,
            'JUMLAH_PPN': int(round(inv.amount_tax)) or 0,
            'JUMLAH_PPNBM': 0,
            'IS_CREDITABLE':1
        }
        csvwriter.writerow([data[v] for v in headers])


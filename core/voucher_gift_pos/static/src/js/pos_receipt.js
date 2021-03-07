odoo.define('voucher_gift_pos.pos_receipt', function(require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var screens = require('point_of_sale.screens');
var QWeb = core.qweb;

screens.ReceiptScreenWidget.include({
    render_receipt: function() {
        this.a2 = window.location.origin + '/web/image?model=pos.config&field=image&id='+this.pos.config.id
        var self = this;
        self.coupon_code = '';
        var order = this.pos.get_order();
        var order_json = order.export_as_JSON();
        new Model('gift.coupon.pos').call('create_gift_voucher_from_pos',[order_json]).then(function(coupon_code){
            if (coupon_code && coupon_code['coupon']){
            self.coupon_code = coupon_code['coupon'];
            self.$('.pos-receipt-container').html(QWeb.render('PosTicket',{
                    widget:self,
                    order: order,
                    receipt: order.export_for_printing(),
                    orderlines: order.get_orderlines(),
                    paymentlines: order.get_paymentlines(),
                    coupon: coupon_code['coupon'],
                }));
            }
            else{
            self.$('.pos-receipt-container').html(QWeb.render('PosTicket',{
                    widget:self,
                    order: order,
                    receipt: order.export_for_printing(),
                    orderlines: order.get_orderlines(),
                    paymentlines: order.get_paymentlines(),
                }));
            }

        })
        
    },
        show: function () {
        this._super();   
        this.renderElement();
        var order = this.pos.get_order();
        var order_details = order.export_for_printing();
        setTimeout(function(){
		        try {
		            JsBarcode("#barcode", order_details.coupon_availed_code);
		        } catch (error) {
		        }
            },500);
        this.$('.change-value').html(this.format_currency(this.pos.get_order().get_change()));
    },
    
});



});


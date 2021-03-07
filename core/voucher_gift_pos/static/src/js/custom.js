odoo.define('vouchers_gitf_pos.custom_button', function (require) { 
	"use strict";
	var core = require('web.core');
	var screens = require('point_of_sale.screens');
	var gui = require('point_of_sale.gui');
	
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var pos_model = require('point_of_sale.models');
    var pos_popup = require('point_of_sale.popups');
    var models = pos_model.PosModel.prototype.models;
    var PosModelSuper = pos_model.PosModel;
    var OrderSuper = pos_model.Order;
    var Model = require('web.DataModel');
    var _t = core._t;
    var utils = require('web.utils');
    var round_pr = utils.round_precision;

    var PaymentScreenWidget = screens.PaymentScreenWidget;
    pos_model.load_fields('coupon_availed');
    //models.load_fields('res.partner',['loyalty_id']);
    
    // getting vouchers and coupons
    models.push(
        {
            model: 'gift.voucher.pos',
            fields: ['id', 'voucher_type', 'name', 'product_id', 'e_date', 'product_categ','check_voucher', 'customer_required','limit_to_membership'],
            loaded: function (self, vouchers) {
                    self.vouchers = vouchers;
            },
        },{
            model: 'res.branch',
            fields: ['id', 'name'],
            loaded: function (self, branches) {
                self.branches= branches;
            },
        },{
            model: 'gift.coupon.pos',
            fields: ['id', 'name', 'code', 'voucher', 'start_date',
                'end_date', 'partner_id', 'limit', 'total_avail', 'voucher_val', 'type','check_coupon','coupon_order', 'customer_required','membership_related'],
            //domain: function(self){ return [['voucher','=',2]]; },            
            loaded: function (self, coupons) {
                self.coupons = coupons;
        },
        }
        );
    
	var MyMessagePopup = pos_popup.extend({
		template: 'MyMessagePopup_vouchers',
		
		init: function(parent) {
            return this._super(parent);
        },
        show: function(options){
            options = options || {};
            this._super(options);
            this.renderElement();
            this.$('#voucher_selected_id').focus();
        },
        renderElement: function () {
            this._super();
            var self = this;
            var order = this.pos.get_order();

            $('.voucher_selected_id, .branch_selected_id').change(function () {
            	 var current_order = self.pos.get_order();
                 var coupon = $(".custom_coupon_code").val();
                 console.log("current_order.....1................",current_order)

		
	
                 if (current_order.orderlines.models && current_order.orderlines.models.length == 0){
                     self.gui.show_popup('error',{
                         'title': _t('No products !'),
                         'body': _t('You cannot apply coupon without products.'),
                     });
                 }

             	var voucher_text;
             	var voucher;
		var v_membership;
             	 $('.voucher_selected_id').children('option:selected').each(function(idx,el){
                 	voucher = el.value
                 	voucher_text = el.text;
			var customer = self.pos.get_client();
			for(var i in self.pos.vouchers){
				//console.log("vouchers[i]['name']",self.pos.vouchers[i]['name']);
				//console.log("voucher_text",voucher_text,voucher);
				if (self.pos.vouchers[i]['name'] == voucher_text){
					v_membership = self.pos.vouchers[i]['limit_to_membership'][0]
					break;
				}
			     }
			//console.log("customer",customer)
			//console.log("v_membership",v_membership);
			//console.log("customer.loyalty_id[0]",customer.loyalty_id[0]);
			if(customer && v_membership && v_membership != customer.loyalty_id[0] ){
				console.log("v_membership",v_membership);
				voucher = '';
                     		self.gui.show_popup('error',{
                         	'title': _t('Error !'),
                         	'body': _t('Please check Membership and Customer'),
                     });
                  }
                 });
             	 
              	var branch_text;
             	var branch;
             	 $('.branch_selected_id').children('option:selected').each(function(idx,el){
             		branch = el.value
             		branch_text = el.text;
                 });
             	 
             	 console.log('--------------');
             	 console.log(branch_text);
             	 console.log(branch);
             	 console.log('--------------');
             	 
                 
                 if (voucher!='' && branch!=''){
					var temp = {'voucher_id': voucher,'branch_id': branch};
					var order_json = order.export_as_JSON();
	                 
	             	new Model('gift.coupon.pos').call('find_coupon', ['', temp,order_json]).done(function (result) {
	             		if(!result){
	             			$('.coupon_body').css('display','none');
	             			$('.coupon_status').css('display','');
	             			$(".coupon_status_p").text("No coupon found!");
		                    $(".custom_coupon_code").val('');    	
		                    $(".custom_coupon_code_visible").val('');
		                    $(".coupon_id").val('');
	             		}else{
	             			$('.coupon_body').css('display','');
	             			$('.coupon_status').css('display','none');
		                    $(".custom_coupon_code").val(result['coupon_code']);            	
		                    $(".custom_coupon_code_visible").val(result['coupon_code']);
		                    $(".coupon_id").val(result['coupon_id']);
	             		}
	            	});
                 }else{
	                    $(".custom_coupon_code").val('');    	
	                    $(".custom_coupon_code_visible").val('');
	                    $(".coupon_id").val('');
                 }
            });
            
            this.$(".confirm-coupon").click(function () {

                var partner_id = false
               /* if (order.get_client() != null)
                    partner_id = order.get_client();

                if (partner_id==false) {
                	self.gui.show_popup('confirm',{
                        'title': _t('Select Customer!'),
                        'body': _t('Kindly Select Customer First!'),
                    });
                	return false;
                }*/                
            	
                var coupon_exists = $(".custom_coupon_code_visible").val();
                console.log(coupon_exists);
                if(coupon_exists==''){

                	self.gui.show_popup('error',{
                        'title': _t('Select Coupon First!'),
                        'body': _t('No Coupon is Selected!!'),
                    });
                	return false;
                	
                } 
        
            	self.gui.close_popup();
            });
        },
	});
	gui.define_popup({ name: 'voucher_popup', widget: MyMessagePopup });
	


	var _super = pos_model.Order;
	pos_model.Order = pos_model.Order.extend({

	    finalize: function(){
	        var client = this.get_client();
            $('.coupon_body').css('display','none');
 			$('.coupon_status').css('display','');
 			$(".coupon_status_p").text("No coupon found!");
            $(".custom_coupon_code").val('');    	
            $(".custom_coupon_code_visible").val('');
            $(".coupon_id").val('');	        
	        _super.prototype.finalize.apply(this,arguments);
	    },

	    export_for_printing: function(){
	        var json = _super.prototype.export_for_printing.apply(this,arguments);
	        json.coupon_availed = $(".coupon_id").val();
	        json.coupon_availed_code = $(".custom_coupon_code_visible").val();	        
	        return json;
	    },

	    export_as_JSON: function(){
	        var json = _super.prototype.export_as_JSON.apply(this,arguments);
	        json.coupon_availed = $(".coupon_id").val();
	        return json;
	    },
	});	
	
	
	//Custom Code
	var CustomButton = screens.ActionButtonWidget.extend({
	    template: 'CustomButton',
	    init: function(parent) {
            return this._super(parent);
        },
        renderElement: function () {
            var self = this;
            this._super();
            this.$(".manual-coupon").click(function () {
                self.gui.show_popup('voucher_popup',{
                    'title': _t('Generate Coupon'),
                });
            });
        },
	});
	
	screens.define_action_button({
	    'name': 'custom_button',
	    'widget': CustomButton,
	});
});

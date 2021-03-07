odoo.define("voucher_gift_pos.coupons", function (require) {
    "use strict";
    var core = require('web.core');
    var pos_model = require('point_of_sale.models');
    var pos_popup = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var models = pos_model.PosModel.prototype.models;
    var PosModelSuper = pos_model.PosModel;
    var OrderSuper = pos_model.Order;
    var Model = require('web.DataModel');
    var _t = core._t;
    var utils = require('web.utils');
    var PosScreens = require('point_of_sale.screens')
    var PaymentScreenWidget = PosScreens.PaymentScreenWidget
    var PosBaseWidget = require('point_of_sale.BaseWidget');

    // var VoucherWidgetNew = PosScreens.ActionButtonWidget.extend({
    //     template:"VoucherWidgetNew",
    //     init: function(parent) {
    //         return this._super(parent);
    //     },
    //     renderElement: function () {
    //         var self = this;
    //         this._super();
    //         this.$(".coupons").click(function () {
    //             var current_user_id = self.pos.user.id;
    //             self.gui.show_popup('auto_pin_validation', {});
    //             var conf = self.pos.config
    //             $('.auto_pin_apply').click(function(){
    //                 var user_pin = parseInt($('#auto_pin').text().trim());
    //                 new Model("res.users").call("check_promotion_pin",
    //                     [conf.approvers_ids, user_pin]).then(function (res) {
    //                     if (res) {
    //                         self.gui.show_popup('coupon',{
    //                             'title': _t('Enter your Coupon'),
    //                         });
    //                     } else {
    //                         alert("PIN Does not Match!");
    //                     }
    //                 });
    //             });
    //         });
    //     },
    // });

    // PosScreens.ProductScreenWidget.include({
    //     start: function(){
    //         this._super();
    //         this.coupons = new VoucherWidgetNew(this,{});
    //         this.coupons.replace(this.$('.placeholder-VoucherWidgetNew'));
    //     },
    // });

    var round_pr = utils.round_precision;
    var CouponPopupClass = _.filter(gui.Gui.prototype.popup_classes, function(c){
        return c.name === 'coupon';
    })
    var CouponPopupWidget = CouponPopupClass[0].widget;
     // For returning Selected Coupon and Voucher
     function find_coupon(code, coupons, vouchers) {
        var coupon = [];
        for(var i in coupons){
            if (coupons[i]['code'] == code){
                coupon.push(coupons[i]);
            }
        }
        if(coupon.length > 0){
            for(var i in vouchers){
                if (vouchers[i]['id'] == coupon[0]['voucher'][0]){
                    coupon.push(vouchers[i]);
                    return coupon;
                }
            }
        }
        return false
    }

    function check_coupon_applicable_on_this(voucher,order_items,coupon, applied_coupons, customer) {
        //checking already applied
        for (var i in order_items[0].order.coupon_stack){
            if (order_items[0].order.coupon_stack[i].code == coupon[0].code ){
                return false
            }
        }

        // checking it is already used or not
        var applicable = false
        var voucher_obj = false
        var categ = []
        var product = []
        var brand = []

        for (var i in order_items){
            categ.push(order_items[i]['product']['pos_categ_id'][0]);
            product.push(order_items[i]['product']['id']);
            }
        for(var i in voucher){
                if (voucher[i]['id'] == coupon[0]['voucher'][0]){
                    voucher_obj = voucher[i]
                }
            }
        if (voucher_obj && voucher_obj['voucher_type'] == 'all'){
            return true
        }
        else if (voucher_obj && voucher_obj['voucher_type'] == 'product'){
            var found = product.find( val => voucher_obj['product_id'].includes(val) )
            if (found){
                return true
            }
            else{
                return false
            }
        }
        else if (voucher_obj && voucher_obj['voucher_type'] == 'category'){
            var found = categ.find( val => voucher_obj['product_categ'].includes(val) )
            if (found){
                return true
            }
            else{
                return false
            }
        }
        else if (voucher_obj && voucher_obj['voucher_type'] == 'Brand'){
            var found = brand.find( val => voucher_obj['brand_ids'].includes(val) )
            if (found){
                return true
            }
            else{
                return false
            }
        }

        return false;
    }

    function check_validity(coupon, applied_coupons, customer) {
        // checking it is already used or not
        
        for (var i in applied_coupons){
            var customer_id = customer && customer['id'] || false
            if(applied_coupons[i]['coupon_pos'] == coupon[0]['code'] && applied_coupons[i]['partner_id'][0] == customer_id){
                return applied_coupons[i];
            }
        }
        return false;
    }

    function check_expiry(start, end) {
        var today = moment().format('YYYY-MM-DD');
        if(start && end) {
            if (today < start || today > end)
                return false;
        }
        else if(start){
            if (today < start)
                return false;
        }
        else if(end){
            if (today > end)
                return false;
        }
        return true;
    }

    function get_coupon_product(products) {
        for (var i in products){
            if(products[i]['display_name'] == 'Gift-Coupon')
                return products[i]['id'];
        }
        return false;
    }
    pos_model.load_models([{
        model:  'product.product',
        fields: ['display_name', 'list_price','price','pos_categ_id', 'taxes_id', 'barcode', 'default_code',
                 'to_weight', 'uom_id', 'description_sale', 'description', 'product_tmpl_id','tracking',
                 'product_brand_id', 'categ_id'],
        order:  ['sequence','default_code','name'],
        domain: [['sale_ok','=',true],['available_in_pos','=',true]],
        context: function(self){ return { pricelist: self.pricelist.id, display_default_code: false }; },
        loaded: function(self, products){
            self.db.add_products(products);
        },
	}], { 'after': 'product.product' });
    models.push({
            model: 'gift.voucher.pos',
            fields: ['id', 'voucher_type', 'name', 'product_id', 'e_date', 'product_categ','min_order_value','brand_ids', 'customer_required','limit_to_membership'],
            loaded: function (self, vouchers) {
                    self.vouchers = vouchers;
            },
            },)
            
    pos_model.load_fields('gift.coupon.pos', ['min_order_value','is_stackable','sequence', 'customer_required','membership_related'])
    pos_model.load_fields('res.partner',['loyalty_id']);
    CouponPopupWidget.include({

        renderElement: function () {
            this._super();
            this.$(".validate_coupon").unbind('click')
            this.$(".confirm-coupon").unbind('click')
            var self = this;
            this.$(".validate_coupon").on('click',function () {
                // checking the code entered
                var current_order = self.pos.get_order();
                var coupon = $(".coupon_code").val();
                if (current_order.orderlines.models.length == 0){
                    self.gui.show_popup('error',{
                        'title': _t('No products !'),
                        'body': _t('You cannot apply coupon without products.'),
                    });
                }
                else if(coupon){
                    var coupon_res = find_coupon(coupon, self.pos.coupons, self.pos.vouchers);
                    if (coupon_res) {
                        var customer_required = coupon_res[0].customer_required && coupon_res[1].customer_required
                        if(!customer_required || self.pos.get_client()){
                            var customer = self.pos.get_client();
                            //var coupon_res = find_coupon(coupon, self.pos.coupons, self.pos.vouchers);
                            var flag = true;
			                var membership = true;
                            var total_amt = 0.0
                            for (var k in current_order.orderlines.models) {
                                    total_amt += (current_order.orderlines.models[k].price * current_order.orderlines.models[k].quantity)
                            }
                            if(customer && coupon_res[0].membership_related[0] && coupon_res[0].membership_related[0] != customer.loyalty_id[0] ){

                                flag = false;
                                membership = false;
                                $(".coupon_status_p").text("!");
                            }
                            if(coupon_res[0] && total_amt < coupon_res[0].min_order_value){

                                flag = false;

                                $(".coupon_status_p").text("Unable to apply coupon. Check coupon validity.!");
                            }
                            // is there a coupon with this code which has balance above zero
                            if(flag && coupon_res && coupon_res[0]['total_avail'] > 0){
                                var applied_coupons = self.pos.applied_coupon;
                                var order_items = current_order.orderlines.models;
                                var applicable_on_this = check_coupon_applicable_on_this(self.pos.vouchers,order_items,coupon_res, applied_coupons, customer);

                                if (!applicable_on_this) {
                                    flag = false;
                                }
                                // checking coupon status
                                var coupon_stat = check_validity(coupon_res, applied_coupons, customer);

                                // if this coupon was for a particular customer and is not used already
                                if((customer && coupon_res[0]['partner_id'].length > 0) && !(coupon_res[0]['partner_id'].includes(customer["id"]))){

                                    flag = false;
                                }
                                var today = moment().format('YYYY-MM-DD');
                                // checking coupon balance and expiry
                                
                                if(flag && coupon_stat && coupon_stat.number_pos < coupon_res[0]['limit'] && today <= coupon_res[0]['end_date']){

                                    // checking coupon validity
                                    flag = check_expiry(coupon_res[0]['start_date'], coupon_res[0]['end_date']);
                                }

                                // this customer has not used this coupon yet
                                else if(flag && !coupon_stat && today <= coupon_res[0]['end_date']){

                                    flag = check_expiry(coupon_res[0]['start_date'], coupon_res[0]['end_date']);
                                }
                                else{
                                    flag = false;
                                    $(".coupon_status_p").text("Unable to apply coupon. Check coupon validity.!");
                                }
                                
                            }
                            else if(membership == false){
                	            $(".coupon_status_p").text("Please check Membership and Customer");
			                } else{
                                flag = false;
                                $(".coupon_status_p").text("Invalid code or no coupons left. Please try again !!");
                            }

                            if(flag){

                                var val = coupon_res[0]['type'] == 'fixed' ?
                                    coupon_res[0]['voucher_val'] : coupon_res[0]['voucher_val'] + "%";
                                var obj = $(".coupon_status_p").text("voucher value is : "+val+" \n" +
                                    " Do you want to proceed ? \n This operation cannot be reversed.");
                                obj.html(obj.html().replace(/\n/g,'<br/>'));
                                var order = self.pos.get_order();
                                order.set_coupon_value(coupon_res[0]);
                            }
                            self.flag = flag;
                            if(flag){
                               $(".confirm-coupon").css("display", "block");
                            } else if(membership == false){
				                $(".coupon_status_p").text("Please check Membership and Customer");
			                } else{
                                var ob = $(".coupon_status_p").text("Invalid code or no coupons left. \nPlease check coupon validity.\n" +
                                    "or check whether the coupon usage is limited to a particular customer or product(s)");
                                ob.html(ob.html().replace(/\n/g,'<br/>'));
                            }
                        } else{
                            $(".coupon_status_p").text("Please select a customer !!");
                        }
                    } else {
                        var ob = $(".coupon_status_p").text("Invalid Coupon code. \nPlease check coupon code.\n");
                        ob.html(ob.html().replace(/\n/g,'<br/>'));
                    }
                }
            });

            this.$(".confirm-coupon").click(function () {
                // verifying and applying coupon
                if(self.flag){
                    var order = self.pos.get_order();
                    var vouchers = self.pos.vouchers;
                    var voucher = null;
                    for (var i in vouchers){
                        if(vouchers[i]['id'] == order.coupon_status.voucher[0]){
                            voucher = vouchers[i];
                            break;
                        }
                    }

                    var lines = order ? order.orderlines : false;
                    var in_stack = false
                    for (var i in order.coupon_stack){
                        if (order.coupon_stack[i]['code'] == order.coupon_status['code']){
                            in_stack = true;
                            break;
                        }
                    }
                    var temp = {
                            'coupon_pos': order.coupon_status['code'],
                            'voucher': voucher['id'],
                            'ordername': order.name,
                        };
                    new Model('gift.coupon.pos').call('check_stackable_coupon', ['', temp]).done(function (result) {
                    	if(!result){
                            self.gui.close_popup();
                            self.gui.show_popup('error',{
                                'title': _t('Unable to apply coupon !'),
                                'body': _t('Either coupon is already applied or you have not selected any products.'),
                            });
                    	}else {

                            if(lines.models.length > 0 && order.check_voucher_validy()) {
                                var product = self.pos.db.get_product_by_id(self.coupon_product);
                                var price = -1;
                                if (order.coupon_status['type'] == 'fixed') {
                                    price *= order.coupon_status['voucher_val'];
                                }
                                if (order.coupon_status['type'] == 'percentage') {
//                                    price *= order.get_total_with_tax() * order.coupon_status['voucher_val'] / 100;
                                    price *= order.get_price_total_by_voucher() * order.coupon_status['voucher_val'] / 100;
                                }
                                if ((order.get_total_with_tax - price) <= 0) {
                                    self.gui.close_popup();
                                    self.gui.show_popup('error', {
                                        'title': _t('Unable to apply coupon !'),
                                        'body': _t('Coupon amount is too large to apply. The total amount cannot be negative'),
                                    });
                                }
                                else{
                                     order.coupon_stack.push(order.coupon_status);
                                    order.coupon_applied();
//                                    if (order.stackable){
//                                        var order_app_cou = order.order_line.filter(item['code'] != false);
////                                    for (var cop in order.coupon_stack){
////                                        for (var li in order.order_line){
////                                        }
////                                    }
    ////
//                                    };

                                    order.add_product(product, {quantity: 1, price: price});
                                    // updating coupon balance after applying coupon
                                    var client = self.pos.get_client();

                                    var temp = {
                                        'partner_id': client && client['id'] || false,
                                        'coupon_pos': order.coupon_status['code'],
                                        'voucher': voucher['id'],
                                        'date_used': moment().format('YYYY-MM-DD'),
                                        'coupon_amount': price,
                                        'order_amount': order.get_total_with_tax(),
                                        'order_name': order.name,
                                    };

                                    new Model('partner.coupon.pos').call('update_history', ['', temp]).done(function (result) {
                                        // alert("result")
                                        var applied = self.pos.applied_coupon;
                                        var already_used = false;
                                        for (var j in applied) {
                                            var partner = client && client['id'] || false
                                            if (applied[j]['partner_id'][0] == partner &&
                                                applied[j]['coupon_pos'] == order.coupon_status['code']) {
                                                applied[j]['number_pos'] += 1;
                                                already_used = true;
                                                break;
                                            }
                                        }
                                        if (!already_used) {
                                            var partner_id = client && client['id'] || false
                                            var partner_name = client && client['name'] || false
                                            var temp = {
                                                'partner_id': [partner_id, partner_name],
                                                'number_pos': 1,
                                                'coupon_pos': order.coupon_status['code'],
                                                'order_name': order.name,
                                            };
                                            self.pos.applied_coupon.push(temp);
                                        }
                                    });
                                    self.gui.close_popup();
                                }
                            }
                            else{
                                self.gui.close_popup();
                                self.gui.show_popup('error',{
                                    'title': _t('Unable to apply coupon !'),
                                    'body': _t('This coupon is not applicable on the products or category or brand you have selected !'),
                                });
                            }
                        }

                    });
                    
                    //var is_stackable_cop =  (order.coupon_stack.length > 0) ? order.coupon_status['is_stackable'] : true ;
                    //if(order.coupon && !order.stackable || in_stack || !is_stackable_cop){
                    
                }
                else{
                    self.gui.close_popup();
                    self.gui.show_popup('error',{
                        'title': _t('Unable to apply coupon !'),
                        'body': _t('Invalid Code or no Coupons left !'),
                    });
                }
            });
        },
    });

    var _super = pos_model.Order;
pos_model.Order = pos_model.Order.extend({
        export_for_printing: function(){
            var json = _super.prototype.export_for_printing.apply(this,arguments);
            var order = this.pos.get_order();
            var order_json = order.export_as_JSON();
            new Model('gift.coupon.pos').call('get_gift_voucher_from_pos',[order_json]).then(function(coupon_code){

            if (coupon_code && coupon_code['coupon']) {
                json.coupon = {
                coupon: coupon_code['coupon'],
                };
            }
            })
            return json;
            },
        initialize: function(attributes,options){
            this.coupon = false;
            this.stackable = false;
            this.coupon_status = [];
            this.coupon_stack = [];
            return OrderSuper.prototype.initialize.call(this, attributes,options);;
        },
        set_coupon_value: function (coupon) {
            this.coupon_status = coupon;
            return;
        },
        coupon_applied: function () {
            this.coupon = true;
            this.stackable = this.coupon_status['is_stackable'];
            this.export_as_JSON();
            return;
        },

        get_price_total_by_voucher: function(){
            var self = this;
            var order = self.pos.get_order();
            var vouchers = self.pos.vouchers;
            var voucher = null;
            for (var i in vouchers){
                if(vouchers[i]['id'] == self.coupon_status.voucher[0]){
                    voucher = vouchers[i];
                    break;
                }
            }
            if(voucher){
                switch(voucher.voucher_type){
                    case 'product': {
                        var lines = order.orderlines.models;
                        var product  = []
                        var price = 0.0
                        for (var p in lines){
                            if(voucher['product_id'].includes(lines[p]['product']['id'])){
                                price += lines[p].get_display_price();
                            }
                        }
                        return price
                        break;
                    }
                    case 'category':{
                        var lines = order.orderlines.models;
                        var price = 0.0
                        var categ = []
                        for (var p in lines){
                            if(lines[p].product.pos_categ_id){
                                if(voucher['product_categ'].includes(lines[p]['product']['pos_categ_id'][0])){
                                    price += lines[p].get_display_price();
                                }
                            }
                        }
                        return price
                        break;
                    }
                    case 'Branch':{
                        var lines = order.orderlines.models;
                        var price = 0.0;
                        var brand = []
                        for (var p in lines){
                                if(voucher['brand_id'].includes(lines[p]['product']['brand_id'])){
                                    price += lines[p].get_display_price();
                                }
                            }
                        return price
                        break;

                    }
                    case 'all': price = order.get_total_with_tax(); return price; break;
                    default: break;
                }
        }
        },

        check_voucher_validy: function () {
            var self = this;
            var order = self.pos.get_order();
            var vouchers = self.pos.vouchers;
            var voucher = null;
            for (var i in vouchers){
                if(vouchers[i]['id'] == self.coupon_status.voucher[0]){
                    voucher = vouchers[i];
                    break;
                }
            }
            var flag ;
            if(voucher){
                switch(voucher.voucher_type){
                    case 'product': {
                        var lines = order.orderlines.models;
                        var product  = []
                        for (var p in lines){
                            product.push(lines[p]['product']['id']);
                        }
                        var found = product.find( val => voucher['product_id'].includes(val) )
                        if (found){
                            flag = true;
                        }
                        else
                            flag = false;
                        break;
                    }
                    case 'category':{
                        var lines = order.orderlines.models;
                        var categ = []
                        for (var p in lines){
                            if(lines[p].product.pos_categ_id){
                                categ.push(lines[p]['product']['pos_categ_id'][0]);
                            }
                        }
                        var found = categ.find( val => voucher['product_categ'].includes(val) )
                        if (found){
                            return true
                        }
                        else{
                            return false
                        }
                        if(voucher.product_categ[0] in category){
                            flag = true;
                        }
                        else{
                            flag = false;
                        }
                        break;
                    }
                    case 'Brand':{
                        var lines = order.orderlines.models;
                        var brand = []
                        for (var p in lines){
                                brand.push(lines[p]['product']['brand_id'][0]);
                            }
                        var found = brand.find( val => voucher['brand_ids'].includes(val) )
                        if (found){
                            flag = true;
                        }
                        else
                            flag = false;
                        break;

                    }
                    case 'all': flag = true; break;
                    default: break;
                }
            }
            return flag;
        },
        export_as_JSON: function () {
            var self = OrderSuper.prototype.export_as_JSON.call(this);
            self.coupon = this.coupon;
            self.coupon_status = this.coupon_status;
            return self;
        },
        init_from_JSON: function(json) {
            this.coupon = json.coupon;
            this.coupon_status = json.coupon_status;
            OrderSuper.prototype.init_from_JSON.call(this, json);
        },
        get_total_without_tax: function() {
            var res = OrderSuper.prototype.get_total_without_tax.call(this);
            // var final_res = round_pr(this.orderlines.reduce((function(sum, orderLine) {
            //     return sum + (orderLine.get_unit_price() * orderLine.get_quantity() * (1.0 - (orderLine.get_discount() / 100.0)));
            // }), 0), this.pos.currency.rounding);
            // return final_res;
            return res
        },

    });
PosScreens.OrderWidget.include({
        remove_orderline: function(order_line){
            var res = this._super(order_line);
            var self = this;
            if (order_line.product.display_name == "Gift-Coupon"){
                order_line.order.coupon = false;
                this.coupon = false;
                new Model('partner.coupon.pos').call('delete_history_from_current_order', ['',order_line.order.name]);
                for (var i in order_line.order.coupon_stack){
                    if (order_line.line_coupon_code == order_line.order.coupon_stack[i]['code']){
                            order_line.order.coupon_stack.splice(i,1);
                    }
                }
                if (order_line.order.coupon_stack.length < 1){
                        order_line.order.stackable = false;
                        this.stackable = false;
                        order_line.order.coupon = false;
                        this.coupon = false;
                    }
                for (var i in self.pos.applied_coupon){
                    if (self.pos.applied_coupon[i]['order_name'] == order_line.order.name){
                            self.pos.applied_coupon.splice( i, 1 );
                    }
                }
            }
            return res
        },
    });



var _super_orderline = pos_model.Orderline.prototype;

pos_model.Orderline = pos_model.Orderline.extend({
   initialize: function(attr, options){
       _super_orderline.initialize.call(this,attr,options);
       this.line_coupon_code = false;
   },
   init_from_JSON: function(json){
      _super_orderline.init_from_JSON.call(this, json);
      this.line_coupon_code = json.line_coupon_code || false;
   },

   set_line_coupon_code: function(coupon) {
      this.line_coupon_code = coupon.code;
      this.trigger('change');
   },
    can_be_merged_with: function(orderline) {
            if (this.line_coupon_code) {
                return false;
            } else {
                return _super_orderline.can_be_merged_with.apply(this,arguments);
            }
        },

});

var _super_order = pos_model.Order.prototype;
pos_model.Order = pos_model.Order.extend({
    initialize: function() {
       _super_order.initialize.apply(this,arguments);
       this.line_coupon_code = false;
    },
   export_as_JSON: function() {
       var json = _super_order.export_as_JSON.apply(this,arguments);
       json.line_coupon_code = this.get_line_coupon_code() || false;
       return json;
   },
   init_from_JSON: function(json) {
       _super_order.init_from_JSON.apply(this,arguments);
       this.line_coupon_code = json.line_coupon_code || false;
   },

   get_line_coupon_code: function(){
       return this.line_coupon_code;
   },

add_product: function(product, options){
    _super_order.add_product.apply(this,arguments);
    var line_coupon_code = this.coupon_status ? this.coupon_status['code'] : '' ;
    var selected_order_line = this.get_selected_orderline();
    if(selected_order_line){
        selected_order_line.line_coupon_code = line_coupon_code;
        selected_order_line.trigger('change', selected_order_line);
    }
    // selected_order_line.line_coupon_code = line_coupon_code;
    // selected_order_line.trigger('change', selected_order_line);
},
});
});

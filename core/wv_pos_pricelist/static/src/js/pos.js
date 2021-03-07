odoo.define('wv_pos_pricelist', function (require) {
"use strict";
    var models = require('point_of_sale.models');
    var chrome = require('point_of_sale.chrome');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var _t = core._t;

    models.load_fields('res.partner','pos_pricelist_id');
    models.load_fields('product.product','default_selection');
    models.load_models([
        {
            model: 'pos.pricelist',
            fields: ['id', 'name'],
            loaded: function (self, pricelists) {
                self.pricelists = pricelists;
            },
        },{
            model: 'pos.pricelist.items',
            fields: ['id', 'fixed_price', 'date_end', 'applied_on', 'min_quantity',
                'percent_price', 'date_start', 'product_tmpl_id', 'pos_pricelist_id', 'compute_price', 'categ_id','item1'],
            loaded: function (self, pricelist_items) {
                self.pricelist_items = pricelist_items;
            },
        },
        {
            model: 'product.template',
            fields: ['id', 'categ_id'],
            loaded: function (self, category) {
                self.category = category;
            },
        }
    ]);
    
    var OrderSuper = models.Order;
    models.Order = models.Order.extend({
        initialize: function(attributes,options){
            var result = OrderSuper.prototype.initialize.apply(this,arguments);
            this.selected_pricelist_id = this.pos.config.default_pricelist[0];
            return result;
            
        },
        apply_pricelist: function(pricelist_id){
            var self = this;
            if(!this.pos.config.allow_pricelist){
                return 
            }
            var pricelist_items = self.pos.pricelist_items;
            var items = [];
            for (var i in pricelist_items){
                if(pricelist_items[i].pos_pricelist_id[0] == pricelist_id){
                    items.push(pricelist_items[i]);
                }
            }
            pricelist_items = [];
            var today = moment().format('YYYY-MM-DD');
            for (var i in items){
                if(((items[i].date_start == false) || (items[i].date_start <= today))&& ((items[i].date_end == false) || (items[i].date_end >= today))){
                    pricelist_items.push(items[i]);
                }
            }
            var global_items = [];
            var category_items = [];
            var category_ids = [];
            var product_items = [];
            var product_ids = [];
            var default_code_items = [];
            var default_items = [];
            for(var i in pricelist_items){
                switch(pricelist_items[i].applied_on){
                case 'global': global_items.push(pricelist_items[i]); break;
                case 'product_category': category_items.push(pricelist_items[i]);
                    category_ids.push(pricelist_items[i].categ_id[0]) ; break;
                case 'product': product_items.push(pricelist_items[i]);
                    product_ids.push(pricelist_items[i].product_tmpl_id[0]) ;break;
                case 'default_code': default_code_items.push(pricelist_items[i]);
                    default_items.push(pricelist_items[i].item1[1]) ;break;

                }
            }
            var order = self.pos.get_order();
            var lines = order ? order.get_orderlines() : null;
            for (var l in lines){
                var product_item = self.find_pricelist_item(lines[l].product.product_tmpl_id, product_ids);
                var categ_item = self.find_pricelist_item(lines[l].product.pos_categ_id[0], category_ids);
                var temp = -1;
                var new_price = lines[l].product.price;
                if(product_item){
                    for(var j in product_items){
                        if(product_items[j].product_tmpl_id[0] == lines[l].product.product_tmpl_id){
                           if(lines[l].quantity >= product_items[j].min_quantity){
                                if(temp < 0){
                                    temp = lines[l].quantity - product_items[j].min_quantity;
                                    new_price = self.set_price(lines[l], product_items[j]);
                                }
                                else if(temp > (lines[l].quantity - product_items[j].min_quantity) &&
                                    (lines[l].quantity - product_items[j].min_quantity) >= 0){
                                    temp = lines[l].quantity - product_items[j].min_quantity;
                                    new_price = self.set_price(lines[l], product_items[j]);
                                }
                            }
                        }
                    }
                    lines[l].set_unit_price(new_price);
                }
                else if(default_code_items.length > 0){
                    for(var j in default_code_items){
                        if(default_code_items[j].item1[0] == lines[l].product.default_selection[0]){
                           if(lines[l].quantity >= default_code_items[j].min_quantity)
                            {
                                if(temp < 0){
                                    temp = lines[l].quantity - default_code_items[j].min_quantity;
                                    new_price = self.set_price(lines[l], default_code_items[j]);
                                }
                                else if(temp > (lines[l].quantity - default_code_items[j].min_quantity) &&
                                    (lines[l].quantity - default_code_items[j].min_quantity) >= 0){
                                    temp = lines[l].quantity - default_code_items[j].min_quantity;
                                    new_price = self.set_price(lines[l], default_code_items[j]);
                                }
                            }
                        }
                    }
                    lines[l].set_unit_price(new_price);
                }
                else if(categ_item){
                    for(var j in category_items){
                        if(category_items[j].categ_id[0] == lines[l].product.pos_categ_id[0]){
                           if(lines[l].quantity >= category_items[j].min_quantity)
                            {
                                if(temp < 0){
                                    temp = lines[l].quantity - category_items[j].min_quantity;
                                    new_price = self.set_price(lines[l], category_items[j]);
                                }
                                else if(temp > (lines[l].quantity - category_items[j].min_quantity) &&
                                    (lines[l].quantity - category_items[j].min_quantity) >= 0){
                                    temp = lines[l].quantity - category_items[j].min_quantity;
                                    new_price = self.set_price(lines[l], category_items[j]);
                                }
                            }
                        }
                    }
                    lines[l].set_unit_price(new_price);
                }
                else if(global_items.length > 0){
                    for(var j in global_items){
                        if(lines[l].quantity >= global_items[j].min_quantity)
                        {
                            if(temp < 0){
                                temp = lines[l].quantity - global_items[j].min_quantity;
                                new_price = self.set_price(lines[l], global_items[j]);
                            }
                            else if(temp > (lines[l].quantity - global_items[j].min_quantity) &&
                                (lines[l].quantity - global_items[j].min_quantity) >= 0){
                                temp = lines[l].quantity - global_items[j].min_quantity;
                                new_price = self.set_price(lines[l], global_items[j]);
                            }
                        }
                    }
                    lines[l].set_unit_price(new_price);
                }
                else{
                    lines[l].set_unit_price(lines[l].product.price);
                }
            }
        },
        add_product: function (product, options) {
            var self = this;
            var pricelist_id = this.selected_pricelist_id;
            OrderSuper.prototype.add_product.call(this, product, options);
            if (pricelist_id){
                self.apply_pricelist(pricelist_id);
            }
        },
        set_price: function (line, item) {
            var new_price = 0;
            switch (item.compute_price){
                case 'fixed': new_price = item.fixed_price; break;
                case 'percentage': new_price = line.product.price -(line.product.price * item.percent_price / 100); break;
            }
            return new_price;
        },
        find_pricelist_item: function (id, item_ids) {
            for (var j in item_ids){
                if(item_ids[j] == id){
                    return true;
                    break;
                }
            }
            return false;
        },
        set_client: function(client){
            var self = this;
            var current_pricelist = $('.o_pricelist_button');
            if(client){
                if (client.pos_pricelist_id){
                    current_pricelist.html(client.pos_pricelist_id[1]);
                    var order = self.pos.get_order();
                    order.selected_pricelist_id = client.pos_pricelist_id[0];
                    if (order) {
                        if (order.orderlines.length) {
                            self.apply_pricelist(client.pos_pricelist_id[0]);
                        }
                    }
                }
            }
            OrderSuper.prototype.set_client.call(this, client);
        },
        export_as_JSON: function(){
            var json = OrderSuper.prototype.export_as_JSON.apply(this,arguments);
            json.pos_pricelist = this.selected_pricelist_id;
            return json;
        },
    });

    var OrderlineSuper = models.Orderline;
    models.Orderline = models.Orderline.extend({
        set_quantity: function(quantity){
            OrderlineSuper.prototype.set_quantity.call(this, quantity);
            var pricelist_id = this.order.selected_pricelist_id;
            if (pricelist_id) {
                this.order.apply_pricelist(pricelist_id);
            }
        },
    });
    
    var SetPriceListButton = screens.ActionButtonWidget.extend({
        template: 'SetPriceListButton',
        init: function (parent, options) {
            this._super(parent, options);

            this.pos.get('orders').bind('add remove change', function () {
                this.renderElement();
            }, this);

            this.pos.bind('change:selectedOrder', function () {
                this.renderElement();
            }, this);
        },
        button_click: function () {
            var self = this;
            var pricelists = _.map(self.pos.pricelists, function (pricelist) {
                return {
                    label: pricelist.name,
                    item: pricelist.id
                };
            });
            self.gui.show_popup('selection',{
                title: _t('Select Pricelist'),
                list: pricelists,
                confirm: function (pricelist) {
                    var order = self.pos.get_order();
                    var client = order.get_client();
                    order.apply_pricelist(pricelist);
                    order.selected_pricelist_id = pricelist;
                    self.renderElement();
                },
                is_selected: function (pricelist) {
                    return pricelist.name === self.pos.get_order().selected_price.name;
                }
            });
        },
        get_current_pricelist_name: function () {
            var name = _t('Pricelist');
            var order = this.pos.get_order();

            if (order) {
                var selected_pricelist_id = order.selected_pricelist_id;
                for(var i=0;i<this.pos.pricelists.length;i++){
                    if(this.pos.pricelists[i].id == selected_pricelist_id)
                    {
                        name = this.pos.pricelists[i].name;
                    } 
                }
            }
             return name;
        },
    });

    screens.define_action_button({
        'name': 'SetPriceListButton',
        'widget': SetPriceListButton,
        'condition': function(){
            return this.pos.config.allow_pricelist;
        },
    });

});


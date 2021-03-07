odoo.define('sync_pos_orders', function(require){
    
    var Backbone = window.Backbone;
    var Core = require('web.core');
    var Session = require('web.session');
    var Chrome = require('point_of_sale.chrome');
    var Models = require('point_of_sale.models');
    var Screens = require('point_of_sale.screens');
    var longpolling = require('pos_longpolling');
    var _t = Core._t;
    var exports = {};


    Screens.ReceiptScreenWidget.extend({
        finish_order: function() {
            if (!this._locked)
                this.pos.get('selectedOrder').destroy({'reason': 'finishOrder'});
        },
    });
    Screens.OrderWidget.include({
        rerender_orderline: function(order_line){
            if (order_line.node && order_line.node.parentNode)
                return this._super(order_line);
        },
        remove_orderline: function(order_line){
            if (this.pos.get_order() && this.pos.get_order().get_orderlines().length === 0)
                return this._super(order_line);
            if (order_line.node.parentNode)
                return this._super(order_line);
        },
    });

    var PosModelSuper = Models.PosModel;
    Models.PosModel = Models.PosModel.extend({
        initialize: function(){
            var self = this;
            var channel_name = "pos.sync_session";
            var callback = this.sync_on_update;
            PosModelSuper.prototype.initialize.apply(this, arguments);
            this.sync_syncing_in_progress = false;
            this.sync_session = false;
            this.get('orders').bind('remove', function(order, collection, options){
                if (!self.sync_session.client_online) {
                    if (order.order_on_server ) {
                        self.sync_session.no_connection_warning();
                        if (self.debug)
                            console.log('PosModel initialize error');
                        return false;
                    }
                }
                order.sync_remove_order();
            });
            this.sync_session = new exports.MultiSession(this);
            this.add_channel(channel_name, callback, this);
        },
        sync_on_update: function(message, sync_all){
            var self = this;
            var message_data = '';
            var message_action = '';
            var error = false;
            this.sync_syncing_in_progress = true;
            try{
                if (this.debug){
                    console.log('TS', this.config.name, 'on_update:', JSON.stringify(message));
                }
                var order = false;
                message_data = message.data || {};
                message_action = message.action;
                if (message_data.uid){
                    order = this.get('orders').find(function(order){
                        return order.uid == message_data.uid;
                    });
                }
                if (sync_all) {
                    this.message_ID = message_data.message_ID;
                    this.sync_do_update(order, message_data);
                } else {
                    if (message_action == 'update_order')
                        this.sync_do_update(order, message_data);
                    else if (order && message_action == 'remove_order')
                        order.destroy({'reason': 'abandon'});

                    if (self.message_ID + 1 != message_data.message_ID)
                        self.sync_session.request_sync_all();
                    else
                        self.message_ID = message_data.message_ID;
                }
            }catch(error){
                error = error;
            }
            this.sync_syncing_in_progress = false;
            if (error){ throw(error); }
        },
        on_removed_order: function(removed_order,index,reason){
            if (this.sync_session){
                if (this.sync_syncing_in_progress){
                    if (this.get('orders').size() === 0)
                        this.add_new_order();
                    else
                        return this.set({'selectedOrder': this.get('orders').at(index) || this.get('orders').first()});
                    return;
                } else if (reason === 'finishOrder'){
                    if (this.get('orders').size() > 0)
                        return this.set({'selectedOrder' : this.get('orders').at(index) || this.get('orders').first()});
                    this.add_new_order();
                    this.get('selectedOrder').sync_replace_empty_order = true;
                    return;
                } 
            }
            return PosModelSuper.prototype.on_removed_order.apply(this, arguments);
        },
        sync_create_order: function(options){
            options = _.extend({pos: this}, options || {});
            return new Models.Order({}, options);
        },
                sync_do_update: function(order, data){
            var pos = this;
            this.pos_session.order_ID = data.sequence_number;
            if (!order){
                var create_new_order = pos.config.accept_incoming_orders || !(data.sync_info && data.sync_info.created.user.id != pos.sync_my_info().user.id);
                if (!create_new_order)
                    return;
                json = {
                    sequence_number: data.sequence_number,
                    pos_session_id: this.pos_session.id,
                    multiprint_resume: data.multiprint_resume,
                    uid: data.uid,
                    new_order: false,
                    lines: false,
                    statement_ids: false,
                    order_on_server: true,
                };
                order = this.sync_create_order({sync_info:data.sync_info, revision_ID:data.revision_ID, data:data, json:json});
                this.get('orders').add(order);
                this.sync_on_add_order(this.get_order());
            } else {
                order.sync_info = data.sync_info;
                order.revision_ID = data.revision_ID;
            }
            var not_found = order.orderlines.map(function(r){ return r.uid; });
            if(data.partner_id !== false)
            {
                var client = order.pos.db.get_partner_by_id(data.partner_id);
                if(!client)
                {
                    $.when(this.load_new_partners_by_id(data.partner_id)).then(function(client){
                        client = order.pos.db.get_partner_by_id(data.partner_id);
                        order.set_client(client);
                    },function(){});
                }
                order.set_client(client);
            }
            else
                order.set_client(null);

            _.each(data.lines, function(dline){
                dline = dline[2];
                not_found = _.without(not_found, dline.uid);
                var product = pos.db.get_product_by_id(dline.product_id);
                var line = order.orderlines.find(function(r){ return dline.uid == r.uid; });
                if (!line){
                    line = new Models.Orderline({}, {
                        pos: pos,
                        order: order,
                        product: product
                    });
                    line.uid = dline.uid;
                }
                line.sync_info = dline.sync_info || {};
                if(dline.price_unit !== undefined){
                    line.set_unit_price(dline.price_unit);
                }
                if(dline.qty !== undefined){
                    line.set_quantity(dline.qty);
                }
                if(dline.discount !== undefined){
                    line.set_discount(dline.discount);
                }
                if(dline.mp_skip !== undefined){
                    line.set_skip(dline.mp_skip);
                }
                if(dline.mp_dirty !== undefined){
                    line.set_dirty(dline.mp_dirty);
                }
                if(dline.note !== undefined){
                    line.set_note(dline.note);
                }
                order.orderlines.add(line);
            });

            _.each(not_found, function(uid){
                var line = order.orderlines.find(function(r){ return uid == r.uid; });
                order.orderlines.remove(line);
            });
            order.order_on_server = true;
            order.new_order = false;
        },
        sync_my_info: function(){
            var user = this.cashier || this.user;
            return {
                'user': {'id': user.id, 'name': user.name},
                'pos': {'id': this.config.id, 'name': this.config.name}
            };
        },
        sync_on_add_order: function (current_order) {
            if (!current_order)
                return;
            is_frozen = !current_order.sync_replace_empty_order;
            if (this.config.replace_empty_order && current_order.new_order && !is_frozen)
                current_order.destroy({'reason': 'abandon'});
            else if (is_frozen || !current_order.new_order || !this.config.deactivate_empty_order)
                this.set('selectedOrder', current_order);
        },
        load_new_partners_by_id: function(partner){
            var self = this;
            var def  = new $.Deferred();
            var fields = _.find(this.Models,function(model){ return model.model === 'res.partner'; }).fields;
            new Model('res.partner')
                .all({'timeout':3000, 'shadow': true})
                .filter([['id','=',partner]])
                .query(fields)
                .then(function(partners){
                    if (self.db.add_partners(partners))
                        def.resolve();
                    else
                        def.reject();
                    }, function(err,event){ 
                    event.preventDefault();
                    def.reject(); 
                });
            return def;
        },
    });

    var OrderSuper = Models.Order;
    Models.Order = Models.Order.extend({
        initialize: function(attributes, options){
            var self = this;
            options = options || {};
            if (!options.json || !('new_order' in options.json))
                this.new_order = true;

            OrderSuper.prototype.initialize.apply(this, arguments);
            this.sync_info = {};
            this.sync_replace_empty_order = false;
            this.revision_ID = options.revision_ID || 1;

            if (!_.isEmpty(options.sync_info))
                this.sync_info = options.sync_info;
            else if (this.pos.sync_session)
                this.sync_info.created = this.pos.sync_my_info();
            this.bind('change:sync', function(){ self.sync_update(); });
        },
        set_client: function(client){
            this.trigger('change:sync');
            OrderSuper.prototype.set_client.apply(this,arguments);
        },
        sync_check: function(){
            if (! this.pos.sync_session || this.pos.sync_syncing_in_progress || this.temporary)
                return;
            return true;
        },
        sync_update: function(){
            var self = this;
            if (this.new_order) {
                this.new_order = false;
                this.trigger('change:update_new_order');
                this.sequence_number = this.pos.pos_session.order_ID;
                this.pos.pos_session.order_ID = this.pos.pos_session.order_ID + 1;
            } else {
                this.trigger('change');
            }
            if (!this.sync_check())
                return;
            if (this.sync_update_timeout)
                clearTimeout(this.sync_update_timeout);
            this.sync_update_timeout = setTimeout(
                function(){
                    self.sync_update_timeout = false;
                    self.do_sync_update();
                }, 0);
        },
        sync_remove_order: function(){
            if (!this.sync_check())
                return;
            this.do_sync_remove_order();
        },
        do_sync_remove_order: function(){
            this.pos.sync_session.remove_order({'uid': this.uid, 'revision_ID': this.revision_ID});
        },
        remove_orderline: function(line){
            OrderSuper.prototype.remove_orderline.apply(this, arguments);
            line.order.trigger('change:sync');
        },
        add_product: function(){
            this.trigger('change:sync');
            OrderSuper.prototype.add_product.apply(this, arguments);
        },
        init_from_JSON: function(json) {
            this.new_order = json.new_order;
            this.order_on_server = json.order_on_server;
            OrderSuper.prototype.init_from_JSON.call(this, json);
        },
        export_as_JSON: function(){
            var data = OrderSuper.prototype.export_as_JSON.apply(this, arguments);
            data.sync_info = this.sync_info;
            data.new_order = this.new_order;
            data.revision_ID = this.revision_ID;
            data.order_on_server = this.order_on_server;
            return data;
        },
        do_sync_update: function(){
            var self = this;
            if (this.enquied)
                return;
            var order = function(){
                self.enquied=false;
                var data = self.export_as_JSON();
                return self.pos.sync_session.update(data).done(function(res){
                    self.order_on_server = true;
                    if (res && res.action=="update_revision_ID") {
                        var order_ID = res.order_ID;
                        var server_revision_ID = res.revision_ID;
                        if (order_ID && self.sequence_number != order_ID) {
                            self.sequence_number = order_ID;
                            self.pos.pos_session.order_ID = order_ID;
                            self.trigger('change');
                        }
                        if (server_revision_ID && server_revision_ID > self.revision_ID)
                            self.revision_ID = server_revision_ID;
                    }
                })
            };
            this.enquied = true;
            this.pos.sync_session.enque(order);
        }
    });
    var OrderlineSuper = Models.Orderline;
    Models.Orderline = Models.Orderline.extend({
        initialize: function(){
            var self = this;
            OrderlineSuper.prototype.initialize.apply(this, arguments);
            this.sync_info = {};
            if (!this.order)
                return;
            this.uid = this.order.generate_unique_id() + '-' + this.id;
            if (this.order.screen_data.screen === "splitbill")
                return;
            if (this.order.sync_check())
                this.sync_info.created = this.order.pos.sync_my_info();
            this.bind('change', function(line){
                if (self.order.sync_check() && !line.sync_changing_selected) {
                    line.sync_info.changed = line.order.pos.sync_my_info();
                    line.order.sync_info.changed = line.order.pos.sync_my_info();
                    var order_lines = line.order.orderlines;
                    order_lines.trigger('change', order_lines);
                    line.order.trigger('change:sync');
                }
            });
        },
        export_as_JSON: function(){
            var data = OrderlineSuper.prototype.export_as_JSON.apply(this, arguments);
            data.uid = this.uid;
            data.sync_info = this.sync_info;
            return data;
        },
        set_selected: function(){
            this.sync_changing_selected = true;
            OrderlineSuper.prototype.set_selected.apply(this, arguments);
            this.sync_changing_selected = false;
        }
    });

    Chrome.OrderSelectorWidget.include({
        init: function(parent,options) {
            this._super(parent,options);
            this.pos.get('orders').bind('change:update_new_order', this.renderElement, this);
        },
        destroy: function(){
            this.pos.get('orders').unbind('change:update_new_order', this.renderElement, this);
            this._super();
        },
    });

    exports.MultiSession = Backbone.Model.extend({
        initialize: function(pos){
            var self = this;
            this.pos = pos;
            this.func_queue = [];
            this.order_ID = null;
            this.client_online = true;
            this.update_queue = $.when();
            this.pos.longpolling_connection.on("change:poll_connection", function(status){
                if (status) {
                    if (self.offline_sync_all_timer) {
                        clearInterval(self.offline_sync_all_timer);
                        self.offline_sync_all_timer = false;
                    }
                    self.request_sync_all();
                } else {
                    if (!self.offline_sync_all_timer) {
                        self.no_connection_warning();
                        self.start_offline_sync_timer();
                        if (self.pos.debug)
                            console.log('MultiSession initialize error');
                    }
                }
            });
        },
        update: function(data){
            return this.send({
                action: 'update_order',
                data: data
            });
        },
        remove_order: function(data){
            this.send({
                action: 'remove_order',
                data: data
            });
        },
        request_sync_all: function(){
            var data = {};
            return this.send({
                'action': 'sync_all',
                data: data
            });
        },
        enque: function(func){
            var self = this;
            this.func_queue.push(func);
            this.update_queue = this.update_queue.then(function() {
                if (self.func_queue[0]) {
                    var next = $.Deferred();
                    var func1 = self.func_queue.shift();
                    func1().always(function () { next.resolve() });
                    return next;
                }
            })
        },
        _debug_send_number: 0,
        send: function(message){
            var current_send_number = 0;
            var self = this;
            if (this.pos.debug){
                current_send_number = this._debug_send_number++;
                console.log('TS', this.pos.config.name,
                    'send #' + current_send_number +' :', JSON.stringify(message));
            }
            message.data.pos_id = this.pos.config.id;
            var send_it = function () {
                return Session.rpc("/sync_pos_restaurant_order/update", {
                    message: message,
                    sync_session_id: self.pos.config.sync_session_id[0],
                });
            };
            return send_it().fail(function (error, e) {
                if (self.pos.debug){
                    console.log('TS', self.pos.config.name,
                        'failed request #'+current_send_number+':', error.message);
                }
                if(error.message === 'XmlHttpRequestError ') {
                    self.client_online = false;
                    e.preventDefault();
                    self.pos.longpolling_connection.network_is_off();
                    if (!self.offline_sync_all_timer) {
                        self.no_connection_warning();
                        self.start_offline_sync_timer();
                    }
                } else {
                    self.request_sync_all();
                }
            }).done(function(res){
                var server_orders_uid = [];
                self.client_online = true;
                if (self.pos.debug){
                    console.log('TS', self.pos.config.name,
                        'response #'+current_send_number+':', JSON.stringify(res));
                }
                if (res.action == "revision_error") {
                    var warning_message = _t('There is a conflict during synchronization, try your action again');
                    self.warning(warning_message);
                    self.request_sync_all();
                }
                if (res.action == 'sync_all') {
                    res.orders.forEach(function (item) {
                        self.pos.sync_on_update(item, true);
                        server_orders_uid.push(item.data.uid);
                    });
                    self.pos.pos_session.order_ID = res.order_ID;
                    if (res.order_ID != 0)
                        self.pos.pos_session.sequence_number = res.order_ID;
                    self.destroy_removed_orders(server_orders_uid);
                }
                if (self.offline_sync_all_timer) {
                    clearInterval(self.offline_sync_all_timer);
                    self.offline_sync_all_timer = false;
                }
            });
        },
        start_offline_sync_timer: function(){
            var self = this;
            self.offline_sync_all_timer = setInterval(function(){ self.request_sync_all() }, 5000);
        },
        send_offline_orders: function() {
            var self = this;
            var orders = this.pos.get("orders");
            orders.each(function(item) {
                if (!item.order_on_server && item.get_orderlines().length > 0)
                    item.sync_update();
            });
        },
        warning: function(warning_message){
            this.pos.chrome.gui.show_popup('error',{'title': _t('Warning'), 'body': warning_message});
        },
        destroy_removed_orders: function(server_orders_uid) {
            var self = this;
            var orders = self.pos.get('orders').filter(function(r){
                return (r.order_on_server === true);
            });
            orders.forEach(function(item) {
                var remove_order = server_orders_uid.indexOf(item.uid);
                if (remove_order === -1) {
                    var order = self.pos.get('orders').find(function (order) {
                        return order.uid == item.uid;
                    });
                    order.destroy({'reason': 'abandon'});
                }
            });
            self.send_offline_orders();
        },
        no_connection_warning: function(){
            var warning_message = _t("No connection to the server. You can create new orders only. It is forbidden to modify existing orders.");
            this.warning(warning_message);
        }
    });
    return exports;
});
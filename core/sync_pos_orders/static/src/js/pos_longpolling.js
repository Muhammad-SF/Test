odoo.define('pos_longpolling', function(require){

    var Backbone = window.Backbone;
    var Session = require('web.session');
    var Core = require('web.core');
    var Models = require('point_of_sale.models');
    var Bus = require('bus.bus');
    var Chrome = require('point_of_sale.chrome')
    Bus.bus.activated = true;
    var _t = Core._t;
    var exports = {};

    var PosModelSuper = Models.PosModel;
    Models.PosModel = Models.PosModel.extend({
        initialize: function(){
            var self = this;
            PosModelSuper.prototype.initialize.apply(this, arguments);
            this.channels = {};
            this.lonpolling_activated = false;
            this.bus = Bus.bus;
            this.longpolling_connection = new exports.LongpollingConnection(this);
            var channel_name = "pos.longpolling";
            var callback = this.longpolling_connection.network_is_on;
            this.add_channel(channel_name, callback, this.longpolling_connection);
            this.ready.then(function () {
                self.start_longpolling();
            });
        },
        init_channel: function(channel_name){
            var channel = this.get_full_channel_name(channel_name);
            this.bus.add_channel(channel);
        },
        get_full_channel_name: function(channel_name){
            return JSON.stringify([Session.db,channel_name,String(this.config.id)]);
        },
        add_channel: function(channel_name, callback, thisArg) {
            if (thisArg){
                callback = _.bind(callback, thisArg);
            }
            this.channels[channel_name] = callback;
            if (this.lonpolling_activated) {
                this.init_channel(channel_name);
            }
        },
        remove_channel: function(channel_name) {
            if (channel_name in this.channels) {
                delete this.channels[channel_name];
                this.bus.delete_channel(this.get_full_channel_name(channel_name));
            }
        },
        on_notification: function(notification) {
            for (var i = 0; i < notification.length; i++) {
                this.on_notification_do(notification[i][0], notification[i][1]);
            }
            this.db.save('bus_last', this.bus.last);
        },
        on_notification_do: function (channel, message) {
            var self = this;
            if (_.isString(channel)) {
                var channel = JSON.parse(channel);
            }
            if(Array.isArray(channel) && (channel[1] in self.channels)){
                try{
                    self.longpolling_connection.network_is_on();
                    var callback = self.channels[channel[1]];
                    if (callback) {
                        if (self.debug){
                            console.log('POS LONGPOLLING', self.config.name, channel[1], JSON.stringify(message));
                        }
                        callback(message);
                    }
                }catch(error){
                    this.chrome.gui.show_popup('error',{
                        'body': error,
                        'title': _t('Error'),
                    });
                }
            }
        },
        start_longpolling: function(){
            var self = this;
            this.bus.last = this.db.load('bus_last', 0);
            this.bus.on("notification", this, this.on_notification);
            this.bus.stop_polling();
            _.each(self.channels, function(value, key){
                self.init_channel(key);
            });
            this.bus.start_polling();
            this.lonpolling_activated = true;
            this.longpolling_connection.send();
        },
    });
    exports.LongpollingConnection = Backbone.Model.extend({
        initialize: function(pos) {
            this.pos = pos;
            this.status = false;
            this.timer = false;
            this.response_status = false;
        },
        set_status: function(status) {
            if (this.status == status) {
                return;
            }
            this.status = status;
            this.trigger("change:poll_connection", status);
        },
        network_is_on: function(message) {
            if (message) {
                this.response_status = true;
            }
            this.update_timer();
            this.set_status(true);
        },
        network_is_off: function() {
            this.update_timer();
            this.set_status(false);
        },
        send: function() {
            var self = this;
            this.response_status = false;
            Session.rpc("/pos_longpolling/update", {message: "PING", pos_id: self.pos.config.id}).then(function(){
                if (!self.response_status) {
                    self.response_timer();
                }
            }, function(error, e){
                e.preventDefault();
                if (self.pos.debug){
                    console.log('POS LONGPOLLING send error', self.pos.config.name);
                }
                self.network_is_off();
            });
        },
        start_timer: function(time, type){
            var time = Math.round(time * 3600.0);
            var self = this;
            this.timer = setTimeout(function() {
                if (type == "query") {
                    self.send();
                } else if (type == "response") {
                    if (self.pos.debug){
                        console.log('POS LONGPOLLING start_timer error', self.pos.config.name);
                    }
                    self.network_is_off();
                }
            }, time * 1000);
        },
        stop_timer: function(){
            var self = this;
            if (this.timer) {
                clearTimeout(this.timer);
                this.timer = false;
            }
        },
        update_timer: function(){
            this.stop_timer();
            this.start_timer(this.pos.config.query_timeout, 'query');
        },
        response_timer: function() {
            this.stop_timer();
            this.start_timer(this.pos.config.response_timeout, "response");
        },
    });
    Chrome.StatusWidget.include({
        connection_status_set: function(status) {
            var element = this.$('.poll_connection_status');
            element.removeClass(status ? 'oe_red' : 'oe_green');
            element.addClass(status ? 'oe_green' : 'oe_red');
        }
    });
    Chrome.SynchNotificationWidget.include({
        start: function(){
            var self = this;
            this._super();
            this.pos.longpolling_connection.on("change:poll_connection", function(status){
                self.connection_status_set(status);
            });
        },
    });
    return exports;
});
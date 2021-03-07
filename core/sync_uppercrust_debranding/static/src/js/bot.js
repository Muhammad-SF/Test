odoo.define('sync_uppercrust_debranding.Bot', function (require) {
    "use strict";

    var chat_manager = require('mail.chat_manager');
    var session = require('web.session');
    var WebClient = require('web.WebClient');
    var Model = require('web.Model');

    WebClient.include({
        show_application: function () {
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(function () {
                new Model("ir.config_parameter")
                .call("get_param", ['sync_app_system_name'])
                .then(function (system_name) {
                    session.system_name = system_name;
                });
            });
        },
    });

    var make_message_super = chat_manager.make_message;
    chat_manager.make_message = function (data) {
        var message = make_message_super(data);
        if (message.author_id === 'ODOOBOT') {
            message.avatar_src = '/web/binary/company_logo?company_id=' + session.company_id;
            message.displayed_author = session.system_name + ' Bot';
        }
        return message;
    };
});
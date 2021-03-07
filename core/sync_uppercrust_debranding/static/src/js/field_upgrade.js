odoo.define('sync_uppercrust_debranding.form_upgrade_widgets', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var session = require('web.session');
var form_widgets = require('web.form_widgets');
var framework = require('web.framework');
var Model = require('web.DataModel');

var _t = core._t;
var QWeb = core.qweb;

/**
 *  This widget is intended to be used in config settings.
 *  When checked, an upgrade popup is showed to the user.
 */
var AbstractFieldUpgrade = {
    events: {
        'click input': 'on_click_input',
    },

    start: function() {
        this._super.apply(this, arguments);
        this.get_enterprise_label().after($("<span>", {
            'class': "label label-primary oe_inline"
        }));

        new Model("ir.config_parameter").call("get_param", ['sync_app_system_name']).then(function (system_name) {
            session.system_name = system_name;
        });

        new Model("ir.config_parameter").call("get_param", ['sync_app_support_url']).then(function (support_url) {
            session.support_url = support_url;
        });
    },

    open_dialog: function() {

        var buttons = [
            {
                text: _t("Cancel"),
                close: true,
            },
        ];

        return new Dialog(this, {
            size: 'medium',
            buttons: buttons,
            $content: $('<div>', {
                html: '<h3>Kindly contact us for this feature!! <span><a href="' + session.support_url + '" target="_blank">Click Here For More Info</a></h3>',
            }),
            title: _t(session.system_name),
        }).open();
    },

    confirm_upgrade: function() {
        new Model("ir.config_parameter").call("get_param", [[["share", "=", false]]]).then(function(data) {
            framework.redirect("https://www.odoo.com/odoo-enterprise/upgrade?num_users=" + data);
        });
    },

    get_enterprise_label: function() {},
    on_click_input: function() {},
};

var UpgradeBoolean = form_widgets.FieldBoolean.extend(AbstractFieldUpgrade, {
    template: "FieldUpgradeBoolean",

    get_enterprise_label: function() {
        return this.$label;
    },

    on_click_input: function() {
        if(this.$checkbox.prop("checked")) {
            this.open_dialog().on('closed', this, function() {
                this.$checkbox.prop("checked", false);
            });
        }
    },
});

var UpgradeRadio = form_widgets.FieldRadio.extend(AbstractFieldUpgrade, {
    get_enterprise_label: function() {
        // override the margin:0px
        this.$('label').addClass('mr4');
        return this.$('label').last();
    },
    on_click_input: function(event) {
        if($(event.target).val() === "1") {
            this.open_dialog().on('closed', this, function() {
                this.$('input').first().prop("checked", true);
            });
        }
    },
});

core.form_widget_registry
    .add('upgrade_boolean', UpgradeBoolean)
    .add('upgrade_radio', UpgradeRadio);

});
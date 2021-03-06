odoo.define('sync_uppercrust_debranding.title', function(require) {
"use strict";

var core = require('web.core');
var ajax = require('web.ajax');
var Dialog = require('web.Dialog');
var CrashManager = require('web.CrashManager'); // We can import crash_manager also
var mixins = require('web.mixins');
var session = require('web.session');

var QWeb = core.qweb;
var _t = core._t;
var _lt = core._lt;


var map_title ={
    user_error: _lt('Warning'),
    warning: _lt('Warning'),
    access_error: _lt('Access Error'),
    missing_error: _lt('Missing Record'),
    validation_error: _lt('Validation Error'),
    except_orm: _lt('Global Business Error'),
    access_denied: _lt('Access Denied'),
};

CrashManager.include({
    rpc_error: function(error) {
        var self = this;
        if (!this.active) {
            return;
        }
        if (this.connection_lost) {
            return;
        }
        if (error.code === -32098) {
            core.bus.trigger('connection_lost');
            this.connection_lost = true;
            var timeinterval = setInterval(function() {
                ajax.jsonRpc('/web/webclient/version_info').then(function() {
                    clearInterval(timeinterval);
                    core.bus.trigger('connection_restored');
                    self.connection_lost = false;
                });
            }, 2000);
            return;
        }
        var handler = core.crash_registry.get(error.data.name, true);
        if (handler) {
            new (handler)(this, error).display();
            return;
        }
        if (error.data.name === "odoo.http.SessionExpiredException" || error.data.name === "werkzeug.exceptions.Forbidden") {
            this.show_warning({type: _t("Session Expired"), data: {message: _t("Your session expired. Please refresh the current web page.")}});
            return;
        }
        if (_.has(map_title, error.data.exception_type)) {
            if(error.data.exception_type === 'except_orm'){
                if(error.data.arguments[1]) {
                    error = _.extend({}, error,
                                {
                                    data: _.extend({}, error.data,
                                        {
                                            message: error.data.arguments[1],
                                            title: error.data.arguments[0] !== 'Warning' ? (" - " + error.data.arguments[0]) : '',
                                        })
                                });
                }
                else {
                    error = _.extend({}, error,
                                {
                                    data: _.extend({}, error.data,
                                        {
                                            message: error.data.arguments[0],
                                            title:  '',
                                        })
                                });
                }
            }
            else {
                error = _.extend({}, error,
                            {
                                data: _.extend({}, error.data,
                                    {
                                        message: error.data.arguments[0],
                                        title: map_title[error.data.exception_type] !== 'Warning' ? (" - " + map_title[error.data.exception_type]) : '',
                                    })
                            });
            }

            this.show_warning(error);
        //InternalError

        } else {
            this.show_error(error);
        }
    },
    show_warning: function(error) {
        if (!this.active) {
            return;
        }
        // Error message contains odoo title. Replace it
        error.message = error.message && error.message.replace("Odoo", "")
        new Dialog(this, {
            size: 'medium',
            title: _.str.capitalize(error.type || error.message) || _t("Warning"),
            subtitle: error.data.title,
            $content: $(QWeb.render('CrashManager.warning', {error: error}))
        }).open();
    },
    show_error: function(error) {
        if (!this.active) {
            return;
        }
        error.message = error.message && error.message.replace("Odoo", "")
        new Dialog(this, {
            title: _.str.capitalize(error.type || error.message) || _t("Warning"),
            $content: QWeb.render('CrashManager.error', {error: error})
        }).open();
    },
    show_message: function(exception) {
        this.show_error({
            type: _t("Client Error"),
            message: exception,
            data: {debug: ""}
        });
    },
});
Dialog.include({
    init: function (parent, options) {
        this._super(parent);
        this._opened = $.Deferred();

        options = _.defaults(options || {}, {
            title: _t(''), subtitle: '',
            size: 'large',
            dialogClass: '',
            $content: false,
            buttons: [{text: _t("Ok"), close: true}]
        });

        this.$content = options.$content;

        this.title = options.title;
        this.subtitle = options.subtitle;
        this.$modal = $(QWeb.render('Dialog', {title: this.title, subtitle: this.subtitle}));

        switch(options.size) {
            case 'large':
                this.$modal.find('.modal-dialog').addClass('modal-lg');
                break;
            case 'small':
                this.$modal.find('.modal-dialog').addClass('modal-sm');
                break;
        }

        this.dialogClass = options.dialogClass;
        this.$footer = this.$modal.find(".modal-footer");

        this.set_buttons(options.buttons);

        this.$modal.on('hidden.bs.modal', _.bind(this.destroy, this));
    },
});
});
// Notification view chnage
odoo.define('sync_uppercrust_debranding.native_notifications', function (require) {
    "use strict";

    var session = require('web.session');
    var core = require('web.core');
    var utils = require('mail.utils');
    var bus = require('bus.bus').bus;

    var _t = core._t;

    var _native_notification = function (title, content) {
        var notification = new Notification(title, {
            body: content,
            icon: '/web/binary/company_logo?company_id=' + session.company_id
        });
        notification.onclick = function () {
            window.focus();
            if (this.cancel) {
                this.cancel();
            } else if (this.close) {
                this.close();
            }
        };
    };

    var notification_super = utils.send_notification;
    utils.send_notification = function (widget, title, content) {
        if (title === 'Permission granted' || title === 'Permission denied') {
            content = content.replace(/Odoo/ig, '');
        }
        if (Notification && Notification.permission === "granted") {
            if (bus.is_master) {
                _native_notification(title, content);
            }
        } else {
            notification_super(widget, title, content);
        }
    };

});

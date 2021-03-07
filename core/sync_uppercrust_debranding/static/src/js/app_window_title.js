odoo.define('sync_uppercrust_debranding.sync_app_system_name', function (require) {
"use strict";

var WebClient = require('web.WebClient');
    WebClient.include({
        init: function() {
            this._super.apply(this, arguments);
            this.set('title_part', {"zopenerp": document.title});
        }
    });
});
odoo.define('transfer_activity_log.add_export_button', function (require) {
"use strict";
var core = require('web.core');
var ListView = require('web.ListView');
var QWeb = core.qweb;


ListView.include({       

        render_buttons: function($node) {
                var self = this;
                this._super($node);
                    this.$buttons.on('click', '.oe_add_export_button', this.proxy('execute_export_action'));
        },

        execute_export_action: function () {         
        		var dataset = this.dataset;  
 				this.do_action({
                type: "ir.actions.act_window",
                name: "Activity Log Report",
                res_model: "transfer.activity.log.wiz",
                views: [[false,'form']],
                target: 'new',
                view_type : 'form',
                view_mode : 'form',
                context: {'active_model': 'transfer.activity.log', 'default_picking_name': dataset.domain[0][2]}
        		});
         } 

});

});
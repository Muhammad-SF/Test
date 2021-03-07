odoo.define('point_of_sale.pos_session', function (require) {
"use strict";
var chrome = require('point_of_sale.chrome');
var core = require('web.core');
var window_manager = require('mail.window_manager');
var ajax = require('web.ajax');
var gui = require('point_of_sale.gui');
var popup = require('point_of_sale.popups');
var PosBaseWidget = require('point_of_sale.BaseWidget');
var Model = require('web.Model');
var ActionManager = require('web.ActionManager');


var QWeb = core.qweb;
var _t = core._t;


chrome.Chrome.include({

    build_chrome: function() {
            var self = this 
            this._super();
            if(!this.pos.config.iface_session_report){
                $('.session_report').hide()
            }
            this.$('.session_report').click(function(){
                self.on_click_pos_pos_message();
            });

        },
    
    on_click_pos_pos_message: function () {
        console.log("vvv0vv0v0v0vv0v0v0v0v0vv0",this.pos)
                var self = this;
        var pos_session_id = self.pos.pos_session.id;
        this.gui.show_popup('password',{
                'title': _t('Password ?'),
                confirm: function(pw) {
                    var done = new $.Deferred();
                    var res_user = new Model('res.users');
                    res_user.call("check_session_security_pin_number", [pw]).then(function (value) {
                        //alert(value);
                       
                        if(value == true){
                            
                          var print = {
                                'context': {'active_id': [pos_session_id],
                                'active_ids':[pos_session_id]},
                                'report_file': 'techno_pos_session_report.report_pos_session_pdf',
                                'report_name': 'techno_pos_session_report.report_pos_session_pdf',
                                'report_type': "qweb-pdf",
                                'type': "ir.actions.report.xml",
                            };
                        var options = {};
                        var action_manager = new ActionManager();
                        action_manager.ir_actions_report_xml(print);
                           
                        } 

                        else{
                            alert('Incorrect Pin Number');
                        }
                    });
                   
                },
            });
    },

   

});




});

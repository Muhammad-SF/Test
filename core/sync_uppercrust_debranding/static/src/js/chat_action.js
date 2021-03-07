odoo.define('sync_uppercrust_debranding.chat_client_action', function (require) {
"use strict";
	var core = require('web.core');
	var utils = require('mail.utils');
	var web_client = require('web.web_client');
	var ChatAction = core.action_registry.get('mail.chat.instant_messaging');
	
	ChatAction.include({
		 events: _.extend({}, ChatAction.prototype.events, {
			"click .ad_mail_request_permission": function (event) {
			    event.preventDefault();
			    var self = this;
			    this.$(".o_mail_annoying_notification_bar").slideUp();
			    var def = window.Notification && window.Notification.requestPermission();
			    if (def) {
			        def.then(function (value) {
			            if (value === 'granted') {
			                utils.send_notification(_t('Permission granted'), _t('has now the permission to send you native notifications on this device.'));
			            } else {
			                utils.send_notification(_t('Permission denied'), _t('will not have the permission to send native notifications on this device.'));
			            }
			        });
			    }
			},
		})
	});
});
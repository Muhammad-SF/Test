odoo.define('task_list_manager.Chatter', function (require) {
"use strict";

var chat_manager = require('mail.chat_manager');
var composer = require('mail.composer');
var ChatThread = require('mail.ChatThread');
var utils = require('mail.utils');

var config = require('web.config');
var core = require('web.core');
var form_common = require('web.form_common');
var framework = require('web.framework');
var pyeval = require('web.pyeval');
var web_utils = require('web.utils');
var session = require('web.session');
var chatter = require('mail.Chatter');
var thread = require('mail.ChatThread');
console.log("=====chatter==================",chatter)
var _t = core._t;
var QWeb = core.qweb;
var time = require('web.time');
var core = require('web.core');
var time = require('web.time');
var utils = require('mail.utils');
var Model = require('web.Model')
var QWeb = core.qweb;
var _t = core._t;
var setDelayLabel = function(activities){
    var today = moment().startOf('day');
    _.each(activities, function(activity){
        var to_display = '';
        var diff = activity.date_deadline.diff(today, 'days', true); // true means no rounding
        if(diff === 0){
            to_display = _t('Today');
        }else{
            if(diff < 0){ // overdue
                if(diff === -1){
                    to_display = _t('Yesterday');
                }else{
                    to_display = _.str.sprintf(_t('%d days overdue'), Math.abs(diff));
                }
            }else{ // due
                if(diff === 1){
                    to_display = _t('Tomorrow');
                }else{
                    to_display = _.str.sprintf(_t('Due in %d days'), Math.abs(diff));
                }
            }
        }
        activity.label_delay = to_display;
    });
    return activities;
};

//// -----------------------------------------------------------------------------
//// Document Chatter ('mail_thread' widget)
////
//// Since it is displayed on a form view, it extends 'AbstractField' widget.
//// -----------------------------------------------------------------------------

thread.include({
	render: function (messages, options) {
        var self = this;
		console.log("=========",this)
        var msgs = _.map(messages, this._preprocess_message.bind(this));
        if (this.options.display_order === thread.ORDER.DESC) {
            msgs.reverse();
        }
        options = _.extend({}, this.options, options);

        // Hide avatar and info of a message if that message and the previous
        // one are both comments wrote by the same author at the same minute
        // and in the same document (users can now post message in documents
        // directly from a channel that follows it)
        var prev_msg;
        _.each(msgs, function (msg) {
            if (!prev_msg || (Math.abs(msg.date.diff(prev_msg.date)) > 60000) ||
                prev_msg.message_type !== 'comment' || msg.message_type !== 'comment' ||
                (prev_msg.author_id[0] !== msg.author_id[0]) || prev_msg.model !== msg.model ||
                prev_msg.res_id !== msg.res_id) {
                msg.display_author = true;
            } else {
                msg.display_author = !options.squash_close_messages;
            }
            prev_msg = msg;
        });

        this.$el.html(QWeb.render('mail.ChatThread', {
            messages: msgs,
            options: options,
            ORDER: thread.ORDER,
        }));

        _.each(msgs, function(msg) {
            var $msg = self.$('.o_thread_message[data-message-id="'+ msg.id +'"]');
            $msg.find('.o_mail_timestamp').data('date', msg.date);

            self.insert_read_more($msg);
        });

        if (!this.update_timestamps_interval) {
            this.update_timestamps_interval = setInterval(function() {
                self.update_timestamps();
            }, 1000*60);
        }
        var parent = self.getParent();
        new Model("mail.activity").call("search_read", [[['res_model', '=', parent.model],['res_id', '=', parent.res_id]]]).then(function(results){
        	console.log('results   '+results.length)
        	_.each(results, function (activity) {
                activity.create_date = moment(time.auto_str_to_date(activity.create_date));
                activity.date_deadline = moment(time.auto_str_to_date(activity.date_deadline));
            });
            // sort activities by due date
        		results = _.sortBy(results, 'date_deadline');
            var activities = setDelayLabel(results);
            if (activities.length) {
                var nbActivities = _.countBy(activities, 'state');
                self.$el.find('.o_thread_date_separator:first').prepend(QWeb.render('task_list_manager.activity_items', {
                    activities: activities,
                    nbPlannedActivities: nbActivities.planned,
                    nbTodayActivities: nbActivities.today,
                    nbOverdueActivities: nbActivities.overdue,
//                    date_format: time.getLangDatetimeFormat(),
                }));
            }
        });
        
    },

})
chatter.include({
//    template: 'mail.Chatter',
	
    events: {
        "click .o_chatter_button_new_message": "on_open_composer_new_message",
        "click .o_chatter_button_log_note": "on_open_composer_log_note",
        "click .o_chatter_button_schedule_activity": '_onScheduleActivity',
        'click .o_activity_edit': '_onEditActivity',
        'click .o_activity_unlink': '_onUnlinkActivity',
        'click .o_activity_done': '_onMarkActivityDone',
    },
    init: function (parent, record, mailFields, options) {
    
        this._super.apply(this, arguments);
        this.model = this.view.dataset.model;
        this.res_id = undefined;
        this.context = this.options.context || {};
        this.dp = new web_utils.DropPrevious();
        this.activities = [];
    },
    _onScheduleActivity: function () {
    	console.log("=================this.model==========",this)
    	var self = this
        var action = {
                type: 'ir.actions.act_window',
                res_model: 'mail.activity',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
                context: {
                    default_res_id: this.res_id,
                    default_res_model: this.model,
                    default_res_model_id: false,
//                    default_previous_activity_type_id: previous_activity_type_id,
                },
                res_id:  false,
            };
            return this.do_action(action, {
                on_close: function() {
                    self.trigger('need_refresh');
                	self.render_value()
                },
            });
    },
    _onEditActivity: function (event, options) {
//        console.
//    	event.preventDefault();
        var self = this;
        var activity_id = $(event.currentTarget).data('activity-id');
        var action = _.defaults(options || {}, {
            type: 'ir.actions.act_window',
            res_model: 'mail.activity',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_res_id: this.res_id,
                default_res_model: this.model,
            },
            res_id: activity_id,
        });
        return this.do_action(action, {
            on_close: function () {
                // remove the edited activity from the array of fetched activities to
                // force a reload of that activity
                self.activities = _.reject(self.activities, {id: activity_id});
                self.render_value()
            },
        });
    },
    _onUnlinkActivity: function (event, options) {
        event.preventDefault();
        var self=this;
        var activity_id = $(event.currentTarget).data('activity-id');
        options = _.defaults(options || {}, {
            model: 'mail.activity',
            args: [[activity_id]],
        });
        return new Model("mail.activity").call("unlink",[[activity_id]]).then(function()
        		{
        		self.render_value();
		});
        },

    on_open_composer_log_note: function () {
        this.open_composer({is_log: true});
    },
    _markActivityDone: function (id, feedback) {
    	var self = this;
        return new Model("mail.activity").call("action_feedback",[[id]],{feedback: feedback}).then(function (result){
        	if (result){
        		self.msg_ids.push(result)
        	}
        });
    },

//    _markActivityReload: function (id, feedback) {
//        return new Model("mail.activity").call("page_reload",[[id]],{});
//    },

    _onMarkActivityDone: function (event) {
        event.preventDefault();
        var self = this;
        var $popover_el = $(event.currentTarget);
        var activity_id = $popover_el.data('activity-id');
//        var previous_activity_type_id = $popover_el.data('previous-activity-type-id');
        if (!$popover_el.data('bs.popover')) {
            $popover_el.popover({
                title : _t('Feedback'),
                html: 'true',
                trigger:'click',
                content : function() {
                    var $popover = $(QWeb.render("task_list_manager.activity_feedback_form", {}));
                    $popover.on('click', '.o_activity_popover_done_next', function () {
                        var feedback = _.escape($popover.find('#activity_feedback').val());
//                        var previous_activity_type_id = $popover_el.data('previous-activity-type-id');
                        self._markActivityDone(activity_id, feedback)
                            .then(self._onScheduleActivity());
//                        self._markActivityReload();
//                        this.$input = this.$('.o_composer_input textarea');
//                        this.$input.focus(function () {
                        
//                        });
//                        self.$input.focus();
//                        self.trigger('need_refresh');
//                     	self.render_value()

                        self.render_value();
                    });
                    $popover.on('click', '.o_activity_popover_done', function () {
                        var feedback = _.escape($popover.find('#activity_feedback').val());
                        console.log("======self._markActivityDone(activity_id, feedback)===========",activity_id,feedback)
                        self._markActivityDone(activity_id, feedback)
                            .then(function(){
                            	self.fetch_and_render_thread(self.msg_ids);
                            });
                    });
                    $popover.on('click', '.o_activity_popover_discard', function () {
                        $popover_el.popover('hide');
                    });
                    return $popover;
                },
            }).on("show.bs.popover", function (e) {
                var $popover = $(this).data("bs.popover").tip();
                $popover.addClass('o_mail_activity_feedback').attr('tabindex', 0);
                $(".o_mail_activity_feedback.popover").not(e.target).popover("hide");
            }).on("shown.bs.popover", function () {
                var $popover = $(this).data("bs.popover").tip();
                $popover.find('#activity_feedback').focus();
                $popover.off('focusout');
                $popover.focusout(function (e) {
                    // outside click of popover hide the popover
                    // e.relatedTarget is the element receiving the focus
                    if(!$popover.is(e.relatedTarget) && !$popover.find(e.relatedTarget).length) {
                        $popover.popover('hide');
                    }
                });
            }).popover('show');
        }
    },

});
//
//    willStart: function () {
//        return chat_manager.is_ready;
//    },
//
//    start: function () {
//        var self = this;
//
//        // Hide the chatter in 'create' mode
//        this.view.on("change:actual_mode", this, this.check_visibility);
//        this.check_visibility();
//        var $container = this.$el.parent();
//        if ($container.hasClass('oe_chatter')) {
//            this.$el
//                .addClass($container.attr("class"))
//                .unwrap();
//        }
//
//        // Move the follower's widget (if any) inside the chatter
//        this.followers = this.field_manager.fields.message_follower_ids;
//        if (this.followers) {
//            this.$('.o_chatter_topbar').append(this.followers.$el);
//            this.followers.on('redirect', chat_manager, chat_manager.redirect);
//            this.followers.on('followers_update', this, this.on_followers_update);
//        }
//
//        this.thread = new ChatThread(this, {
//            display_order: ChatThread.ORDER.DESC,
//            display_document_link: false,
//            display_needactions: false,
//            squash_close_messages: false,
//        });
//        this.thread.on('load_more_messages', this, this.load_more_messages);
//        this.thread.on('toggle_star_status', this, function (message_id) {
//            chat_manager.toggle_star_status(message_id);
//        });
//        this.thread.on('redirect', chat_manager, chat_manager.redirect);
//        this.thread.on('redirect_to_channel', this, this.on_channel_redirect);
//
//        this.ready = $.Deferred();
//
//        var def1 = this._super.apply(this, arguments);
//        var def2 = this.thread.appendTo(this.$el);
//
//        return $.when(def1, def2).then(function () {
//            chat_manager.bus.on('new_message', self, self.on_new_message);
//            chat_manager.bus.on('update_message', self, self.on_update_message);
//            self.ready.resolve();
//        });
//    },
//
//    check_visibility: function () {
//        this.set({"force_invisible": this.view.get("actual_mode") === "create"});
//    },
//
//    fetch_and_render_thread: function (ids, options) {
//        var self = this;
//        options = options || {};
//        options.ids = ids;
//
//        // Ensure that only the last loaded thread is rendered to prevent displaying the wrong thread
//        var fetch_def = this.dp.add(chat_manager.get_messages(options));
//
//        // Empty thread and display a spinner after 1s to indicate that it is loading
//        this.thread.$el.empty();
//        web_utils.reject_after(web_utils.delay(1000), fetch_def).then(function () {
//            self.thread.$el.append(QWeb.render('Spinner'));
//        });
//
//        return fetch_def.then(function (raw_messages) {
//            self.thread.render(raw_messages, {display_load_more: raw_messages.length < ids.length});
//        });
//    },
//
//    on_post_message: function (message) {
//        var self = this;
//        var options = {model: this.model, res_id: this.res_id};
//        chat_manager
//            .post_message(message, options)
//            .then(function () {
//                self.close_composer();
//                if (message.partner_ids.length) {
//                    self.refresh_followers(); // refresh followers' list
//                }
//            })
//            .fail(function () {
//                // todo: display notification
//            });
//    },
//
//    /**
//     * When a message is correctly posted, fetch its data to render it
//     * @param {Number} message_id : the identifier of the new posted message
//     * @returns {Deferred}
//     */
//    on_new_message: function (message) {
//        if (message.model === this.model && message.res_id === this.res_id) {
//            this.msg_ids.unshift(message.id);
//            this.fetch_and_render_thread(this.msg_ids);
//        }
//    },
//
//    on_update_message: function (message) {
//        if (message.model === this.model && message.res_id === this.res_id) {
//            this.fetch_and_render_thread(this.msg_ids);
//        }
//    },
//
//    on_channel_redirect: function (channel_id) {
//        var self = this;
//        var def = chat_manager.join_channel(channel_id);
//        $.when(def).then(function () {
//            // Execute Discuss client action with 'channel' as default channel
//            self.do_action('mail.mail_channel_action_client_chat', {active_id: channel_id});
//        });
//    },
//
//    on_followers_update: function (followers) {
//        this.mention_suggestions = [];
//        var self = this;
//        var prefetched_partners = chat_manager.get_mention_partner_suggestions();
//        var follower_suggestions = [];
//        _.each(followers, function (follower) {
//            if (follower.res_model === 'res.partner') {
//                follower_suggestions.push({
//                    id: follower.res_id,
//                    name: follower.name,
//                    email: follower.email,
//                });
//            }
//        });
//        if (follower_suggestions.length) {
//            this.mention_suggestions.push(follower_suggestions);
//        }
//        _.each(prefetched_partners, function (partners) {
//            self.mention_suggestions.push(_.filter(partners, function (partner) {
//                return !_.findWhere(follower_suggestions, { id: partner.id });
//            }));
//        });
//    },
//
//    load_more_messages: function () {
//        var self = this;
//        var top_msg_id = this.$('.o_thread_message').first().data('messageId');
//        var top_msg_selector = '.o_thread_message[data-message-id="' + top_msg_id + '"]';
//        var offset = -framework.getPosition(document.querySelector(top_msg_selector)).top;
//        this.fetch_and_render_thread(this.msg_ids, {force_fetch: true}).then(function(){
//            offset += framework.getPosition(document.querySelector(top_msg_selector)).top;
//            self.thread.scroll_to({offset: offset});
//        });
//    },
//
//    /**
//     * The value of the field has change (modification or switch to next document). Form view is
//     * not re-rendered, simply updated. A re-fetch is needed.
//     * @override
//     */
//    render_value: function () {
//        return this.ready.then(this._render_value.bind(this));
//    },
//
//    _render_value: function () {
//        // update context
//        var context = _.extend(this.options.context || {},
//            pyeval.eval('contexts', this.build_context())
//        );
//        this.context = _.extend({
//            default_res_id: this.view.datarecord.id || false,
//            default_model: this.view.model || false,
//        }, context);
//        this.thread_dataset = this.view.dataset;
//        this.res_id = this.view.datarecord.id;
//        this.record_name = this.view.datarecord.display_name;
//        this.msg_ids = this.get_value() || [];
//
//        // destroy current composer, if any
//        if (this.composer) {
//            this.composer.destroy();
//            this.composer = undefined;
//            this.mute_new_message_button(false);
//        }
//
//        // fetch and render messages of current document
//        return this.fetch_and_render_thread(this.msg_ids);
//    },
//    refresh_followers: function () {
//        if (this.followers) {
//            this.followers.read_value();
//        }
//    },
//    // composer toggle
//    on_open_composer_new_message: function () {
//        this.open_composer();
//    },
//    on_open_composer_log_note: function () {
//        this.open_composer({is_log: true});
//    },
//    open_composer: function (options) {
//        var self = this;
//        var old_composer = this.composer;
//        // create the new composer
//        this.composer = new ChatterComposer(this, this.thread_dataset, {
//            commands_enabled: false,
//            context: this.context,
//            input_min_height: 50,
//            input_max_height: Number.MAX_VALUE, // no max_height limit for the chatter
//            input_baseline: 14,
//            is_log: options && options.is_log,
//            record_name: this.record_name,
//            default_body: old_composer && old_composer.$input && old_composer.$input.val(),
//            default_mention_selections: old_composer && old_composer.mention_get_listener_selections(),
//        });
//        this.composer.on('input_focused', this, function () {
//            this.composer.mention_set_prefetched_partners(this.mention_suggestions || []);
//        });
//        this.composer.insertBefore(this.$('.o_mail_thread')).then(function () {
//            // destroy existing composer
//            if (old_composer) {
//                old_composer.destroy();
//            }
//            if (!config.device.touch) {
//                self.composer.focus();
//            }
//            self.composer.on('post_message', self, self.on_post_message);
//            self.composer.on('need_refresh', self, self.refresh_followers);
//            self.composer.on('close_composer', null, self.close_composer.bind(self, true));
//        });
//        this.mute_new_message_button(true);
//    },
//    close_composer: function (force) {
//        if (this.composer && (this.composer.is_empty() || force)) {
//            this.composer.do_hide();
//            this.composer.$input.val('');
//            this.mute_new_message_button(false);
//        }
//    },
//    mute_new_message_button: function (mute) {
//        if (mute) {
//            this.$('.o_chatter_button_new_message').removeClass('btn-primary').addClass('btn-default');
//        } else if (!mute) {
//            this.$('.o_chatter_button_new_message').removeClass('btn-default').addClass('btn-primary');
//        }
//    },
//
//    destroy: function () {
//        chat_manager.remove_chatter_messages(this.model);
//        this._super.apply(this, arguments);
//    },
//
//});
//
//core.form_widget_registry.add('mail_thread', Chatter);

//return Chatter;
    
});

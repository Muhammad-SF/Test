odoo.define('calendar.inherit', function (require) {
    "use strict";

var bus = require('bus.bus').bus;
var core = require('web.core');
var CalendarView = require('web_calendar.CalendarView');
var data = require('web.data');
var Dialog = require('web.Dialog');
var form_common = require('web.form_common');
var Model = require('web.DataModel');
var Notification = require('web.notification').Notification;
var session = require('web.session');
var WebClient = require('web.WebClient');
var widgets = require('web_calendar.widgets');

var FieldMany2ManyTags = core.form_widget_registry.get('many2many_tags');
var _t = core._t;
var _lt = core._lt;
var QWeb = core.qweb;

CalendarView.include({
	 open_quick_create : function() {
		 if (this.model !== 'employee.working.schedule.calendar') {
			 this._super();
		 }
	 }
 });

widgets.SidebarFilter.include({
     template: 'CalendarView.sidebar.filters.inherit',
    events: _.extend(widgets.SidebarFilter.prototype.events, {
        'click .check_all': 'on_check_all'
    }),
    render: function() {
        var self = this;
        var filters = _.filter(this.view.get_all_filters_ordered(), function(filter) {
            return _.contains(self.view.now_filter_ids, filter.value);
        });

        if (!self.check_all_click ){
            for (var key in  filters) {
                if (filters.hasOwnProperty(key)) {
                    if (filters[key].value){
                        filters[key].is_checked = false;
                    }
                    else {
                        filters[key].is_checked = true;
                    }
                }
            }
        }

        this.$('.o_calendar_contacts').html(QWeb.render('CalendarView.sidebar.contacts', { filters: filters }));
    },
    on_click: function(e) {
        this.check_all_click = true;
        if (e.target.tagName !== 'INPUT') {
            $(e.currentTarget).find('input').click();
            return;
        }
        this.view.all_filters[e.target.value].is_checked = e.target.checked;
        this.trigger_up('reload_events');
    },
    on_check_all: function(e) {
        this.check_all_click = true;
        if (e.target.tagName !== 'INPUT') {
            $(e.currentTarget).find('input').click();
            return;
        }
        if ($('.check_all>input').prop('checked') == true){
            $('.o_calendar_contact>div>input').prop('checked', true);
            for (var key in  this.view.all_filters) {
                if (this.view.all_filters.hasOwnProperty(key)) {
                    this.view.all_filters[key].is_checked = true;
                }
            }
        }
        else {
            $('.o_calendar_contact>div>input').prop('checked', false);
            for (var key in  this.view.all_filters) {
                if (this.view.all_filters.hasOwnProperty(key)) {
                    if (this.view.all_filters[key].value){
                        this.view.all_filters[key].is_checked = false;
                    }
                    else {
                        this.view.all_filters[key].is_checked = true;
                    }
                }
            }
        }
        this.trigger_up('reload_events');
    },
});
});
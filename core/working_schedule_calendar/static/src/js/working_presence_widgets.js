odoo.define('working_schedule_calendar.working_presence_widgets', function (require) {
"use strict";

var core = require('web.core');
var form_common = require('web.form_common');
// var kanban_widgets = require('web_kanban.widgets');
// var calendar_widgets = require('web_calendar.widgets');

var QWeb = core.qweb;
var _t = core._t;

var FormIndicator = form_common.AbstractField.extend({
    init: function() {
        this._super.apply(this, arguments);
    },
    start: function() {
        this.display_field();
        // this.render_value();  -> gets called automatically in form_common.AbstractField
        // this.$el.tooltip({title: _t("employee presence<br/>green: checked in<br/>red: checked out"), trigger: 'hover'});
        return this._super();
    },
    render_value: function() {
        this.$('.oe_working_schedule_calendar_status').toggleClass("oe_working_schedule_calendar_status_green", this.get_value() == 'checked_in');
        this.$('.oe_working_schedule_calendar_status').toggleClass("oe_working_schedule_calendar_status_grey", this.get_value() == 'not_checked_in');
    },
    display_field: function() {
        this.$el.html(QWeb.render("Indicator"));
    },
});

// var CalendarIndicator = calendar_widgets.AbstractField.extend({
//     init: function() {
//         this._super.apply(this, arguments);
//     },
//     start: function() {
//         this.display_field();
//         this.render_value(); // doesn't get called automatically in kanban_widgets.AbstractField
//         // this.$el.tooltip({title: _t("employee presence<br/>green: checked in<br/>red: checked out"), trigger: 'hover'});
//         return this._super();
//     },
//     render_value: function() {
//         this.$('.oe_working_schedule_calendar_status').toggleClass("oe_working_schedule_calendar_status_green", this.get_value() == 'checked_in');
//         this.$('.oe_working_schedule_calendar_status').toggleClass("oe_working_schedule_calendar_status_grey", this.get_value() == 'not_checked_in');
//     },
//     display_field: function() {
//         this.$el.html(QWeb.render("Indicator"));
//     },
// });

core.form_widget_registry.add('working_schedule_calendar_form_presence_indicator', FormIndicator);
// calendar_widgets.registry.add('working_schedule_calendar_presence_indicator', CalendarIndicator);

});
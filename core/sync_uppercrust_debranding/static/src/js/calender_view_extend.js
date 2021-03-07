odoo.define('sync_uppercrust_debranding.CalendarViewextend', function (require) {
    "use strict";
    var CalendarView = require('web_calendar.CalendarView');
    var time = require('web.time');
    var core = require('web.core');

    var _t = core._t;

    function get_fc_defaultOptions() {
	    var dateFormat = time.strftime_to_moment_format(_t.database.parameters.date_format);

	    // moment.js converts '%p' to 'A' for 'AM/PM'
	    // But FullCalendar v1.6.4 supports 'TT' format for 'AM/PM' but not 'A'
	    // NB: should be removed when fullcalendar is updated to 2.0 because it would
	    // be supported. See the following link
	    // http://fullcalendar.io/wiki/Upgrading-to-v2/
	    var timeFormat = time.strftime_to_moment_format(_t.database.parameters.time_format).replace('A', 'TT');

	    // adapt format for fullcalendar v1.
	    // see http://fullcalendar.io/docs1/utilities/formatDate/
	    var conversions = [['YYYY', 'yyyy'], ['YY', 'y'], ['DDDD', 'dddd'], ['DD', 'dd']];
	    _.each(conversions, function(conv) {
	        dateFormat = dateFormat.replace(conv[0], conv[1]);
	    });

	    // If 'H' is contained in timeFormat display '10:00'
	    // Else display '10 AM'. 
	    // See : http://fullcalendar.io/docs1/utilities/formatDate/
	    var hourFormat = function(timeFormat){
	        if (/H/.test(timeFormat))
	            return 'HH:mm';
	        return 'hh TT';
	    };

	    return {
	        weekNumberTitle: _t("W"),
	        allDayText: _t("All day"),
	        monthNames: moment.months(),
	        monthNamesShort: moment.monthsShort(),
	        dayNames: moment.weekdays(),
	        dayNamesShort: moment.weekdaysShort(),
	        firstDay: moment._locale._week.dow,
	        weekNumberCalculation: function(date) {
	            return moment(date).week();
	        },
	        axisFormat: hourFormat(timeFormat),
	        // Correct timeformat for agendaWeek and agendaDay
	        // http://fullcalendar.io/docs1/text/timeFormat/
	        timeFormat: timeFormat + ' {- ' + timeFormat + '}',
	        weekNumbers: true,
	        titleFormat: {
	            month: 'MMMM yyyy',
	            week: "w",
	            day: dateFormat,
	        },
	        columnFormat: {
	            month: 'ddd',
	            week: 'ddd ' + dateFormat,
	            day: 'dddd ' + dateFormat,
	        },
	        weekMode : 'liquid',
	        snapMinutes: 15,
	    };
	}



    CalendarView.include({
	    get_fc_init_options: function () {
	        //Documentation here : http://arshaw.com/fullcalendar/docs/
	        var self = this;
	        return $.extend({}, get_fc_defaultOptions(), {
	            defaultView: (this.mode == "month")? "month" : ((this.mode == "week")? "agendaWeek" : ((this.mode == "day")? "agendaDay" : "month")),
	            header: false,
	            selectable: !this.options.read_only_mode && this.create_right,
	            selectHelper: true,
	            editable: this.editable,
	            droppable: true,

	            // callbacks
	            viewRender: function(view) {
	                var mode = (view.name == "month")? "month" : ((view.name == "agendaWeek") ? "week" : "day");
	                if(self.$buttons !== undefined) {
	                    self.$buttons.find('.active').removeClass('active');
	                    self.$buttons.find('.o_calendar_button_' + mode).addClass('active');
	                }

	                var title = self.title + ' (' + ((mode === "week")? _t("Week ") : "") + view.title + ")"; 
	                self.set({'title': title});

	                self.$calendar.fullCalendar('option', 'height', Math.max(290, parseInt(self.$('.o_calendar_view').height())));

	                setTimeout(function() {
	                    var $fc_view = self.$calendar.find('.fc-view');
	                    var width = $fc_view.find('> table').width();
	                    $fc_view.find('> div').css('width', (width > $fc_view.width())? width : '100%'); // 100% = fullCalendar default
	                }, 0);
	            },
	            windowResize: function() {
	                self.$calendar.fullCalendar('render');
	            },
	            eventDrop: function (event, _day_delta, _minute_delta, _all_day, _revertFunc) {
	                var data = self.get_event_data(event);
	                self.proxy('update_record')(event._id, data); // we don't revert the event, but update it.
	            },
	            eventResize: function (event, _day_delta, _minute_delta, _revertFunc) {
	                var data = self.get_event_data(event);
	                self.proxy('update_record')(event._id, data);
	            },
	            eventRender: function (event, element, view) {
	                element.find('.fc-event-title').html(event.title + event.attendee_avatars);
	            },
	            eventAfterRender: function (event, element, view) {
	                if ((view.name !== 'month') && (((event.end-event.start)/60000)<=30)) {
	                    //if duration is too small, we see the html code of img
	                    var current_title = $(element.find('.fc-event-time')).text();
	                    var new_title = current_title.substr(0,current_title.indexOf("<img")>0?current_title.indexOf("<img"):current_title.length);
	                    element.find('.fc-event-time').html(new_title);
	                }
	            },
	            eventClick: function (event) { self.open_event(event._id,event.title); },
	            select: function (start_date, end_date, all_day, _js_event, _view) {
	                var data_template = self.get_event_data({
	                    start: start_date,
	                    end: end_date,
	                    allDay: all_day,
	                });
	                self.open_quick_create(data_template);
	            },

	            unselectAuto: false,
	        });
	    },

    });
});
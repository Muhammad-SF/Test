odoo.define('actual.timesheet', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
var form_common = require('web.form_common');
var formats = require('web.formats');
var Model = require('web.DataModel');
var time = require('web.time');
var utils = require('web.utils');

var QWeb = core.qweb;
var _t = core._t;

var ActualTimesheet = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
    events: {
        "click .oe_timesheet_weekly_attendance": "go_to_attadance",
        "click .approve_btn": "approve_timesheet",
    },
    ignore_fields: function() {
        return ['line_id'];
    },
    init: function() {
        this._super.apply(this, arguments);
        this.set({
            sheets: [],
            date_from: false,
            date_to: false,
        });

        this.field_manager.on("field_changed:timesheet_ids", this, this.query_sheets);
        this.field_manager.on("field_changed:date_from", this, function() {
            this.set({"date_from": time.str_to_date(this.field_manager.get_field_value("date_from"))});
        });
        this.field_manager.on("field_changed:date_to", this, function() {
            if (this.field_manager.get_field_value("date_to") >= new Date().toISOString().slice(0, 10)) {
                // alert("Date To should be before today!");
            }
            else {
                this.set({"date_to": time.str_to_date(this.field_manager.get_field_value("date_to"))});
            }
            // this.set({"date_to": time.str_to_date(this.field_manager.get_field_value("date_to"))});
        });
        this.field_manager.on("field_changed:branch_id", this, function() {
            this.set({"branch_id": this.field_manager.get_field_value("branch_id")});
        });
        this.field_manager.on("field_changed:user_id", this, function() {
            this.set({"user_id": this.field_manager.get_field_value("user_id")});
        });
        this.on("change:sheets", this, this.update_sheets);
        this.res_o2m_drop = new utils.DropMisordered();
        this.render_drop = new utils.DropMisordered();
        this.description_line = _t("/");
    },
    approve_timesheet: function(event){
        console.log('Approve: ', event);
        const date = $(event.target).parent('td').data('date');
        const employee = $(event.target).data('employee');
        const ATLModel = new Model('actual.timesheet.line');
        ATLModel.call('approve_timesheet', [employee, date]).then((result) => {
            $(event.target).parent('td').find('.approve_btn').hide();
            $(event.target).parent('td').find('.cancel_btn').hide();
        });
    },
    go_to_attadance: function(event) {
        console.log('abc');
        const date = $(event.target).parent('td').data('date');
        const employee = $(event.target).data('employee');
        this.do_action({
        	type: 'ir.actions.act_window',
            res_model: "hr.attendance",
            name: 'Attendance',
            views: [
                [false, 'list'],
                [false, 'form'],
            ],
            target: 'current',
            domain: [
            	["employee_id", "=",  employee],
            	["check_in", ">=",  date],
            	["check_in", "<=",  date],
            ],
            context: {},
        });
        // this.do_action({
        //     type: 'ir.actions.act_window',
        //     res_model: "hr.employee",
        //     res_id: id,
        //     views: [[false, 'form']],
        // });
    },
    query_sheets: function() {
        if (this.updating) {
            return;
        }
        this.querying = true;
        var commands = this.field_manager.get_field_value("timesheet_ids");
        var self = this;
        this.res_o2m_drop.add(new Model(this.view.model).call("resolve_2many_commands",
                ["timesheet_ids", commands, [], new data.CompoundContext()]))
            .done(function(result) {
                self.set({sheets: result});
                self.querying = false;
            });
    },
    update_sheets: function() {
        if(this.querying) {
            return;
        }
        this.updating = true;

        var commands = [form_common.commands.delete_all()];
        _.each(this.get("sheets"), function (_data) {
            var data = _.clone(_data);
            if(data.id) {
                commands.push(form_common.commands.link_to(data.id));
                commands.push(form_common.commands.update(data.id, data));
            } else {
                commands.push(form_common.commands.create(data));
            }
        });

        var self = this;
        this.field_manager.set_values({'timesheet_ids': commands}).done(function() {
            self.updating = false;
        });
    },
    initialize_field: function() {
        form_common.ReinitializeWidgetMixin.initialize_field.call(this);
        this.on("change:sheets", this, this.initialize_content);
        this.on("change:date_to", this, this.initialize_content);
        this.on("change:date_from", this, this.initialize_content);
        this.on("change:user_id", this, this.initialize_content);
        this.on("change:branch_id", this, this.onchange_branch);
    },
    onchange_branch: function() {
        var branchId = this.get('branch_id');
        var ResBranch = new Model('res.branch');
        ResBranch.call('get_list_employee_ids', [branchId]).then((employee_ids) => {
            console.log('Employee: ', employee_ids);
            var ops = this.generate_o2m_value();
            employee_ids.map(employee_id => {
                ops.push(_.extend({}, this.default_get, {
                    name: this.description_line,
                    overtime_hours: 0,
                    date: time.date_to_str(this.dates[0]),
                    employee_id: employee_id,
                    option: '',
                    updating: true,
                    from_hours: 0,
                    to_hours: 0,
                }));
            })
            this.set({
                sheets: ops
            });
            this.destroy_content();
        })
    },
    initialize_content: function() {
        if(this.setting) {
            return;
        }

        // don't render anything until we have date_to and date_from
        if (!this.get("date_to") || !this.get("date_from")) {
            return;
        }

        // it's important to use those vars to avoid race conditions
        var dates;
        var employees;
        var employee_names;
        var employee_jobs;
        var default_get;
        var self = this;
        return this.render_drop.add(new Model("actual.timesheet.line").call("default_get", [
            ['date','name','user_id','employee_id', 'option','from_hours','to_hours','overtime_hours', 'attendance_ids',
                'start_time','aft_clock_in', 'aft_clock_out', 'alt_clock_in','alt_clock_out'],
            new data.CompoundContext({'user_id': self.get('user_id')})
        ]).then(function(result) {
            self.canBeApproved = result.canBeApproved;
            default_get = result;
            // calculating dates
            dates = [];
            var start = self.get("date_from");
            var end = self.get("date_to");
            while (start <= end) {
                dates.push(start);
                var m_start = moment(start).add(1, 'days');
                start = m_start.toDate();
            }
            // group by employee
            employees = _.chain(self.get("sheets"))
            .map(_.clone)
            .each(function(el) {
                // much simpler to use only the id in all cases
                if (typeof(el.employee_id) === "object") {
                    el.employee_id = el.employee_id[0];
                }
            })
            .groupBy("employee_id").value();

            var employee_ids = _.map(_.keys(employees), function(el) { return el === "false" ? false : Number(el); });

            employees = _(employees).chain().map(function(lines, employee_id) {
                console.log('lineslineslines   '+JSON.stringify(lines))
                var employees_defaults = _.extend({}, default_get, (employees[employee_id] || {}).value || {});
                // group by days
                employee_id = (employee_id === "false")? false : Number(employee_id);
                var index = _.groupBy(lines, "date");
                var days = _.map(dates, function(date) {
                    var day = {day: date, lines: index[time.date_to_str(date)] || []};
                    // add line where we will insert/remove hours
                    console.log('Date '+date)
                    console.log('day.lines   '+JSON.stringify(day.lines))
                    var to_add = _.find(day.lines, function(line) { return line.name === self.description_line; });
                    if (to_add) {
                        day.lines = _.without(day.lines, to_add);
                        day.lines.unshift(to_add);
                    } else {
                        day.lines.unshift(_.extend(_.clone(employees_defaults), {
                            name: self.description_line,
                            overtime_hours: 0,
                            date: time.date_to_str(date),
                            employee_id: employee_id,
                            option: '',
                            from_hours:0,
                            to_hours:0,
                            // attendance_ids:[]
                        }));
                    }
                    return day;
                });
                return {employee: employee_id, days: days, employees_defaults: employees_defaults};
            }).value();

            // we need the name_get of the employees
            return new Model("hr.employee").call("read", [_.pluck(employees, "employee"),[]]).then(function(result) {
                employee_names = {};
                employee_jobs = {};
                _.each(result, function(el) {
                    console.log('EMPLOUEEEE   '+JSON.stringify(el))
                    employee_names[el['id']] = el['name'];
                    if (typeof(el['job_id']) === "object") {
                        employee_jobs[el['id']] = el['job_id'][1];
                    }
                    else{
                        employee_jobs[el['id']] = '';
                    }
                });

                employees = _.sortBy(employees, function(el) {
                    return employee_names[el.employee];
                });
            });
        })).then(function(result) {
            // we put all the gathered data in self, then we render
            self.dates = dates;
            self.employees = employees;
            self.employee_names = employee_names;
            self.employee_jobs = employee_jobs;
            self.default_get = default_get;
            //real rendering
            new Model('actual.timesheet').call('get_clock_in',[employees]).then(function (result) {
                console.log(result);
                self.employee_clock_in = result;
                self.display_data();
            });
        });
    },
    destroy_content: function() {
        if (this.dfm) {
            this.dfm.destroy();
            this.dfm = undefined;
        }
    },
    is_valid_value:function(value){
        this.view.do_notify_change();
        var split_value = value.split(":");
        var valid_value = true;
        if (split_value.length > 2) {
            return false;
        }
        _.detect(split_value,function(num){
            if(isNaN(num)) {
                valid_value = false;
            }
        });
        return valid_value;
    },
    canBeAprrove: function(){
        return this.canBeApproved || this.field_manager.datarecord.canBeApproved;
    },
    display_data: function() {
        var self = this;
        self.$el.html(QWeb.render("sarangoci_actual_timesheet.ActualTimesheet", {widget: self}));
        _.each(self.employees, function(employee) {
            _.each(_.range(employee.days.length), function(day_count) {
                if (!self.get('effective_readonly')) {
                    console.log('Editable mode: ' + JSON.stringify(employee.days[day_count].lines[0]));
                    const forcastFields = ['employee_id', 'date', 'option', 'from_hours', 'overtime_hours'];
                    const actual_fields = ['date', 'start_time', 'aft_clock_in', 'aft_clock_out', 'alt_clock_in', 'alt_clock_out', 'overtime_hours', 'overtime_input','employee_id', 'approver_id'];
                    const domain = [['employee_id', '=', employee.employee], ['date','=',employee.days[day_count].lines[0].date]];
                    let current_date = employee.days[day_count].lines[0].date;
                    let current_line = employee.days[day_count].lines[0].date;
                    const ATLModel = new Model('actual.timesheet.line');
                    const BTLModel = new Model('branch.timesheet.line');
                     BTLModel.query(forcastFields).filter(domain).limit(1).all().then(function (result) {
                         if(result && result.length>0){
                             console.log("BTL Employee " + employee.employee + " - day " + employee.employee + ": ", result );
                             employee.days[day_count].lines[0].option = employee.days[day_count].lines[0].option || result[0].option;
                             employee.days[day_count].lines[0].start_time = employee.days[day_count].lines[0].start_time || result[0].from_hours;
                             self.get_option_box(employee, day_count).val(employee.days[day_count].lines[0].option);
                             self.get_start_time_box(employee, day_count).val(self.formatTime(employee.days[day_count].lines[0].start_time));

                         }
                     });

                     ATLModel.query(actual_fields).filter(domain).limit(1).all().then(function (result) {
                         if(result && result.length>0){
                             console.log("ATL Employee " + employee.employee + " - day " + employee.employee + ": ", result );
                             self.get_first_clock_in_box(employee, day_count).text(self.start_box(result[0].aft_clock_in) || 0);
                             self.get_first_clock_out_box(employee, day_count).text(self.start_box(result[0].aft_clock_out) || 0);
                             self.get_last_clock_in_box(employee, day_count).text(self.start_box(result[0].alt_clock_in) || 0);
                             self.get_last_clock_out_box(employee, day_count).text(self.start_box(result[0].alt_clock_out) || 0);

                             employee.days[day_count].lines[0].aft_clock_in = self.start_box(result[0].aft_clock_in) || 0;
                             employee.days[day_count].lines[0].aft_clock_out = self.start_box(result[0].aft_clock_out) || 0;
                             employee.days[day_count].lines[0].alt_clock_in = self.start_box(result[0].alt_clock_in) || 0;
                             employee.days[day_count].lines[0].alt_clock_out = self.start_box(result[0].alt_clock_out) || 0;
                             employee.days[day_count].lines[0].overtime_hours = employee.days[day_count].lines[0].overtime_hours || result[0].overtime_hours || 0;
                             employee.days[day_count].lines[0].overtime_input = employee.days[day_count].lines[0].overtime_input || result[0].overtime_hours || 0;

                             self.get_system_ot_box(employee, day_count).html(self.overtime_hours_box(employee, day_count));
                             self.get_inputted_ot_box(employee, day_count).val(self.formatTime(employee.days[day_count].lines[0].overtime_input || 0));
                             employee.days[day_count].lines[0].approver_id = result[0].approver_id;
                             if(result[0].approver_id){
                                 $('td[data-date="' + current_date + '"]').find('.approve_btn').hide();
                                 $('td[data-date="' + current_date + '"]').find('.cancel_btn').hide();
                             }
                         }
                     });

                     self.get_start_time_box(employee, day_count).val(self.start_time_box(employee, day_count, true)).change(function() {
                        var num = $(this).val();
                        if (self.is_valid_value(num) && num !== 0) {
                            num = Number(self.parse_client(num));
                        }
                        if (isNaN(num)) {
                        } else {
                            employee.days[day_count].lines[0].start_time = num;
                            if(!isNaN($(this).val())){
                                $(this).val(self.start_time_box(employee, day_count, true));
                            }
                            self.sync();
                        }
                    });
                     self.get_inputted_ot_box(employee, day_count).val(self.overtime_input_box(employee, day_count, true)).change(function() {
                        var num = $(this).val();
                        if (self.is_valid_value(num) && num !== 0) {
                            num = Number(self.parse_client(num));
                        }
                        if (isNaN(num)) {
                        } else {
                            employee.days[day_count].lines[0].overtime_input = num;
                            if(!isNaN($(this).val())){
                                $(this).val(self.overtime_input_box(employee, day_count, true));
                            }
                            self.sync();
                        }
                    });

                    self.get_option_box(employee, day_count).val(self.option_box(employee, day_count)).change(function() {
                            employee.days[day_count].lines[0].option = $(this).val();
                            $(this).val(self.option_box(employee, day_count));
                            self.sync();
                        });
                } else {
                    console.log('BBBBBBBBBB');
                    self.get_option_box(employee, day_count).html(self.option_box(employee, day_count) || '&nbsp;');
                    var option = employee.days[day_count].lines[0].option
                    var color = 'white'
                    if(option=='Off'){color = '#A9A9A9'}
                    else if(option=='Ijin'){color='#01579B'}
                    else if(option=='Sakit'){color='#B3E5FC'}
                    else if(option=='Cuti'){color=' #66CDAA'}
                    else if(option=='Alpha'){color='#F44336'}
                    else if(option){color='#D4E157'}
                    self.get_option_box(employee, day_count).parent().css("background-color", color);
                    self.get_start_time_box(employee, day_count).html(self.start_time_box(employee, day_count, true));
                    self.get_first_clock_in_box(employee, day_count).html(self.aft_clock_in_box(employee, day_count, true));
                    self.get_first_clock_out_box(employee, day_count).html(self.aft_clock_out_box(employee, day_count, true));
                    self.get_last_clock_in_box(employee, day_count).html(self.alt_clock_in_box(employee, day_count, true));
                    self.get_last_clock_out_box(employee, day_count).html(self.alt_clock_out_box(employee, day_count, true));
                    self.get_system_ot_box(employee, day_count).html(self.overtime_hours_box(employee, day_count, true));
                    self.get_inputted_ot_box(employee, day_count).html(self.overtime_input_box(employee, day_count, true));

                    const forcastFields = ['employee_id', 'date', 'option', 'from_hours', 'overtime_hours'];
                    const actual_fields = ['date', 'start_time', 'aft_clock_in', 'aft_clock_out', 'alt_clock_in', 'alt_clock_out', 'overtime_hours', 'overtime_input','employee_id'];
                    const domain = [['employee_id', '=', employee.employee], ['date','=',employee.days[day_count].lines[0].date]];

                    const ATLModel = new Model('actual.timesheet.line');
                    const BTLModel = new Model('branch.timesheet.line');
                    BTLModel.query(forcastFields).filter(domain).limit(1).all().then(function (result) {
                        console.log('Noeditable: emp_' + employee.employee + '/' + employee.days[day_count].lines[0].date + ': ', result );
                        if(result && result.length>0){
                            self.pull_forecast(employee, day_count, result[0]);
                            self.pull_forecast_label(employee, day_count, employee.days[day_count].lines[0]);
                        }
                    });
                    ATLModel.query(actual_fields).filter(domain).limit(1).all().then((result) => {
                        console.log('Noeditable: emp_' + employee.employee + '/' + employee.days[day_count].lines[0].date + ': ', result );
                        if(result && result.length>0){
                            self.pull_attendance(employee, day_count, result[0]);
                            self.pull_attendance_label(employee, day_count, employee.days[day_count].lines[0]);
                        }
                    });
                }
            });
        });
        // if(!this.get('effective_readonly')) {
        //     this.init_add_employee();
        // }
    },

    pull_forecast_label: function (employee, day_count, values) {
        this.get_option_box(employee, day_count).text(values.option || 0);
        this.get_start_time_box(employee, day_count).text(this.formatTime(values.start_time, 0) || 0);
    },
    pull_forecast: function(employee, day_count, values){
        employee.days[day_count].lines[0].option = employee.days[day_count].lines[0].option || values.option;
        employee.days[day_count].lines[0].start_time = employee.days[day_count].lines[0].start_time || values.from_hours;
        employee.days[day_count].lines[0].overtime_hours = employee.days[day_count].lines[0].overtime_hours || values.overtime_hours;
        employee.days[day_count].lines[0].overtime_input = employee.days[day_count].lines[0].overtime_input || values.overtime_hours;
    },
    pull_default_forecast_label: function(employee, day_count, values){
        this.get_option_box(employee, day_count).val('');
        this.get_start_time_box(employee, day_count).val(0);
    },
    pull_attendance_label: function (employee, day_count, values) {
        this.get_first_clock_in_box(employee, day_count).text(this.start_box(values.aft_clock_in) || 0);
        this.get_first_clock_out_box(employee, day_count).text(this.start_box(values.aft_clock_out) || 0);
        this.get_last_clock_in_box(employee, day_count).text(this.start_box(values.alt_clock_in) || 0);
        this.get_last_clock_out_box(employee, day_count).text(this.start_box(values.alt_clock_out) || 0);
        this.get_system_ot_box(employee, day_count).html(this.overtime_hours_box(employee, day_count));
        this.get_inputted_ot_box(employee, day_count).html(this.formatTime(this.getFistLine(employee, day_count, 'overtime_input')));
    },

    pull_default_attendance_label: function (employee, day_count) {
        this.get_first_clock_in_box(employee, day_count).text(this.formatTime(0));
        this.get_first_clock_out_box(employee, day_count).text(this.formatTime(0));
        this.get_last_clock_in_box(employee, day_count).text(this.formatTime(0));
        this.get_last_clock_out_box(employee, day_count).text(this.formatTime(0));
    },

    pull_attendance: function (employee, day_count, values) {
        employee.days[day_count].lines[0].aft_clock_in = this.start_box(values.aft_clock_in) || 0;
        employee.days[day_count].lines[0].aft_clock_out = this.start_box(values.aft_clock_out) || 0;
        employee.days[day_count].lines[0].alt_clock_in = this.start_box(values.alt_clock_in) || 0;
        employee.days[day_count].lines[0].alt_clock_out = this.start_box(values.alt_clock_out) || 0;
        employee.days[day_count].lines[0].overtime_hours = employee.days[day_count].lines[0].overtime_hours || values.overtime_hours;
        employee.days[day_count].lines[0].overtime_input = employee.days[day_count].lines[0].overtime_input || values.overtime_hours;
    },
    init_add_employee: function() {
        if (this.dfm) {
            this.dfm.destroy();
        }
        var self = this;
        this.$(".oe_timesheet_weekly_add_row").show();
        this.dfm = new form_common.DefaultFieldManager(this);
        this.dfm.extend_field_desc({
            employee: {
                relation: "hr.employee",
            },
        });
        var FieldMany2One = core.form_widget_registry.get('many2one');
        this.employee_m2o = new FieldMany2One(this.dfm, {
            attrs: {
                name: "employee",
                type: "many2one",
                domain: [
                    ['id', 'not in', _.pluck(this.employees, "employee")],
                ],
                modifiers: '{"required": true}',
            },
        });
        this.employee_m2o.prependTo(this.$(".o_add_timesheet_line > div")).then(function() {
            self.employee_m2o.$el.addClass('oe_edit_only');
        });
        this.$(".oe_timesheet_button_add").click(function() {
            var id = self.employee_m2o.get_value();
            if (id === false) {
                self.dfm.set({display_invalid_fields: true});
                return;
            }

            var ops = self.generate_o2m_value();
            ops.push(_.extend({}, self.default_get, {
                name: self.description_line,
                overtime_hours: 0,
                date: time.date_to_str(self.dates[0]),
                employee_id: id,
                option:'',
                from_hours:0,
                to_hours:0,
                // attendance_ids:[],
            }));
            self.set({sheets: ops});
            self.destroy_content();
        });
    },
    get_option_box: function(employee, day_count) {
        return this.$('[data-employee-option="' + employee.employee + '"][data-day-count="' + day_count + '"]');
    },
    get_start_time_box: function(employee, day_count) {
        return this.$('[data-start-time="' + employee.employee + '"][data-day-count="' + day_count + '"]');
    },
    get_first_clock_in_box: function(employee, day_count) {
        return this.$('[data-first-clock-in="' + employee.employee + '"][data-day-count="' + day_count + '"]');
    },
    get_first_clock_out_box: function(employee, day_count) {
        return this.$('[data-first-clock-out="' + employee.employee + '"][data-day-count="' + day_count + '"]');
    },
    get_last_clock_in_box: function(employee, day_count) {
        return this.$('[data-last-clock-in="' + employee.employee + '"][data-day-count="' + day_count + '"]');
    },
    get_last_clock_out_box: function(employee, day_count) {
        return this.$('[data-last-clock-out="' + employee.employee + '"][data-day-count="' + day_count + '"]');
    },
    get_system_ot_box: function(employee, day_count) {
        return this.$('[data-overtime-hours="' + employee.employee + '"][data-day-count="' + day_count + '"]');
    },
    get_inputted_ot_box: function(employee, day_count) {
        return this.$('[data-overtime-input="' + employee.employee + '"][data-day-count="' + day_count + '"]');
    },
    sum_box: function(employee, day_count, show_value_in_hour) {
        var line_total = 0;
        _.each(employee.days[day_count].lines, function(line) {
            line_total += line.overtime_hours;
        });
        return (show_value_in_hour && line_total !== 0)?this.formatUTCTime(line_total):line_total;
    },
    from_box: function(employee, day_count, show_value_in_hour) {
        return employee.days[day_count].lines[0].from_hours? this.formatUTCTime(employee.days[day_count].lines[0].from_hours):0;
    },
    to_box: function(employee, day_count, show_value_in_hour) {
        return employee.days[day_count].lines[0].to_hours? this.formatUTCTime(employee.days[day_count].lines[0].to_hours):0;
    },
    start_time_box: function(employee, day_count, value_in_hour) {
        let value =  employee.days[day_count].lines[0].start_time || 0;
        return value_in_hour && value ? this.formatTime(value) : 0;
    },
    aft_clock_in_box: function(employee, day_count, value_in_hour) {
        let value =  employee.days[day_count].lines[0].aft_clock_in || 0;
        return value_in_hour && value ? this.formatUTCTime(value) : 0;
    },
    aft_clock_out_box: function(employee, day_count, value_in_hour) {
        let value =  employee.days[day_count].lines[0].aft_clock_out || 0;
        return value_in_hour && value ? this.formatUTCTime(value) : 0;
    },
    alt_clock_in_box: function(employee, day_count, value_in_hour) {
        let value =  employee.days[day_count].lines[0].alt_clock_in || 0;
        return value_in_hour && value ? this.formatUTCTime(value) : 0;
    },
    alt_clock_out_box: function(employee, day_count, value_in_hour) {
        let value =  employee.days[day_count].lines[0].alt_clock_out || 0;
        return value_in_hour && value ? this.formatUTCTime(value) : 0;
    },
    overtime_hours_box: function(employee, day_count, value_in_hour) {
        let value =  employee.days[day_count].lines[0].overtime_hours || 0;
        return value_in_hour && value ? this.formatUTCTime(value, false) : value.toFixed(2);
    },
    overtime_input_box: function(employee, day_count, value_in_hour) {
        let value =  employee.days[day_count].lines[0].overtime_input || 0;
        return value_in_hour && value ? this.formatTime(value) : value;
    },
    getFistLine: function(employee, day_count, field, value_in_hour=false) {
        let value =  employee.days[day_count].lines[0][field] || 0;
        return value_in_hour && value ? this.formatUTCTime(value) : value;
    },
    start_box: function(time) {
        return time? this.formatUTCTime(time):0;
    },
    formatUTCTime: function (value) {
        var timezone = new Date().getTimezoneOffset() / -60;
        var pattern = '%02d.%02d';
        if (value < 0) {
            value = Math.abs(value);
        }
        var hour = Math.floor(value + timezone);
        var min = Math.round((value % 1) * 60);
        if (min >= 60) {
            min = 0;
            hour = hour + 1;
        }
        if( hour >= 24 ){
            hour = hour% 24;
        }
        return _.str.sprintf(pattern, hour, min);
    },
    formatTime: function (value) {
        var pattern = '%02d.%02d';
        if (value < 0) {
            value = Math.abs(value);
        }
        var hour = Math.floor(value);
        var min = Math.round((value % 1) * 60);
        if (min == 60) {
            min = 0;
            hour = hour + 1;
        }
        if( hour >= 24 ){
            hour = hour% 24;
        }
        return _.str.sprintf(pattern, hour, min);
    },
    clock_box: function(employee_clock, day_count) {
        if(!employee_clock[day_count].check_in) return 0;
        let time_check = new Date(employee_clock[day_count].check_in);
        return (time_check.getHours() < 10 ? "0" : "") + time_check.getHours() + ":" + (time_check.getMinutes() < 10 ? "0" : "") + time_check.getMinutes();
    },
    option_box: function(employee, day_count) {
        return employee.days[day_count].lines[0]? employee.days[day_count].lines[0].option:'';
    },
    sync: function() {
        this.setting = true;
        this.set({sheets: this.generate_o2m_value()});
        this.setting = false;
    },
    //converts hour value to float
    parse_client: function(value) {
        return formats.parse_value(value, { type:"float_time" });
    },
    //converts float value to hour
    // formatUTCTime:function(value){
    //     return formats.format_value(value, { type:"float_time" });
    // },
    generate_o2m_value: function() {
        var ops = [];
        var ignored_fields = this.ignore_fields();
        console.log(JSON.stringify('     dfd    '+this.employees))
        _.each(this.employees, function(employee) {
            _.each(employee.days, function(day) {
                _.each(day.lines, function(line) {
                    if (line.overtime_hours !== 0 || line.option || line.from_hours !== 0 || line.to_hours !== 0) {
                        var tmp = _.clone(line);
                        _.each(line, function(v, k) {
                            if (v instanceof Array) {
                                tmp[k] = v[0];
                            }
                        });
                        // we remove line_id as the reference to the _inherits field will no longer exists
                        tmp = _.omit(tmp, ignored_fields);
                        ops.push(tmp);
                    }
                });
            });
        });
        console.log('opsopsops   '+JSON.stringify(ops))
        return ops;
    },
});

core.form_custom_registry.add('actual_timesheet', ActualTimesheet);

});
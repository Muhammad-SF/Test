odoo.define('web_gantt_native.ToolTip', function (require) {
"use strict";


var core = require('web.core');
var Widget = require('web.Widget');
var time = require('web.time');
var _t = core._t;



var GanttToolTip = Widget.extend({
    template: "GanttToolTip",

   /// this.chart.tooltip.show(this.resizerOffsetX, this);

    init: function(parent, ganttbar) {

        this._super(parent);
        this.record = ganttbar;

    },

    start: function() {


        var self = this;

        this.$el.append('<div class="task-gantt-line-tip-names"></div>');

        var record = self.record[0];

        if (record) {
            var record_data = record.record;
            var expected_duration = (record_data["duration"] * 3600) / 60
            var name = record_data['value_name'];
            var workcenter = false
            if (record_data['workcenter']){
                workcenter = record_data['workcenter'][1];
            }
            var real_duration = false
            if(record_data['real_duration']){
                real_duration = (record_data['real_duration'] * 3600) / 60
            }
            // var duration = record_data['duration']

            // var task_start = record_data['task_start'].toUTCString()
            //
            // var ttt = record_data.task_start;

            // var formatDate = "DD.MM.YYYY HH:mm:ss"; // the string that represents desired format.
            var l10n = _t.database.parameters;

            var formatDate = time.strftime_to_moment_format( l10n.date_format + ' ' + l10n.time_format);


            // var task_start = time.auto_date_to_str(record_data.task_start, 'datetime');
            var task_start,task_stop = false

            if(record_data['wo_state'] == 'done'){
                task_start = moment(record_data["effective_dt_st"]).format(formatDate);
                task_stop = moment(record_data["effective_dt_ed"]).format(formatDate);
            }
            if(record_data['wo_state'] == 'pending' || record_data['wo_state'] == 'ready' || record_data['wo_state'] == 'progress'){
                task_start = moment(record_data["planed_dt_st"]).format(formatDate);
                task_stop = moment(record_data["planed_dt_ed"]).format(formatDate);
            }
            if(record_data['wo_state'] == undefined){
                task_start = time.auto_date_to_str(record_data.task_start, 'datetime');
                task_stop = time.auto_date_to_str(record_data.task_stop, 'datetime');
            }

            var date_deadline = false;
            if (record_data["date_deadline"]) {

                date_deadline = moment(record_data["date_deadline"]).format(formatDate);
            }


            // var task_stop = record_data['task_stop'];
            // task_stop = time.auto_date_to_str(task_stop, 'datetime');

            // var date_deadline = record_data['date_deadline'];
            // date_deadline = time.auto_date_to_str(date_deadline, 'datetime');

            var progress = '';
            var progress_name = 'progress';
            if (record_data['progress']){
                progress = record_data['progress'];

                var progress_field = self.__parentedParent.model_fields_dict['progress'];
                if (progress_field){
                    progress_name = self.__parentedParent.fields[progress_field].string;

                }
                self.__parentedParent.fields[''];
                // progress_name
                //self.model_fields_dict = getFields["model_fields_dict"];

            }

            var date_done = false;
            if (record_data["date_done"]) {

                date_done = moment(record_data["date_done"]).format(formatDate);

            }

            var duration = false;
            if (record_data["duration"]) {

                var total = parseInt(expected_duration, 10);

                if (record_data['duration_scale']) {
                    // duration = humanizeDuration(total*1000,{ units: record_data['duration_scale'].split(",")});
                    duration = humanizeDuration(total * 1000, {
                        units: record_data['duration_scale'].split(","),
                        round: true
                    });
                }
                else{
                    duration = humanizeDuration(total*1000);
                }

            }

            var plan_duration = false;
            if (record_data["plan_duration"]) {
                var plan_total = parseInt(record_data["plan_duration"], 10);

                if (record_data['duration_scale']) {
                    // plan_duration = humanizeDuration(plan_total*1000,{ units: record_data['duration_scale'].split(",")});
                    plan_duration = humanizeDuration(plan_total * 1000, {
                        units: record_data['duration_scale'].split(","),
                        round: true
                    });
                }
                else{
                    plan_duration = humanizeDuration(plan_total*1000);
                }

            }
            var wo_progress = false
            if(record_data["qty_prod"] >= 0 && record_data["qty_to_prod"] >= 0){
                wo_progress = (record_data["qty_prod"] / record_data["qty_to_prod"]) * 100 + '%'
            }





            var constrain_type = false;
            if (record_data['constrain_type']){


                var type = [];
                type["asap"] = 'As Soon As Possible';
                type["alap"] = 'As Late As Possible';
                type["fnet"] = 'Finish No Earlier Than';
                type["fnlt"] = 'Finish No Later Than';
                type["mso"] = 'Must Start On';
                type["mfo"] = 'Must Finish On';
                type["snet"] = 'Start No Earlier Than';
                type["snlt"] = 'Start No Later Than';

                constrain_type = type[record_data['constrain_type']];


            }

            var constrain_date = "none";
            if (record_data["constrain_date"]) {

                constrain_date = moment(record_data["constrain_date"]).format(formatDate);

            }

            var converted_real_duration = false
            var converted_exp_duration = false
            
            if(real_duration > expected_duration){
                var d = Number(expected_duration);
                var h = Math.floor(d / 3600);
                var m = Math.floor(d % 3600 / 60);
                var s = Math.floor(d % 3600 % 60);
                
                var h_slice = h.toString().length
                var m_slice = m.toString().length
                var s_slice = s.toString().length

                converted_exp_duration = ('0' + h).slice(-h_slice) + ":" + ('0' + m).slice(-m_slice) + ":" + ('0' + s).slice(-s_slice);

                var dd = Number(real_duration);
                var hh = Math.floor(dd / 3600);
                var mm = Math.floor(dd % 3600 / 60);
                var ss = Math.floor(dd % 3600 % 60);

                converted_real_duration = ('0' + hh).slice(-2) + ":" + ('0' + mm).slice(-2) + ":" + ('0' + ss).slice(-2);
            }else{
                var d = Number(expected_duration);
                var h = Math.floor(d / 3600);
                var m = Math.floor(d % 3600 / 60);
                var s = Math.floor(d % 3600 % 60);

                var h_slice = h.toString().length
                var m_slice = m.toString().length
                var s_slice = s.toString().length

                converted_exp_duration = ('0' + h).slice(-h_slice) + ":" + ('0' + m).slice(-m_slice) + ":" + ('0' + s).slice(-s_slice);

                var dd = Number(real_duration);
                var hh = Math.floor(dd / 3600);
                var mm = Math.floor(dd % 3600 / 60);
                var ss = Math.floor(dd % 3600 % 60);

                converted_real_duration = ('0' + hh).slice(-2) + ":" + ('0' + mm).slice(-2) + ":" + ('0' + ss).slice(-2);
            
            }
            
            $('<div class="task-gantt-line-tip-name">Name:</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
            $('<div class="task-gantt-line-tip-name">Start date:</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
            $('<div class="task-gantt-line-tip-name">End date:</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
            // $('<div class="task-gantt-line-tip-name">Deadline:</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
            // $('<div class="task-gantt-line-tip-name">'+progress_name+'</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
            if(!isNaN(expected_duration)){
                if(record_data['wo_state'] == 'pending' || record_data['wo_state'] == 'ready' || record_data['wo_state'] == 'progress'){
                    if (converted_exp_duration) {
                        $('<div class="task-gantt-line-tip-name">Expected Duration:</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
                    }
                }
            }
            if(record_data['wo_state'] == 'done'){
                if (converted_real_duration) {
                    $('<div class="task-gantt-line-tip-name">Real Duration:</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
                }
            }
            if (workcenter) {
                $('<div class="task-gantt-line-tip-name">Workcenter:</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
            }

            if (date_done) {
                 $('<div class="task-gantt-line-tip-name">Done date:</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
            }

            if (plan_duration) {
                 $('<div class="task-gantt-line-tip-name">Plan Duration:</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
            }

            /*if (duration) {
                 $('<div class="task-gantt-line-tip-name">Duration:</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
            }*/

            if (constrain_type) {
                 $('<div class="task-gantt-line-tip-name">Constraint:</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
            }
            if (wo_progress) {
                 $('<div class="task-gantt-line-tip-name">Manufacturing Percentage:</div>').appendTo(this.$el.children(".task-gantt-line-tip-names"));
            }

            this.$el.append('<div class="task-gantt-line-tip-values"></div>');



            $('<div class="task-gantt-line-tip-value">' + name + '</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));
            $('<div class="task-gantt-line-tip-value">' + task_start + '</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));
            $('<div class="task-gantt-line-tip-value">' + task_stop + '</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));
            // $('<div class="task-gantt-line-tip-value">' + date_deadline + '</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));
            // $('<div class="task-gantt-line-tip-value">' + progress + '%</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));

            if(!isNaN(expected_duration)){
                if(record_data['wo_state'] == 'pending' || record_data['wo_state'] == 'ready' || record_data['wo_state'] == 'progress'){
                    if (converted_exp_duration) {
                        $('<div class="task-gantt-line-tip-value">' + converted_exp_duration + '</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));
                    }
                }
            }
            if(record_data['wo_state'] == 'done'){
                if (converted_real_duration) {
                    $('<div class="task-gantt-line-tip-value">' + converted_real_duration + '</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));
                }
            }
            if (workcenter) {
                $('<div class="task-gantt-line-tip-value">' + workcenter + '</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));
            }

            if (date_done) {
                $('<div class="task-gantt-line-tip-value">' + date_done + '</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));
            }
            if (plan_duration) {
                $('<div class="task-gantt-line-tip-value">' + plan_duration + '</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));
            }

            /*if (duration) {
                $('<div class="task-gantt-line-tip-value">' + duration + '</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));
            }*/

            if (constrain_type) {
                $('<div class="task-gantt-line-tip-value">' + constrain_type + ': ' + constrain_date + '</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));
            }
            if (wo_progress) {
                $('<div class="task-gantt-line-tip-value">' + wo_progress + '</div>').appendTo(this.$el.children(".task-gantt-line-tip-values"));
            }


        }

        if (self.record.offset()) {

            var o_left = self.record.offset().left;
            var o_top = self.record.offset().top;

            var o_right = $(window).width() - (self.record.offset().left + self.record.outerWidth());


            var tip_lenght = this.$el.children(".task-gantt-line-tip-names").children().length;
            var top_new = o_top - (15*tip_lenght); // if added tip plus 15 every tip

            if (o_top < 325){
                top_new = o_top + 20;
            }

            if (o_right < 200){
                o_left = o_left - 200;
            }


            this.$el.offset({top: top_new , left: o_left});
        }


    },


    renderElement: function () {
        this._super();
        this.$el.data('record', this);

    },



});

return GanttToolTip;

});
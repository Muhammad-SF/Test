odoo.define('web_gantt_native.ToolField', function (require) {
"use strict";

    // var core = require('web.core');
    var time = require('web.time');
    var formats = require('web.formats');
    // var _t = core._t;
    // var _lt = core._lt;



    function getFields(parent, group_bys) {

        // this.fields_keys = _.keys(this.fields_view.fields);

        var gantt_fields_0 = [
            "id"
        ];

        var gantt_fields_1 = [

            "name",
            "date_start",
            "date_stop",
            "progress",
            "user_id",

            "task_time",

            "project_id",
            "date_deadline",
            "progress",

            "on_gantt",

            "date_done",
            "state",

            "subtask_project_id",
            "load_data_id",

            "parent_id",

            "default_seq",

            "sorting_seq",
            "sorting_level",
            "subtask_count",

            "is_milestone",
            "schedule_mode",
            "constrain_type",
            "constrain_date",
            "duration",
            "plan_duration",

            "summary_date_start",
            "summary_date_end",

            "plan_action",

            "color_gantt_set",
            "color_gantt",
            "duration_scale",

            "fold_self",
            "fold_child",

            "critical_path",
            "cp_shows",
            "cp_detail",

            "p_loop",

            "product_id",
            "production_id",
            "real_duration",
            "workcenter",
            "wo_state",
            "planed_dt_st",
            "planed_dt_ed",
            "effective_dt_st",
            "effective_dt_ed",
            "qty_prod",
            "qty_to_prod",




        ];

        var model_fields_dict = [];
        var model_fields = _.compact(_.map(gantt_fields_1, function(key) {

            var key_field = parent.fields_view.arch.attrs[key] || '';
            model_fields_dict[key] = key_field;
            return key_field
        }));


        model_fields = _.uniq(model_fields.concat(group_bys, gantt_fields_0));


        return {
            model_fields : model_fields,
            gantt_fields : gantt_fields_1,
            model_fields_dict : model_fields_dict
        }

    }



    function flatRows (row_datas) {

        var rows_to_gantt = [];

        //recursive tree to flat task.
        var generate_flat_gantt = function(value) {
            if (value.is_group) {
                rows_to_gantt.push({

                    id: value.id,
                    is_group: value.is_group,
                    group_id: value.group_info,
                    level: value.level,
                    value_name: value.task_name,
                    group_field: value.group_field,
                    task_count: value.task_count,
                    fold_group: value.fold_group
                });

            }
            else {

                //Some browser crash
                var assign_to = undefined;
                try {
                     assign_to = value.assign_to[1];
                } catch (err) {}

                rows_to_gantt.push({


                    id: value.id,
                    group_id: value.group_info,
                    level: value.level,
                    value_name: value.task_name,

                    assign_to: assign_to,

                    task_start: value.task_start,
                    task_stop: value.task_stop,tree_seq: value.tree_seq,

                    default_seq: value.default_seq,

                    sorting_level : value.sorting_level,
                    sorting_seq: value.sorting_seq,

                    project_id : value.project_id,

                    date_deadline: value.date_deadline,
                    progress: value.progress,

                    is_milestone: value.is_milestone,
                    on_gantt: value.on_gantt,

                    schedule_mode: value.schedule_mode,
                    constrain_type: value.constrain_type,
                    constrain_date: value.constrain_date,
                    duration: value.duration,

                    real_duration: value.real_duration,
                    wo_state: value.wo_state,
                    planed_dt_st:value.planed_dt_st,
                    planed_dt_ed:value.planed_dt_ed,
                    effective_dt_st:value.effective_dt_st,
                    effective_dt_ed:value.effective_dt_ed,
                    qty_prod:value.qty_prod,
                    qty_to_prod:value.qty_to_prod,
                    workcenter: value.workcenter,
                    plan_duration: value.plan_duration,

                    plan_action: value.plan_action,

                    color_gantt:  value.color_gantt,
                    color_gantt_set: value.color_gantt_set,

                    duration_scale: value.duration_scale,


                    summary_date_start: value.summary_date_start,
                    summary_date_end: value.summary_date_end,

                    subtask_project_id: value.subtask_project_id,
                    load_data_id: value.load_data_id,

                    parent_id: value.parent_id,
                    subtask_count: value.subtask_count,

                    date_done: value.date_done,
                    state: value.state,

                    fold_self: value.fold_self,
                    fold_child: value.fold_child,

                    critical_path: value.critical_path,
                    cp_shows: value.cp_shows,
                    cp_detail: value.cp_detail,

                    p_loop: value.p_loop,




                });

            }
            _.map(value.child_task, function(sub_task) {
                generate_flat_gantt(sub_task);
            });
        };


        //Generate Flat Gant to rows_to_gantt
        _.map(row_datas, function(result) {
           return generate_flat_gantt(result);
        });

        return rows_to_gantt;


    }


    function groupRows (tasks, group_bys, self_parent) {

        var parent = self_parent;
        var GtimeStopA  = [];
        var GtimeStartA = [];

        var model_fields_dict = parent.model_fields_dict;

        var gantt_attrs = parent.fields_view.arch.attrs;
        var second_sort = parent.gantt_data_second_sort;
        var main_group = parent.gantt_data_main_group;


       //prevent more that 1 group by
        //   if (group_bys.length > 0) {
        //       group_bys = [group_bys[0]];
        //   }


        // if there is no group by, simulate it
        if (group_bys.length === 0) {
            group_bys = ["_pseudo_group_by"];
            _.each(tasks, function(el) {
                el._pseudo_group_by = "Plain Gantt View";
            });
            this.fields._pseudo_group_by = {type: "string"};
        }


        var sort_fld = undefined;


        if (second_sort) {

            sort_fld = model_fields_dict["default_seq"];
            if (sort_fld) {
                tasks = _.sortBy(tasks, function (o) {
                    return o[sort_fld];
                });
            }
        }


        if (!second_sort) {

            sort_fld = model_fields_dict["sorting_seq"];
            if (sort_fld) {
                tasks = _.sortBy(tasks, function (o) {
                    return o[sort_fld];
                });
            }
        }


        // get the groups
        var split_groups = function(tasks, group_bys) {

            if (group_bys.length === 0)
                return tasks;
            var sp_groups = [];
            _.each(tasks, function(task) {
                var group_name = task[_.first(group_bys)];
                var group = _.find(sp_groups, function(group) { return _.isEqual(group.name, group_name); });
                if (group === undefined) {
                    group = {name:group_name, tasks: [], __is_group: true};
                   sp_groups.push(group);
                }
                group.tasks.push(task);
            });
            _.each(sp_groups, function(group) {
                group.tasks = split_groups(group.tasks, _.rest(group_bys));
            });
            return sp_groups;
        };

        var groups = split_groups(tasks, group_bys);

        //Sort by sequenses group if detect.
        if (second_sort) {

            var s_field = gantt_attrs["second_seq_field"];
            groups = _.map(groups, function (result) {

                var s_id = result["name"][0];
                var sort_element = _.findWhere(second_sort, {id: s_id});

                if (sort_element) {
                    result["sort_seq"] = sort_element[s_field];
                } else {
                    result["sort_seq"] = -1;
                }

                return result

            });


            groups = _.sortBy(groups, function (o) {
                return o["sort_seq"];
            });

        }

        if (main_group) {

            groups = _.map(groups, function (result) {

                var s_id = result["name"][0];
                var main_element = _.findWhere(main_group, {id: s_id});

                if (main_element) {
                    result["g_data"] = main_element;
                } else {
                    result["g_data"] = false;
                }

                return result

            });
        }



        var assign_to = [];
        // genrate task
        var generate_task_info = function(task, plevel) {
            var level = plevel || 0;
            if (task.__is_group) {
                assign_to = task.user_id;
                var task_infos = _.compact(_.map(task.tasks, function(sub_task) {
                    return generate_task_info(sub_task, level + 1);
                }));
                if (task_infos.length == 0)
                    return;

                var group_name = formats.format_value(task.name, parent.fields[group_bys[level]]);

                var fold_group = false;
                if (task.hasOwnProperty("g_data")) {
                    fold_group = task.g_data["fold_group"]
                }



                var task_count = task_infos.length;
                return {
                    is_group: task.__is_group,
                    group_info: task.name,
                    group_field: group_bys[level],
                    child_task:task_infos,
                    task_name:group_name,
                    level:level,
                    task_count: task_count,
                    fold_group: fold_group

                };
            } else {
                var  today = new Date();
                assign_to = task[model_fields_dict["user_id"]];

                var mp_level = task[model_fields_dict["mp_level"]];

                var sorting_level = task[model_fields_dict["sorting_level"]];
                var sorting_seq = task[model_fields_dict["sorting_seq"]];

                var subtask_project_id = task[model_fields_dict["subtask_project_id"]];
                var load_data_id = task[model_fields_dict["load_data_id"]];

                var parent_id = task[model_fields_dict["parent_id"]];
                var subtask_count = task[model_fields_dict["subtask_count"]];

                var task_name = false

                if('product_id' in task){
                    task_name = task.__name + ' - ' + task.product_id[1];
                }else{
                    task_name = task.__name
                }
                
                /*if('production_id' in task){
                    task_name = task.__name + ' - ' + task.product_id[1] + ' - ' + task.production_id[1];
                }else{
                    task_name = task.__name
                }*/

                var task_start = time.auto_str_to_date(task[model_fields_dict["date_start"]]);
                if (!task_start){
                    task_start = today
                }

                var task_stop = time.auto_str_to_date(task[model_fields_dict["date_stop"]]);
                if (!task_stop) {
                    task_stop = task_start
                }

                // My
                var planed_dt_st = time.auto_str_to_date(task[model_fields_dict["planed_dt_st"]]);
                if (!planed_dt_st){
                    planed_dt_st = today
                }
                var planed_dt_ed = time.auto_str_to_date(task[model_fields_dict["planed_dt_ed"]]);
                if (!planed_dt_ed) {
                    planed_dt_ed = planed_dt_st
                }

                var effective_dt_st = time.auto_str_to_date(task[model_fields_dict["effective_dt_st"]]);
                if (!effective_dt_st){
                    effective_dt_st = today
                }
                var effective_dt_ed = time.auto_str_to_date(task[model_fields_dict["effective_dt_ed"]]);
                if (!effective_dt_ed) {
                    effective_dt_ed = effective_dt_st
                }
                /**********/

                var date_deadline = time.auto_str_to_date(task[model_fields_dict["date_deadline"]]);
                if (!date_deadline){
                    date_deadline = false
                }

                var progress = task[model_fields_dict["progress"]];
                var is_milestone = task[model_fields_dict["is_milestone"]];
                var on_gantt = task[model_fields_dict["on_gantt"]];

                var project_id = undefined;
                try {
                     project_id = task[model_fields_dict["project_id"]][0];
                } catch (err) {}

                var default_seq = task[model_fields_dict["default_seq"]];

                var date_done = time.auto_str_to_date(task[model_fields_dict["date_done"]]);
                if (!date_done){
                    date_done = false
                }


                var constrain_date = time.auto_str_to_date(task[model_fields_dict["constrain_date"]]);
                if (!constrain_date){
                    constrain_date = false
                }

                var duration = task[model_fields_dict["duration"]];
                var real_duration = task[model_fields_dict["real_duration"]];
                // var planed_dt_st = task[model_fields_dict["planed_dt_st"]];
                // var planed_dt_ed = task[model_fields_dict["planed_dt_ed"]];
                // var effective_dt_st = task[model_fields_dict["effective_dt_st"]];
                // var effective_dt_ed = task[model_fields_dict["effective_dt_ed"]];
                var qty_prod = task[model_fields_dict["qty_prod"]];
                var qty_to_prod = task[model_fields_dict["qty_to_prod"]];
                var workcenter = task[model_fields_dict["workcenter"]];
                var wo_state = task[model_fields_dict["wo_state"]];
                var plan_duration = task[model_fields_dict["plan_duration"]];

                var plan_action = task[model_fields_dict["plan_action"]];

                var color_gantt_set = task[model_fields_dict["color_gantt_set"]];
                var color_gantt = task[model_fields_dict["color_gantt"]];

                var duration_scale = task[model_fields_dict["duration_scale"]];


                var summary_date_start = time.auto_str_to_date(task[model_fields_dict["summary_date_start"]]);
                if (!summary_date_start){
                    summary_date_start = false
                }

                var summary_date_end = time.auto_str_to_date(task[model_fields_dict["summary_date_end"]]);
                if (!summary_date_end){
                    summary_date_end = false
                }


                var schedule_mode = task[model_fields_dict["schedule_mode"]];
                var constrain_type = task[model_fields_dict["constrain_type"]];

                var state = task[model_fields_dict["state"]];

                var fold_self = task[model_fields_dict["fold_self"]];
                var fold_child = task[model_fields_dict["fold_child"]];

                var critical_path = task[model_fields_dict["critical_path"]];
                var cp_shows = task[model_fields_dict["cp_shows"]];
                var cp_detail = task[model_fields_dict["cp_detail"]];

                var p_loop = task[model_fields_dict["p_loop"]];


                try {
                     GtimeStopA.push(task_stop.getTime());
                } catch (err) {}

                try {
                     GtimeStartA.push(task_start.getTime());
                } catch (err) {}

                try {
                     GtimeStopA.push(date_done.getTime());
                     GtimeStartA.push(date_done.getTime());
                } catch (err) {}

                try {
                    GtimeStopA.push(date_deadline.getTime());
                    GtimeStartA.push(date_deadline.getTime());
                } catch (err) {}



                return {
                    id:task.id,
                    task_name: task_name,
                    task_start: task_start,
                    task_stop: task_stop,
                    level:level,
                    assign_to:assign_to,

                    mp_level : mp_level,

                    default_seq: default_seq,

                    sorting_level : sorting_level,
                    sorting_seq : sorting_seq,

                    project_id: project_id,

                    date_deadline: date_deadline,

                    progress: progress,

                    is_milestone: is_milestone,

                    constrain_date: constrain_date,
                    schedule_mode: schedule_mode,
                    constrain_type: constrain_type,

                    duration: duration,
                    real_duration:real_duration,
                    planed_dt_st:planed_dt_st,
                    planed_dt_ed: planed_dt_ed,
                    effective_dt_st:effective_dt_st,
                    effective_dt_ed:effective_dt_ed,
                    qty_prod:qty_prod,
                    qty_to_prod:qty_to_prod,
                    wo_state: wo_state,
                    workcenter:workcenter,
                    plan_duration: plan_duration,

                    plan_action: plan_action,

                    color_gantt_set: color_gantt_set,
                    color_gantt:  color_gantt,

                    duration_scale: duration_scale,

                    summary_date_start: summary_date_start,
                    summary_date_end: summary_date_end,

                    on_gantt: on_gantt,

                    subtask_project_id: subtask_project_id,
                    load_data_id: load_data_id,

                    parent_id: parent_id,
                    subtask_count: subtask_count,

                    date_done: date_done,
                    state: state,

                    fold_self: fold_self,
                    fold_child: fold_child,

                    critical_path: critical_path,
                    cp_shows: cp_shows,
                    cp_detail: cp_detail,

                    p_loop: p_loop

                };
            }
        }

        //generate projects info from groupby
        var projects = _.map(groups, function(result) {
           return generate_task_info(result, 0);
        });


        return {
            projects : projects,
            timestop : GtimeStopA,
            timestart : GtimeStartA

        }


    }

    return {
        flatRows: flatRows,
        groupRows: groupRows,
        getFields : getFields
    }

});
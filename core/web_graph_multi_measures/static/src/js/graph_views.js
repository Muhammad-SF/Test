/**
 * Created by trananhdung on 22/02/2018.
 */
odoo.define('web_graph_multi_measures.GraphWidgetExtend', function (require) {

    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;
    var data_manager = require('web.data_manager');
    var GraphWidget = require('web.GraphWidget');
    var GraphView = require('web.GraphView');
    var formats = require('web.formats');
    var config = require('web.config');

    var MAX_LEGEND_LENGTH = 25 * (1 + config.device.size_class);

    var ImprovedGraphWidget = GraphWidget.extend({
        init: function (parent, model, options) {
            this._super(parent, model, options);

            this.measures = [options.measure];
            this.datas = [];
        },

        set_measure: function (measure) {
            this.measure = measure;
            var self = this;
            if (this.measures.indexOf('__count__') < 0 && this.measure === '__count__')
                this.measures = ['__count__'];
            else {
                if (this.measures.indexOf('__count__') >= 0) {
                    this.measures = [];
                }
                if (self.groupbys.length > 1) {
                    self.measures = [self.measure];
                    return this.load_data();
                }
                if (self.measures.indexOf(self.measure) >= 0) {
                    self.measures.splice(self.measures.indexOf(self.measure), 1);
                }
                else {
                    self.measures.push(self.measure);
                }
            }

            return this.load_data();
        },

        load_data: function () {
            var index_measure = arguments[0] || 0;
            var fields = this.groupbys.slice(0);
            var self = this;
            if (this.measures[index_measure] !== '__count__'.slice(0))
                fields = fields.concat(this.measures[index_measure]);
            if (this.measures.length == 0) {
                this.datas = [];
                return this.display_graph();
            }
            if (index_measure < this.measures.length - 1) {
                return this.model
                    .query(fields)
                    .filter(this.domain)
                    .context(this.context)
                    .lazy(false)
                    .group_by(this.groupbys.slice(0, 2))
                    .then(function (result) {
                        self.prepare_data(result, index_measure);
                    });
            }
            else {
                return this.model
                    .query(fields)
                    .filter(this.domain)
                    .context(this.context)
                    .lazy(false)
                    .group_by(this.groupbys.slice(0, 2))
                    .then(function (result) {
                        self.prepare_data(result, index_measure);
                    }).then(this.proxy('display_graph'));
            }
        },

        prepare_data: function () {
            var raw_data = arguments[0],
                is_count = this.measure === '__count__',
                index_measures = arguments[1] || 0;
            var data_pt, j, values, value;

            if (index_measures === 0) {
                this.datas = [];  // clear old data
            }

            this.data = [];
            for (var i = 0; i < raw_data.length; i++) {
                data_pt = raw_data[i].attributes;
                values = [];
                if (this.groupbys.length === 1) data_pt.value = [data_pt.value];
                for (j = 0; j < data_pt.value.length; j++) {
                    var field = _.isArray(data_pt.grouped_on) ? data_pt.grouped_on[j] : data_pt.grouped_on;
                    values[j] = this.sanitize_value(data_pt.value[j], field);
                }
                value = is_count ? data_pt.length : data_pt.aggregates[this.measures[index_measures]];
                this.data.push({
                    labels: values,
                    value: value
                });
            }
            this.datas.push(this.data);
            if (index_measures < this.measures.length - 1) {
                this.load_data(index_measures + 1)
            }
        },

        _build_colors: function (n) {
            if (n === 1) {
                return ['#0000FF'];
            }

            var GColor = function (r, g, b) {
                r = (typeof r === 'undefined') ? 0 : r;
                g = (typeof g === 'undefined') ? 0 : g;
                b = (typeof b === 'undefined') ? 0 : b;
                return {r: r, g: g, b: b};
            };
            var createColorRange = function (c1, c2) {
                var colorList = [], tmpColor;
                for (var i = 0; i < 255; i++) {
                    tmpColor = new GColor();
                    tmpColor.r = c1.r + ((i * (c2.r - c1.r)) / 255);
                    tmpColor.g = c1.g + ((i * (c2.g - c1.g)) / 255);
                    tmpColor.b = c1.b + ((i * (c2.b - c1.b)) / 255);
                    colorList.push(tmpColor);
                }
                return colorList;
            };
            var colors = createColorRange({r: 0, g: 0, b: 255}, {r: 255, g: 255, b: 0}).concat(
                createColorRange({r: 0, g: 255, b: 255}, {r: 255, g: 0, b: 255})
            );
            var result = [],
                distance = parseInt(255 * 2 / (n - 1));
            for (var i = 0; i < n; i++) {
                var c = colors[i === 0 ? 0 : distance * i - 1];
                result.push('rgb(' + [c.r, c.g, c.b].join(',') + ')');
            }
            return result;
        },

        display_line: function () {
            if (this.datas.length === 0) {
                // this.$el[0].remove('svg');
                this.$el.append(QWeb.render('GraphView.error', {
                    title: _t("Not enough data points"),
                    description: "You need at least two data points to display a line chart."
                }));
                return;
            }
            var self = this,
                data = [],
                tickValues,
                tickFormat;
            // var colors = this._build_colors(this.datas.length);

            if (this.groupbys.length === 1) {
                _.each(this.datas, function (this_data, i) {
                    var values = this_data.map(function (datapt, index) {
                        return {x: index, y: datapt.value};
                    });

                    data.push({
                        values: values,
                        key: self.fields[self.measures[i]].string,
                        // color: colors[i],
                    });

                });
                tickValues = data.map(function (d, i, k) {
                    return i;
                });
                tickFormat = function (i) {
                    try {
                        return self.datas[0][i].labels;
                        // return data[d].key;
                    }
                    catch (e) {
                        console.log('sml');
                    }
                };

            }

            if (this.groupbys.length > 1) {
                data = [];
                var data_dict = {},
                    tick = 0,
                    tickLabels = [],
                    serie, tickLabel,
                    identity = function (p) {
                        return p;
                    };
                tickValues = [];
                _.each(this.datas, function (this_data) {
                    for (var i = 0; i < this_data.length; i++) {
                        if (this_data[i].labels[0] !== tickLabel) {
                            tickLabel = this_data[i].labels[0];
                            tickValues.push(tick);
                            tickLabels.push(tickLabel);
                            tick++;
                        }
                        serie = this_data[i].labels[1];
                        if (!data_dict[serie]) {
                            data_dict[serie] = {
                                values: [],
                                key: serie,
                            };
                        }
                        data_dict[serie].values.push({
                            x: tick, y: this_data[i].value,
                        });
                        data = _.map(data_dict, identity);
                    }
                    tickFormat = function (d) {
                        return tickLabels[d];
                    };
                });

            }

            var svg = d3.select(this.$el[0]).append('svg');

            // this._build_line_chart(svg);
            svg.datum(data);

            svg.transition().duration(0);

            var chart = nv.models.lineChart();
            chart.options({
                margin: {left: 120, bottom: 80, right: 40},
                useInteractiveGuideline: true,
                showLegend: _.size(data) <= MAX_LEGEND_LENGTH,
                showXAxis: true,
                showYAxis: true,
                color: d3.scale.category10().range(),
            });
            chart.xAxis.tickValues(tickValues)
                .tickFormat(tickFormat);
            chart.yAxis.tickFormat(function (d) {
                return formats.format_value(d, {
                    type: 'float',
                    digits: self.fields[self.measure] && self.fields[self.measure].digits || [69, 2],
                });
            });

            chart(svg);
            this.to_remove = chart.update;
            nv.utils.onWindowResize(chart.update);

            return chart;
        },

        display_bar: function () {
            // prepare data for bar chart
            var data = [], values,
                measure = this.fields[this.measure].string,
                self = this;
            // var colors = this._build_colors(this.datas.length);

            // zero groupbys
            if (this.groupbys.length === 0) {
                data = [{
                    values: [{
                        x: measure,
                        y: this.data[0].value
                    }],
                    key: measure
                }];
            }
            // one groupby
            if (this.groupbys.length === 1) {
                _.each(this.datas, function (this_data, i) {
                    values = this_data.map(function (datapt) {
                        return {x: datapt.labels, y: datapt.value};
                    });
                    data.push(
                        {
                            values: values,
                            key: self.fields[self.measures[i]].string
                        }
                    );
                });

            }
            if (this.groupbys.length > 1) {
                var xlabels = [],
                    series = [],
                    label, serie, value;
                values = {};
                for (var i = 0; i < this.data.length; i++) {
                    label = this.data[i].labels[0];
                    serie = this.data[i].labels[1];
                    value = this.data[i].value;
                    if ((!xlabels.length) || (xlabels[xlabels.length - 1] !== label)) {
                        xlabels.push(label);
                    }
                    series.push(this.data[i].labels[1]);
                    if (!(serie in values)) {
                        values[serie] = {};
                    }
                    values[serie][label] = this.data[i].value;
                }
                series = _.uniq(series);
                data = [];
                var current_serie, j;
                for (i = 0; i < series.length; i++) {
                    current_serie = {values: [], key: series[i]};
                    for (j = 0; j < xlabels.length; j++) {
                        current_serie.values.push({
                            x: xlabels[j],
                            y: values[series[i]][xlabels[j]] || 0,
                        });
                    }
                    data.push(current_serie);
                }
            }
            var svg = d3.select(this.$el[0]).append('svg');
            svg.datum(data);

            svg.transition().duration(0);

            var chart = nv.models.multiBarChart();
            chart.options({
                margin: {left: 120, bottom: 80, right: 40},
                delay: 250,
                transition: 10,
                showLegend: _.size(data) <= MAX_LEGEND_LENGTH,
                showXAxis: true,
                showYAxis: true,
                rightAlignYAxis: false,
                stacked: this.stacked,
                reduceXTicks: false,
                rotateLabels: -20,
                showControls: (this.groupbys.length > 1),
                color: d3.scale.category10().range(),
            });
            chart.yAxis.tickFormat(function (d) {
                return formats.format_value(d, {
                    type: 'float',
                    digits: self.fields[self.measure] && self.fields[self.measure].digits || [69, 2],
                });
            });

            chart(svg);
            this.to_remove = chart.update;
            nv.utils.onWindowResize(chart.update);

            return chart;
        },

    });

    var ImprovedGraphView = GraphView.extend({

        init: function () {
            this._super.apply(this, arguments);
            this.active_measures = [];
        },

        update_measure: function () {
            var self = this;

            if (this.active_measure === '__count__' && this.active_measures.indexOf('__count__') < 0) {
                this.active_measures = ['__count__'];
            }
            else {
                if (this.active_measures.indexOf('__count__') >= 0) {
                    this.active_measures = [];
                }
                if (this.widget.groupbys.length > 1) {
                    self.active_measures = [self.active_measure];
                }
                else {
                    if (self.active_measures.indexOf(self.active_measure) >= 0) {
                        self.active_measures.splice(self.active_measures.indexOf(self.active_measure), 1);
                    }
                    else {
                        self.active_measures.push(self.active_measure);
                    }
                }
            }


            this.$measure_list.find('li').each(function (index, li) {
                // $(li).toggleClass('selected', $(li).data('field') === self.active_measure);

                $(li).toggleClass('selected', self.active_measures.indexOf($(li).data('field')) >= 0);
            });
        },

        do_search: function (domain, context, group_by) {
            if (!this.widget) {
                this.initial_groupbys = context.graph_groupbys || (group_by.length ? group_by : this.initial_groupbys);
                this.widget = new ImprovedGraphWidget(this, this.model, {
                    measure: context.graph_measure || this.active_measure,
                    mode: context.graph_mode || this.active_mode,
                    domain: domain,
                    groupbys: this.initial_groupbys,
                    context: context,
                    fields: this.fields,
                    stacked: this.fields_view.arch.attrs.stacked !== "False"
                });
                // append widget
                this.widget.appendTo(this.$el);
            } else {
                var groupbys = group_by.length ? group_by : this.initial_groupbys.slice(0);
                this.widget.update_data(domain, groupbys);
            }
        }
    });

    var multi_measures_graph = {
        view: ImprovedGraphView,
        widget: ImprovedGraphWidget
    };

    core.view_registry.add('graph', ImprovedGraphView);

    return multi_measures_graph;
});

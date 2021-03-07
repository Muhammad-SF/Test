odoo.define('uppercrust_backend_theme.GraphRenderer', function (require) {
    "use strict";

    var GraphWidget = require('web.GraphWidget');
    var config = require('web.config');
    var core = require('web.core');
    var Model = require('web.DataModel');

    var data = require('web.data');
    var formats = require('web.formats');

    var _t = core._t;
    var QWeb = core.qweb;

    // hide top legend when too many items for device size
    var MAX_LEGEND_LENGTH = 25 * (1 + config.device.size_class);

    return GraphWidget.include({
        start: function () {
            var self = this;
            this.theme_colors = [];
            return this._super.apply(this, arguments);
        },
        _fetchThemeColors: function () {
            var self = this;
            return new Model('ir.config_parameter').call('get_param', ['uppercrust_backend_theme.selected_theme']).then(function (theme_id) {
                return new Model('ir.web.theme').call('search_read', [[['id', '=', parseInt(theme_id)]]], {'fields': ['leftbar_color', 'buttons_color', 'tag_info', 'tag_danger', 'tag_success', 'tag_warning', 'tag_primary', 'tag_muted']}).then(function (result) {
                    if(!_.isEmpty(result)){
                        self.theme_colors.push(result[0].buttons_color, result[0].leftbar_color, result[0].tag_info, result[0].tag_danger,
                                result[0].tag_success, result[0].tag_warning, result[0].tag_primary, result[0].tag_muted)
                    }
                });
            });
        },
        display_graph: function () {
            var self = this;
            if (this.to_remove) {
                nv.utils.offWindowResize(this.to_remove);
            }
            this.$el.empty();
            if (!this.data.length) {
                this.$el.append(QWeb.render('GraphView.error', {
                    title: _t("No data to display"),
                    description: _t("No data available for this chart. " +
                            "Try to add some records, or make sure that " +
                            "there is no active filter in the search bar."),
                }));
            } else {
                // var chart = this['display_' + this.mode]();
                // if (chart && chart.tooltip.chartContainer) {
                //     chart.tooltip.chartContainer(this.$el[0]);
                // }
                this._fetchThemeColors().then(function () {
                    var chart = self['display_' + self.mode]();
                    if (chart && chart.tooltip.chartContainer) {
                        chart.tooltip.chartContainer(self.$el[0]);
                    }
                });
            }
        },
        _processColors: function (n_elements) {
            return this.theme_colors;
        },
        display_bar: function () {
            // prepare data for bar chart
            var data, values,
                    measure = this.fields[this.measure].string,
                    self = this;

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
                values = this.data.map(function (datapt) {
                    return {x: datapt.labels, y: datapt.value};
                });
                data = [
                    {
                        values: values,
                        key: measure,
                    }
                ];
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
            var colors = this._processColors(this.data.length);
            var chart = nv.models.multiBarChart();
            chart.options({
                margin: {left: 120, bottom: 60},
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
                color: colors,
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
        display_pie: function () {
            var data = [],
                    all_negative = true,
                    some_negative = false,
                    all_zero = true;

            this.data.forEach(function (datapt) {
                all_negative = all_negative && (datapt.value < 0);
                some_negative = some_negative || (datapt.value < 0);
                all_zero = all_zero && (datapt.value === 0);
            });
            if (some_negative && !all_negative) {
                this.$el.append(QWeb.render('GraphView.error', {
                    title: _t("Invalid data"),
                    description: _t("Pie chart cannot mix positive and negative numbers. " +
                            "Try to change your domain to only display positive results"),
                }));
                return;
            }
            if (all_zero) {
                this.$el.append(QWeb.render('GraphView.error', {
                    title: _t("Invalid data"),
                    description: _t("Pie chart cannot display all zero numbers.. " +
                            "Try to change your domain to display positive results"),
                }));
                return;
            }
            if (this.groupbys.length) {
                data = this.data.map(function (datapt) {
                    return {x: datapt.labels.join("/"), y: datapt.value};
                });
            }
            var svg = d3.select(this.$el[0]).append('svg');
            svg.datum(data);

            svg.transition().duration(100);

            var legend_right = config.device.size_class > config.device.SIZES.XS;
            var colors = this._processColors(this.data.length);
            var chart = nv.models.pieChart();
            chart.options({
                delay: 250,
                showLegend: legend_right || _.size(data) <= MAX_LEGEND_LENGTH,
                legendPosition: legend_right ? 'right' : 'top',
                transition: 100,
                color: colors,
            });

            chart(svg);
            this.to_remove = chart.update;
            nv.utils.onWindowResize(chart.update);

            return chart;
        },
        display_line: function () {
            if (this.data.length < 2) {
                this.$el.append(QWeb.render('GraphView.error', {
                    title: _t("Not enough data points"),
                    description: "You need at least two data points to display a line chart."
                }));
                return;
            }
            var self = this,
                    data = [],
                    tickValues,
                    tickFormat,
                    measure = this.fields[this.measure].string;
            if (this.groupbys.length === 1) {
                var values = this.data.map(function (datapt, index) {
                    return {x: index, y: datapt.value};
                });
                data = [
                    {
                        values: values,
                        key: measure,
                        area: true,
                    }
                ];
                tickValues = this.data.map(function (d, i) {
                    return i;
                });
                tickFormat = function (d) {
                    return self.data[d].labels;
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
                for (var i = 0; i < this.data.length; i++) {
                    if (this.data[i].labels[0] !== tickLabel) {
                        tickLabel = this.data[i].labels[0];
                        tickValues.push(tick);
                        tickLabels.push(tickLabel);
                        tick++;
                    }
                    serie = this.data[i].labels[1];
                    if (!data_dict[serie]) {
                        data_dict[serie] = {
                            values: [],
                            key: serie,
                        };
                    }
                    data_dict[serie].values.push({
                        x: tick, y: this.data[i].value,
                    });
                    data = _.map(data_dict, identity);
                }
                tickFormat = function (d) {
                    return tickLabels[d];
                };
            }

            var svg = d3.select(this.$el[0]).append('svg');
            svg.datum(data);

            svg.transition().duration(0);

            var colors = this._processColors(this.data.length);
            var chart = nv.models.lineChart();
            chart.options({
                margin: {left: 120, bottom: 60},
                useInteractiveGuideline: true,
                showLegend: _.size(data) <= MAX_LEGEND_LENGTH,
                showXAxis: true,
                showYAxis: true,
                color: colors,
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
    });

});

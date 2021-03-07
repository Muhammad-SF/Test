odoo.define('sales_target_qty.sales_team_qty_tree_view', function (require) {
    "use strict";
    var core = require('web.core');
    var _t = core._t;

    var WidgetFieldTextSaleTarget = core.list_widget_registry.get('field').extend({
        _format: function(row_data, options) {
            var self = this;
            var value = row_data[self.id].value;
            var max_value = row_data['t_' + self.id].value;
            value  = value || 0.0;
            max_value = max_value || 0.0;
            var color = value >= max_value ? 'green' : 'red';
            return _.template('<div style="color: '+ color +';"><%-text%></div>')({
                text: value
            });
        }
    });
    core.list_widget_registry.add("field.saletarget", WidgetFieldTextSaleTarget);
});

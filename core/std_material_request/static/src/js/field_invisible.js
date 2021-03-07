odoo.define('std_material_request.main', function (require) {
    "use strict";
    var core = require('web.core');
    var ListView = require('web.ListView');
    var pyeval = require('web.pyeval');
    var Class = core.Class;
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;
    var list_widget_registry = core.list_widget_registry;
    var Model = require('web.Model');

    ListView.include({
        setup_columns: function (fields, grouped) {
            var self = this;
            this.columns.splice(0, this.columns.length);
            this.columns.push.apply(this.columns,
                _(this.fields_view.arch.children).map(function (field) {
                    var id = field.attrs.name;
                    return for_(id, fields[id], field);
            }));
            if (grouped) {
                this.columns.unshift(new ListView.MetaColumn('_group'));
            }

            if (this.columns.length > 0) {
                _.each(this.columns, function(col, index){
                    if (col.modifiers && col.modifiers.check_invisible_condition &&
                        self.getParent() && self.getParent().x2m && self.getParent().x2m.field_manager){
                        let check_condition = self.getParent().x2m.field_manager.compute_domain(col.modifiers.invisible);
                        col['invisible'] = check_condition ? '1' : '0';
                    }
                    else if (col.modifiers && col.modifiers.check_invisible_condition && 
                            col.modifiers.invisible){
                        var new_model = new Model(self.model, self.dataset.context, []);
                        new_model.call('check_invisible_condition').then(function(result) {
                            col['invisible'] = result.result == 'show' ? '0' : '1';
                        });
                    }
                });
            }

            this.visible_columns = _.filter(this.columns, function (column) {
                return column.invisible !== '1';
            });

            this.aggregate_columns = _(this.visible_columns).invoke('to_aggregate');
        },
    });

    function for_ (id, field, node) {
        var description = _.extend({tag: node.tag}, field, node.attrs);
        var tag = description.tag;
        var Type = list_widget_registry.get_any([
            tag + '.' + description.widget,
            tag + '.'+ description.type,
            tag
        ]);
        return new Type(id, node.tag, description);
    }
});
odoo.define('sg_account_standardisation.form_name_widget', function (require) {
"use strict";

var Model = require('web.DataModel');
var FieldChar = require('web.form_widgets').FieldChar;

var FieldCharExtend = FieldChar.include({
    render_value: function() {
        var tmp = this._super();
        var self = this
        if(self.name === "name" && self.view.dataset.model=='res.partner') {
            var model = new Model('res.partner');
            var customer = self.build_context().__eval_context.__contexts[1].customer
            var supplier = self.build_context().__eval_context.__contexts[1].supplier
            var dom = []
            if(customer && supplier){
                dom = []
            }else{
                if(customer){dom.push(['customer', '=', true])}
                if(supplier){dom.push(['supplier', '=', true])}
            }
            model.call("search_read", [dom, ['name']], {"context": self.build_context()}).then(function (result) {
                self.$el.easyAutocomplete({data: result,
                getValue: "name",
                list: {
                    match: {
                        enabled: true,
                        method: function(element, phrase) {
                            if (element !== false)
                                return (element.startsWith(phrase));
                            }
                        }
                }
                });
            });
        }
        return tmp
    },
});
});
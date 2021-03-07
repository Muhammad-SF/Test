odoo.define('uppercrust_backend_theme.form_widgets', function (require) {
    "use strict";

    var core = require('web.core');
    var form_widgets = require('web.form_widgets');
    var config = require('web.config');
    var Qweb = core.qweb;

    form_widgets.FieldStatus.include({
        className: "o_statusbar_status",
        render_value: function () {
            var self = this;
            var $content = $(Qweb.render("FieldStatus.content." + ((config.device.size_class <= config.device.SIZES.XS) ? 'mobile' : 'desktop'), {
                'widget': this,
                'value_folded': _.find(this.selection.folded, function (i) {
                    return i[0] === self.get('value');
                }),
            }));
            this.$el.empty().append($content.get().reverse());
        },
    });
});

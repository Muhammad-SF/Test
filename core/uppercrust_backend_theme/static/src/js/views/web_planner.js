odoo.define('uppercrust_backend_theme.planner', function (require) {
    "use strict";

    var core = require('web.core');
    var planner = require('web.planner');
    var QWeb = core.qweb;
    var _t = core._t;

    planner.PlannerLauncher.include({
        start: function () {
            var self = this;
            return self._super.apply(this, arguments).then(function() {
                return self.fetch_application_planner();
            }).then(function(apps) {
                self.$progress = self.$(".o_progress");
                self.$progress.tooltip({
                    html: true,
                    placement: 'bottom',
                    delay: {'show': 500}
                });
                return apps;
            });
        },
        update_parent_progress_bar: function (percent) {
            this.$progress.toggleClass("o_hidden", percent >= 100);
            this.$progress.addClass('p' + percent);
            this.$progress.find('.o_text').text(percent + '%');
        },
    });
});

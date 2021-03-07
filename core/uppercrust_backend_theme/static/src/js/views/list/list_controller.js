odoo.define('uppercrust_backend_theme.ListView', function (require) {
    "use strict";

    var core = require('web.core');
    var ListView = require('web.ListView');
    var _t = core._t;


    ListView.include({
        _doUpdateSidebar: function () {
            var $sidebar = $('body').find('.ad_rightbar');
            (this.groups.get_selection().ids.length > 0 && this.sidebar.$el.hasClass('o_drw_in')) ?
                    $sidebar.addClass('o_open_sidebar') : $sidebar.removeClass('o_open_sidebar');
        },
        do_select: function (ids, records, deselected) {
            this._super.apply(this, arguments);
            if (this.sidebar) {
                this.sidebar.$el.addClass('o_drw_in');
                this._doUpdateSidebar();
            }
        },
        do_show: function () {
            this._super();
            if (this.sidebar) {
                this.sidebar.$el.addClass('o_drw_in');
                this._doUpdateSidebar();
                this.sidebar.do_hide();
            }
        },
    });
});

odoo.define('uppercrust_backend_theme.ViewManager', function (require) {
    "use strict";

    var ViewManager = require('web.ViewManager');
    var config = require('web.config');

    ViewManager.include({
        _display_view: function (old_view) {
            if (this.active_view.type !== 'form' && this.active_view.type !== 'list') {
                $('body').find('.ad_rightbar').removeClass('o_open_sidebar');
            }
            return this._super.apply(this, arguments);
        },
        get_default_view: function () {
            var default_mobile_view = this._super.apply(this, arguments);
            if ((config.device.size_class <= config.device.SIZES.XS && !default_mobile_view.mobile_friendly) ||
                    (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) &&
                            !default_mobile_view.mobile_friendly)) {
                default_mobile_view = (_.find(this.views, function (v) {
                    return v.mobile_friendly;
                })) || default_mobile_view;
            }
            return default_mobile_view;
        },
    });
});
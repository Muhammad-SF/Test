// odoo Menu inherit menuge filter view option
// events view inherit
odoo.define('uppercrust_backend_theme.SearchView', function (require) {
    "use strict";

    var config = require('web.config');
    var SearchView = require('web.SearchView');
    var local_storage = require('web.local_storage');

    SearchView.include({
        init: function (parent, dataset, fvg, options) {
            this._super.apply(this, arguments);
            this.view = parent;
        },
        // events: _.extend({}, SearchView.prototype.events, {
        //     'click .o_searchview_more': function (e) {
        //         var self = this;
        //         $(e.target).toggleClass('fa-search-plus fa-search-minus');
        //         var visible_search_menu = (local_storage.getItem('visible_search_menu') !== 'true');
        //         local_storage.setItem('visible_search_menu', visible_search_menu);
        //         this.toggle_buttons();
        //         if (!$('body').hasClass('modal-open')) {
        //             if ($(e.target).hasClass('fa-search-plus')) {
        //                 $('body').find('.ad_rightbar').removeClass('ad_open_search')
        //             } else {
        //                 $('body').find('.ad_rightbar').addClass('ad_open_search');
        //             }
        //             if (!_.isUndefined(self.view.active_view) && self.view.active_view.type === 'graph') {
        //                 var graph_widget = self.view.active_view.controller.widget;
        //                 _.delay(function () {
        //                     return graph_widget.load_data().then(graph_widget.proxy('display_graph'));
        //                 }, 200);
        //             }
        //         }
        //     },
        // }),
        renderFacets: function (collection, model, options) {
            var self = this;
            this._super.apply(this, arguments);
            var search_area = 0;
            var device_width = window.innerWidth;
            _.each(this.input_subviews, function (childView) {
                if (childView.$el[0].localName !== 'input') {
                    search_area += childView.$el[0].clientWidth;
                }
                if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || config.device.size_class == config.device.SIZES.xs) {
                    if (search_area > (device_width - 240) && childView.$el[0].localName !== 'input') {
                        childView.$el.appendTo(self.$('.o_search_rec_ul'))
                    }
                } else {
                    if (search_area > ((device_width / 2) - 250) && childView.$el[0].localName !== 'input') {
                        childView.$el.appendTo(self.$('.o_search_rec_ul'))
                    }
                }
                if (!_.isEmpty(self.$('.o_search_rec_ul').html())) {
                    !self.$el.hasClass('open') ? self.$el.addClass('open') : false;
                    self.$('.o_search_recs').removeClass('hidden');
                    self.$('.o_search_rec_ul').removeClass('hidden');
                } else {
                    self.$('.o_search_recs').addClass('hidden');
                    self.$('.o_search_rec_ul').addClass('hidden');
                }
            });
        }
    });
});
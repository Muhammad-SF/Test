// odoo Controlpanel view inherit to manage view button.
// search option button click and default filter view active.
// control panel all view button wrap time active button status
// Using for print - action - attechment btn
odoo.define('uppercrust_backend_theme.ControlPanel', function (require) {
    "use strict";

    var ControlPanel = require('web.ControlPanel');
    var config = require('web.config');

    var SystrayMenu = require('web.SystrayMenu');
    var UserMenu = require('web.UserMenu');

    ControlPanel.include({
        events: {
            // search option button click
            // 'click .o_search_options .o_dropdown_toggler_btn': function (e) {
            //     var $searchoption = $('.o_search_options').children('.ad_active'), $clickbutton = $(e.target).parent();
            //     $searchoption.removeClass('ad_active');
            //     ($(e.target).parent().hasClass('o_dropdown')) ?
            //         $clickbutton.addClass('ad_active'): $clickbutton.parent().addClass('ad_active');
            // },
            // Using for print - action
            // 'click .o_cp_sidebar .o_dropdown_toggler_btn': function (e) {
            //     var $searchoption = $('.o_cp_sidebar .btn-group').children('.ad_active'), $clickbutton = $(e.target).parent();
            //     $('.o_cp_sidebar').addClass('ad_active');
            //     $searchoption.removeClass('ad_active');
            //     ($(e.target).parent().hasClass('o_dropdown')) ?
            //         $clickbutton.addClass('ad_active'): $clickbutton.parent().addClass('ad_active');
            // },
            // 'click .o_cp_buttons': function (e) {
            //     $(e.target).toggleClass('cp_open');
            // },
            // Using Toggle - action
            'click .o_cp_sidebar span.o_sidebar_drw': 'onSidebarToggle',
            'click #av_full_view': function (e) {
                if ($('body').hasClass('ad_full_view')) {
                    $('body').find('div.o_main').css({'margin-left':'65px'});
                }
                $('body').removeClass('nav-sm ad_open_childmenu').toggleClass('ad_full_view');
                if ($('body').hasClass('ad_full_view')) {
                    if ($('body').find('.o_uppercrust_submenu').hasClass('o_hidden')){
                        $('body').find('div.o_main').css({'margin-left':'0px'});
                    }
                    else {
                        $('body').find('div.o_main').css({'margin-left':'-225px'});
                    }
                }
            },
        },
      
       

        // Using Toggle - action
        onSidebarToggle: function (e) {
            $(e.target).toggleClass('fa-chevron-left fa-chevron-right');
            $(e.target).parents('.btn-group').toggleClass('o_drw_in');
            $(e.target).parents('.ad_rightbar').toggleClass('o_open_sidebar');
        },
        // control panel all view button wrap time active button status
        _update_switch_buttons: function (active_view_selector) {
            this._super.apply(this, arguments);
            if ($('body').find('.oe_user_menu_placeholder').length > 0 && 
                $('body').find('.oe_user_menu_placeholder > .o_user_menu').length == 0){
                let user_menu = new UserMenu(this);
                var $user_menu_placeholder = $('body').find('.oe_user_menu_placeholder').show();
                var user_menu_loaded = user_menu.appendTo($user_menu_placeholder);
            }
            if ($('body').find('.oe_systray').length > 0 &&
                $('body').find('.oe_systray > .o_global_search').length == 0){
                let systray_menu = new SystrayMenu(this);
                $('body').find('.oe_systray').show();
                 $('body').find('.oe_systray_debug').show();
                systray_menu.setElement($('body').find('.oe_systray'));
                var systray_menu_loaded = systray_menu.start();
            }

                if (this.nodes.$switch_buttons.find('button').length == 0){
                    $(".mobile_tablate_view_class").css("display", "none !important");
                    console.log("mmmmmmmmmmmmmmmmmmmmm",$(".mobile_tablate_view_class"))
                    
                }
                _.each(this.nodes.$switch_buttons.find('button'), function(button) {
                $(button).removeClass('active');
                // ===============add me=================
                $(button)[0].innerText = ''
            });
        this.$(active_view_selector).addClass('active');
            // Using for print - action - attechment btn
            var $active_class = active_view_selector.split('.').join("");
            if ($active_class) {
                $('#all_views_button').attr('class', $active_class);
            }
        },
        // control panel all view button wrap time active button status
        // Form view load time search option hidden- [start]
        _update_search_view: function (searchview, is_hidden) {
            this._super.apply(this, arguments);
            var self = this, $rightbar = $('body').find('.ad_rightbar');
            // var $search_options = $('.o_search_options');
            // For View hide if no view available
            // if ($('.oe_cp_view_btn button').length > 1) {
            //     $('.oe_cp_view_btn').removeClass('hidden');
            // } else {
            //     $('.oe_cp_view_btn').addClass('hidden');
            // }
            // ($search_options.is(':visible') && $search_options.children().length > 0) ?
            //     $rightbar.addClass('ad_open_search'): $rightbar.removeClass('ad_open_search');

            if ((/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) ||
                    (config.device.size_class < config.device.SIZES.SM)) {
                this.$el.addClass('ad_search_full');
            }

            // if (_.isUndefined(this.$enable_searchview)) {
            //     this.$enable_searchview = $('<button/>', {type: 'button'})
            //         .addClass('ad_mobile_searchview btn btn-sm btn-default fa fa-search')
            //         .on('click', function () {
            //             self.searchview_displayed = !self.searchview_displayed;
            //             self.$el.toggleClass('ad_search_full', !self.searchview_displayed);
            //         });
            // }
            // if ((!is_hidden && config.device.size_class <= config.device.SIZES.XS) ||
            //         (!is_hidden && (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)))) {
            //     self.$enable_searchview.insertAfter(self.nodes.$searchview);
            //     self.searchview_displayed = false;
            //     self.nodes.$searchview_buttons.hide();
            // } else {
            //     self.$enable_searchview.detach();
            // }
        },
        // ========================================================
        // ========================================================
    });
});
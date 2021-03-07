// odoo Menu inherit Open time has Children submenu add.
odoo.define('uppercrust_backend_theme.Menu', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var Menu = require('web.Menu');
    var UserMenu = require('web.UserMenu');
     var DataModel = require('web.DataModel');
    var QuickMenu = require('uppercrust_backend_theme.QuickMenu');
    var GlobalSearch = require('uppercrust_backend_theme.global_search');
    var config = require('web.config');
    var session = require('web.session');
    var local_storage = require('web.local_storage');
    var main_menu_serch =''
    var sub_menu_serch = ''
    var current_event = ''
    var Model = require('web.Model');
    require('mail.chat_client_action');

    core.action_registry.get('mail.chat.instant_messaging').include({
        start: function() {
            var parent = this._super(parent);
            $('body').find('.o_uppercrust_submenu').addClass('o_hidden');
            return parent;
        }
    });


    var LogoutMessage = Widget.extend({
        template: 'LogoutMessage',
        events: {
            'click  a.oe_cu_logout_yes': '_onClickLogout',
            'click  .mb-control-close': '_onClickClose',
        },
        init: function (parent) {
            this._super(parent);
        },
        _onClickLogout: function (e) {
            var self = this;
            self.getParent().on_menu_logout();
        },
        _onClickClose: function (e) {
            this.$el.remove();
        }
    });

    var MenuGlobalSearch = Widget.extend({
        template: 'menu.GlobalSearch',
        events: {
            'click  .oe_back_btn': '_closeGloblesearch',
            'click  ul.o_glonal_search_dropdown:not(.oe_back_btn)': '_onClickInside',
        },
        init: function (parent) {
            this._super(parent);
        },
        _closeGloblesearch: function (e) {
            e.preventDefault();
            e.stopPropagation();
            $(e.currentTarget).parents('.o_gb_search').removeClass('open');
        },
        _onClickInside: function (e) {
            e.preventDefault();
            e.stopPropagation();
            if (e.offsetX < this.$('.o_glonal_search_dropdown')[0].offsetWidth) {

                $(e.currentTarget).parents('.o_gb_search').addClass('open');
            } else {
                $(e.currentTarget).parents('.o_gb_search').removeClass('open');
            }
        },
    });

    UserMenu.include({
        start: function () {
            // this._super.apply(this, arguments);
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                var $avatar = self.$('.oe_topbar_avatar');
                var avatar_src = session.url('/web/image', {
                    model: 'res.users',
                    field: 'image',
                    id: session.uid,
                });
                $avatar.attr('src', avatar_src);
                self.$el.on('click', 'li a.o_menu_logout', function (ev) {
                    ev.preventDefault();
                    return new LogoutMessage(self).appendTo(self.$el.closest('body'));
                });
            });
        },
    });

    Menu.include({

        // $(document).on('keypress',function(e) {
        //     if(e.which == 13) {
        //         console.log("RRRRRRRRRRRRRRRR")
        //         alert('You pressed enter!');
        //     }
        // })
        // add me===========================
        init: function() {
            this._super.apply(this, arguments);
            this.$original_menu_list = $('#sidebar-menu');
            this.$search_menu_list = $('.menus_list');
            this.$searchInput = $('#appDrawerSearchInput');
            this.$searchMainMenu = $('#search-main-menu');
            this.$searchResultsContainer = $('#appDrawerSearchResults');
            this.$searchMainMenu = $('#search-main-menu');
            // this.$searchResultsContainer.click($.proxy(this.searchMenus, this));
            this.get_sub_menus();
            this.get_parent_menus();
            $('#appDrawerSearchInput').on("input", this.showFoundMenus.bind(this));
        },
        get_sub_menus: function(){
            var self = this;
            var Menus = new DataModel('ir.ui.menu');

            Menus.query(['action', 'display_name', 'id'])
                .filter([['parent_id', '!=', false],
                         ['action', '!=', false]
                         ])
                .all()
                .then(function(result) {
                    self.sub_menus = result;
                });
        },
        get_parent_menus: function(){
            var self = this;
            new Model('ir.ui.menu')
            .call('get_filter_top_menus', [])
            .then(function(result) {
                if (result && result.length > 0) {
                    self.parent_menus = result;
                }
                else {
                    self.parent_menus = [];
                }
            });
        },
        get_proper_data: function(data){
            let odd_list = data.length % 2 == 0 ? false : true;
            var final_list = []
            var empty_list = []
            for (var i=0; i < data.length; i++) {
                console.log(">>>", i)
                if (data[i].length %2 == 0){
                    if (empty_list.length > 0) {
                        final_list.push(data[i]);
                    }
                    else {
                        empty_list = [];
                        $.merge(empty_list, data[i]);
                        console.log(">>>>>>>", empty_list);
                    }
                }
                else{
                    $.merge(empty_list, data[i]);
                }
                if (empty_list.length % 2 == 0) {
                    final_list.push(empty_list);
                    empty_list = [];
                }
                if ((data.length - i) == 1 && empty_list.length > 0) {
                    final_list.push(empty_list);
                }
            }
            return final_list
        },
        showFoundMenus: function(event) {
            var self = this;
            var search_term = $(event.target).val();
            if(search_term){
                this.searching = true;
                this.$original_menu_list.hide();
                this.$search_menu_list.show();
                let filter_parent_menus = [];
                _.each(self.parent_menus, function(value, key){
                    let filter_data = value.filter(it => it.name && it.name.toLowerCase().includes(search_term.toLowerCase()));
                    if (filter_data && filter_data.length > 0) {
                        filter_parent_menus.push(filter_data);
                    }
                });
                if (filter_parent_menus && filter_parent_menus.length > 0) {
                    let parent_menus_proper_data = this.get_proper_data(filter_parent_menus);
                    main_menu_serch = core.qweb.render(
                            'AppDrawerMainMenuSearchResults',
                            {menus: parent_menus_proper_data})
                    self.$searchMainMenu.html(main_menu_serch);
                }
                let filter_sub_menus = this.sub_menus.filter(it => it.display_name && it.display_name.toLowerCase().includes(search_term.toLowerCase()));
                sub_menu_serch = core.qweb.render(
                            'AppDrawerMenuSearchResults',
                            {menus: filter_sub_menus,
                            }
                        )
                this.$searchResultsContainer
                    // Render the results
                    .html(
                       sub_menu_serch
                    );
                var $menuLinks = this.$searchResultsContainer.find('a');
                $menuLinks.click($.proxy(this.handleClickZones, this));
                if(current_event.keyCode == 13){
                    var link = $menuLinks.first()
                    $(link).get(0).click()
                    // $menuLinks.first().click()
                }
                // this.selectLink($menuLinks.first());
            }
            else{
                this.$original_menu_list.show();
                this.$search_menu_list.hide();
            }
        },
        handleClickZones: function() {
            // console.log("::::::::::::::::",$('#menu_toggle').hasClass('active'))
            $('.oe_back_btn').click()
            $('.o_sub_menu_content')
                .parent()
                .collapse('hide');
            $('.navbar-collapse').collapse('hide');
        },

        selectLink: function($link) {
            console.log("9999999999999999999",$link)
            $('.web-responsive-focus').removeClass('web-responsive-focus');
            if ($link) {
                $link.addClass('web-responsive-focus');
            }
        },
        // ============end=================================
        open_menu: function (id) {
            this._super.apply(this, arguments);
            var $clicked_menu, $sub_menu, $sub_menu_count, $body, $parent_menu;

            // If has childmenu visible button
            $body = $('body');
            $body.find('.oe_back_btn').trigger('click');
            this.$sub_menus = this.$el.parents().find('.o_sub_menu_content');
            $clicked_menu = this.$el.add(this.$sub_menus).find('a[data-menu=' + id + ']');
            if (this.$sub_menus.has($clicked_menu).length) {
                $sub_menu = $clicked_menu.parents('.oe_secondary_menu');
                $sub_menu_count = $sub_menu;
            } else {
                $sub_menu = this.$secondary_menus.find('.oe_secondary_menu[data-menu-parent=' + $clicked_menu.attr('data-menu') + ']');
                $sub_menu_count = $sub_menu.find('.ad_sub_menu');
            }

            // Show current sub menu
            this.$sub_menus.find('.oe_secondary_menu').hide();
            $sub_menu.show();

            // Main menu click time open child menu [start]
            $parent_menu = $('.menu_section').children('ul');
            $parent_menu.click(function () {
                var $has_click_menu = $(this).children('li').children('a').hasClass('oe_menu_toggler');
                if ($has_click_menu) {
                    $body.removeClass('nav-sm');
                    $('#menu_toggle').removeClass('active');
                }
                else {
                    $body.removeClass('nav-sm ad_open_childmenu ad_nochild');
                    $('#children_toggle').removeClass('active');
                    $('#menu_toggle').removeClass('active');
                }
            });
            this.$sub_menus.find('li').click(function () {
                var $click_child_menu = $(this).children('a').hasClass('oe_menu_leaf');
                if ($click_child_menu) {
                    $body.removeClass('nav-sm ad_open_childmenu ad_nochild');
                    $('#children_toggle').removeClass('active');
                    $('#menu_toggle').removeClass('active');
                    var windowWidth = window.matchMedia("(max-width: 700px)")
                    if (windowWidth.matches) {
                        $('body').addClass('ad_full_view');
                        $('body').find('div.o_main').css({'margin-left':'-225px'});
                    }
                    // if ((config.device.size_class <= config.device.SIZES.XS) || (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent))) {
                    //     $body.addClass('ad_full_view');
                    // }
                }
            });

            this.$sub_menus.find('.oe_secondary_menu_section').click(function () {
                var $oe_secondary_menu_section = $(this).children('a').hasClass('oe_menu_leaf')
                if ($oe_secondary_menu_section) {
                    $body.removeClass('nav-sm ad_open_childmenu ad_nochild');
                    $('#children_toggle').removeClass('active');
                    $('#menu_toggle').removeClass('active');
                    var windowWidth = window.matchMedia("(max-width: 700px)")
                    if (windowWidth.matches) {
                        $('body').addClass('ad_full_view');
                        $('body').find('div.o_main').css({'margin-left':'-225px'});
                    }
                    // if ((config.device.size_class <= config.device.SIZES.XS) || (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent))) {
                    //     $body.addClass('ad_full_view');
                    // }
                }
            });
            if ($('.o_main_content.ad_rightbar').hasClass('ad_open_search')) {
                local_storage.setItem('visible_search_menu', 'True');
            }
            // Hide/Show the Submenubar menu depending of the presence of sub-items
            $body.toggleClass('ad_nochild', !$sub_menu_count.children().length);

        },
        // bind_menu: function () {
        //     var self = this;
        //     this._super.apply(this, arguments);
            // this.$searchInput.focus()
            // new QuickMenu(self).appendTo(this.$el.parents('.o_web_client').find('.top_nav .ad_navbar'));
            // this.$el.parents('.o_web_client').find('.oe_systray li.o_global_search').remove();
            // new MenuGlobalSearch(self).appendTo(this.$el.parents('.o_web_client').find('.top_nav .o_quick_menu'));
            // new GlobalSearch(self).appendTo(this.$el.parents('.o_web_client').find('.top_nav .o_gb_search ul'));
        // },

    });
});
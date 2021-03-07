odoo.define('sync_uppercrust_debranding.UserMenu', function (require) {
    "use strict";

    var Model = require('web.Model');
    var session = require('web.session');

    var UserMenu = require('web.UserMenu');
    var documentation_url = '';
    var documentation_dev_url;
    var support_url;
    var account_title;
    var account_url;
    var hasmicro_url;
    var about_equip_url;

    UserMenu.include({
        on_menu_debug: function () {
            window.location = $.param.querystring(window.location.href, 'debug');
        },
        on_menu_debugassets: function () {
            window.location = $.param.querystring(window.location.href, 'debug=assets');
        },
        // =============add me===================
        on_menu_hasmicro: function () {
             hasmicro_url = "https://www.hashmicro.com"
             window.open(hasmicro_url, '_blank');
        },
        on_menu_about_equip: function () {
             about_equip_url = "https://www.equiperp.com"
             window.open(about_equip_url, '_blank');
        },
        
        // ===============end===================
        on_menu_quitdebug: function () {
            window.location.search = "?";
        },
        on_menu_documentation: function () {
            window.open(documentation_url, '_blank');
        },
        on_menu_documentation_dev: function () {
            window.open(documentation_dev_url, '_blank');
        },
        on_menu_support: function () {
            window.open(support_url, '_blank');
        },
        on_menu_account: function () {
            window.open(account_url, '_blank');
        },
        on_menu_lang: function (ev) {
            var self = this;
            var lang = ($(ev).data("lang-id"));
            new Model('res.users').call('write', [[session.uid], {'lang': lang}]).then(function () {
                self.do_action({
                    type: 'ir.actions.client',
                    res_model: 'res.users',
                    tag: 'reload_context',
                    target: 'current'
                });
            });
            return false;
        },
    });

    $(document).ready(function () {
        var self = this;
        var lang_list = '';
        setTimeout(function () {
            new Model('ir.config_parameter').call('search_read', [[['key', '=', 'sync_app_show_debug']], ['value']]).then(function (show) {
                if (show.length >= 1 && (show[0]['value'] == "False")) {
                    $('[data-menu="debug"]').parent().hide();
                    $('[data-menu="debugassets"]').parent().hide();
                    $('[data-menu="quitdebug"]').parent().hide();
                }
            });
            new Model('ir.config_parameter').call('search_read', [[['key', '=', 'sync_app_show_documentation']], ['value']]).then(function (show) {
                if (show.length >= 1 && (show[0]['value'] == "False"))
                    $('[data-menu="documentation"]').hide();
                else {
                    new Model('ir.config_parameter').call('search_read', [[['key', '=', 'sync_app_documentation_url']], ['value']]).then(function (res) {
                        if (res.length >= 1) {
                            _.each(res, function (item) {
                                documentation_url = item['value'];
                            });
                        }
                    });
                }
            });
            new Model('ir.config_parameter').call('search_read', [[['key', '=', 'sync_app_show_documentation_dev']], ['value']]).then(function (show) {
                if (show.length >= 1 && (show[0]['value'] == "False"))
                    $('[data-menu="documentation_dev"]').parent().hide();
                else {
                    new Model('ir.config_parameter').call('search_read', [[['key', '=', 'sync_app_documentation_dev_url']], ['value']]).then(function (res) {
                        if (res.length >= 1) {
                            _.each(res, function (item) {
                                documentation_dev_url = item['value'];
                            });
                        }
                    });
                }
            });
            new Model('ir.config_parameter').call('search_read', [[['key', '=', 'sync_app_show_support']], ['value']]).then(function (show) {
                if (show.length >= 1 && (show[0]['value'] == "False"))
                    $('[data-menu="support"]').parent().hide();
                else {
                    new Model('ir.config_parameter').call('search_read', [[['key', '=', 'sync_app_support_url']], ['value']]).then(function (res) {
                        if (res.length >= 1) {
                            _.each(res, function (item) {
                                support_url = item['value'];
                            });
                        }
                    });
                }
            });
            new Model('ir.config_parameter').call('search_read', [[['key', '=', 'sync_app_show_account']], ['value']]).then(function (show) {
                if (show.length >= 1 && (show[0]['value'] == "False"))
                    $('[data-menu="account"]').parent().hide();
                else {
                    new Model('ir.config_parameter').call('search_read', [[['key', '=', 'sync_app_account_title']], ['value']]).then(function (res) {
                        if (res.length >= 1) {
                            _.each(res, function (item) {
                                account_title = item['value'];
                            });
                        }
                        // ===============below comment me and add me ===========
                        $('[data-menu="account"]').html();
                        // $('[data-menu="account"]').html(account_title);
                    });
                }
            });
            new Model('ir.config_parameter').call('search_read', [[['key', '=', 'sync_app_account_url']], ['value']]).then(function (res) {
                if (res.length >= 1) {
                    _.each(res, function (item) {
                        account_url = item['value'];
                    });
                }
            });
            new Model('ir.config_parameter').call('search_read', [[['key', '=', 'sync_app_show_poweredby']], ['value']]).then(function (show) {
                if (show.length >= 1 && (show[0]['value'] == "False"))
                    $('.o_sub_menu_footer').hide();
            });
            new Model('res.lang').call('search_read', [[], ['name', 'code']]).then(function (res) {
                _.each(res, function (lang) {
                    var a = '';
                    if (lang['code'] === session.user_context.lang) {
                        a = '<i class="fa fa-check"></i>';
                    } else {
                        a = '';
                    }
                    lang_list += '<li><a href="#" data-menu="lang" data-lang-id="' + lang['code'] + '"><img class="flag" src="sync_uppercrust_debranding/static/src/img/flags/' + lang['code'] + '.png"/>' + lang['name'] + a + '</a></li>';
                });
                lang_list += '<li class="divider"></li>';
                $('switch-lang').replaceWith(lang_list);
            });
        }, 2500);
    });
});

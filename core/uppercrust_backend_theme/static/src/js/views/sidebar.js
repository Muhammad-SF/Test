odoo.define('uppercrust_backend_theme.Attachments', function (require) {
    "use strict";

    var core = require('web.core');
    var Sidebar = require('web.Sidebar');

    var QWeb = core.qweb;

    Sidebar.include({
        redraw: function () {
            console.log("%%%%%%%%%%%%%%%%%%%%%%5",this)
            this.$el.html(QWeb.render('Sidebar', {widget: this}));
            var self = this, flag = true;
            // Hides Sidebar sections when item list is empty
            this.$('.o_dropdown').each(function () {
                $(this).toggle(!!$(this).find('li').length);
                if (flag && $(this).find('li').length) {
                    $(this).addClass('ad_active open');
                    flag = false;
                }
            });
            this.$("[title]").tooltip({
                delay: {show: 500, hide: 0}
            });
            this.$('.o_sidebar_add_attachment .o_form_binary_form').change(this.on_attachment_changed);
            this.$('.o_sidebar_delete_attachment').click(this.on_attachment_delete);
            this.$('button.o_dropdown_toggler_btn').on('click', function (e) {
                self.$('.o_dropdown').removeClass('ad_active');
                $(e.target).parent().addClass('ad_active');
            });
        },
    });

});

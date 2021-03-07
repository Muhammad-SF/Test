odoo.define('uppercrust_backend_theme.ChatWindow', function (require) {
    "use strict";

    var ChatWindow = require('mail.ChatWindow');

    ChatWindow.include({
        start: function () {
            this._super.apply(this, arguments);
            this.$body = $('body');
            this.$body.addClass('ad-chat-window');
        },
        on_click_close: function (event) {
            event.stopPropagation();
            event.preventDefault();
            if ((this.$body.find('.o_chat_window').length - 1) === 0) {
                this.$body.removeClass('ad-chat-window');
            }
            this.trigger("close_chat_session");
        },
    });

});

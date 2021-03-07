odoo.define('sync_uppercrust_debranding.web_settings_dashboard', function (require) {
    "use strict";
    var dashboad = require("web_settings_dashboard");

    dashboad.DashboardShare.include({
        init: function(parent, data){
            this._super(parent, data);
        },
        share_twitter: function(){
            var popup_url = _.str.sprintf( 'https://twitter.com/');
            this.sharer(popup_url);
        },
        share_facebook: function(){
            var popup_url = _.str.sprintf('https://www.facebook.com/');
            this.sharer(popup_url);
        },
        share_linkedin: function(){
            var popup_url = _.str.sprintf('http://www.linkedin.com/');
            this.sharer(popup_url);
        },
    });
});
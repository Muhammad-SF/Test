odoo.define('uppercrust_backend_theme.PivotView', function (require) {
    "use strict";

    var core = require('web.core');
    var Sidebar = require('web.Sidebar');
    var PivotView = require('web.PivotView');

    var ThemePivotView = PivotView.extend({
        render_sidebar: function ($node) {
            if (this.xlwt_installed && $node && this.options.sidebar) {
                this.sidebar = new Sidebar(this, {editable: this.is_action_enabled('edit')});
                this.sidebar.appendTo($node);
                if (this.sidebar.$el.find('.o_dropdown').is(':hidden')) {
                    this.sidebar.$el.find('.o_sidebar_drw').hide();
                }
            }
        },
        on_cell_click: function (event) {
            var $target = $(event.target);
            var self = this
            if ($target.hasClass('o_pivot_cell_value')) {
                if (typeof this.domain == 'object'){
                    if (self.domain.hasOwnProperty('__domains')){
                        self.domain = self.domain['__domains'][0]
                    }
                    
                
                }
                
                
            }
            return this._super.apply(this, arguments);
        }
    });

    core.view_registry.add('pivot', ThemePivotView);

    return ThemePivotView;

});

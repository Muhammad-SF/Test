odoo.define('sales_form_view_equip.form_custom_view', function (require) {
    "use strict";

    var core = require('web.core');
    var FormView = require('web.FormView');
    var Model = require('web.Model');
    var _t = core._t;
    var FormView = FormView.include({
        _actualize_mode: function(switch_to){
            var self = this;
            var mode = switch_to || this.get("actual_mode");
	    if (! this.datarecord.id) {
		    mode = "create";
	    } else if (mode === "create") {
		    mode = "edit";
	    }

	    var viewMode = (mode === "view");
	    this.$el.toggleClass('o_form_readonly', viewMode).toggleClass('o_form_editable', !viewMode);
	    if (viewMode && this.dataset.model === 'res.partner'){
	        this.$el.toggleClass('o_form_view', viewMode).toggleClass('o_web_custom_form', viewMode);
		this.$el.find('.o_form_sheet_bg', viewMode).toggleClass('o_form_sheet_bg', viewMode).toggleClass('o_sheet_custom', viewMode);
	        this.$el.find('.oe_chatter').toggleClass('oe_chatter', viewMode).toggleClass('o_web_custom_chatter', viewMode);
		this.$el.find('.oe_title').toggleClass('oe_title', viewMode).toggleClass('o_title_custom', viewMode);
	    }
	    if(viewMode && this.dataset.model === 'crm.lead'){
		this.$el.toggleClass('o_form_view', viewMode).toggleClass('o_web_custom_form_lead', viewMode);
		this.$el.find('.o_form_sheet_bg', viewMode).toggleClass('o_form_sheet_bg', viewMode).toggleClass('o_sheet_custom', viewMode);
	        this.$el.find('.oe_chatter').toggleClass('oe_chatter', viewMode).toggleClass('o_web_custom_chatter_lead', viewMode);
	    }
            this.render_value_defs = [];
	    this.set({actual_mode: mode});

	    if(!viewMode) {
	    	this.autofocus();
	    }
        }
    });
});


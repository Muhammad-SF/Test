odoo.define('sg_account_standardisation.move_line_quickaddd', function (require) {
"use strict";
var core = require('web.core');
var data = require('web.data');
var ListView = require('web.ListView');
var Model = require('web.DataModel');

var QWeb = core.qweb;

var QuickAddListView = ListView.include({
    init: function() {
        this._super.apply(this, arguments);
        this.journals = [];
        this.periods = [];
        this.current_journal = null;
        this.current_period = null;
        this.current_journal_type = null;
    },
    start:function(){
        var self = this;
        var tmp = this._super.apply(this, arguments);
        
        if(self.model=='account.move.line' && this.options['search_view']){
            var defs = [];
            this.$el.parent().prepend(QWeb.render("AccountMoveLineQuickAdd", {widget: this}));
            
            this.$el.parent().find('.oe_account_select_journal').change(function() {
                    self.current_journal = this.value === '' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
            this.$el.parent().find('.oe_account_select_period').change(function() {
                    self.current_period = this.value === '' ? null : parseInt(this.value);
                    self.do_search(self.last_domain, self.last_context, self.last_group_by);
                });
        }
        return tmp;
    },
    do_search: function(domain, context, group_by) {
        var self = this;
        if(self.model=='account.move.line' && this.options['search_view']){
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            var o;
            self.$el.parent().find('.oe_account_select_journal').children().remove().end();
            self.$el.parent().find('.oe_account_select_journal').append(new Option('', ''));
            var mod = new Model("account.move.line", self.dataset.context, self.dataset.domain);
            mod.call("list_journals", []).then(function(result) {
                for (var i = 0;i < result.length;i++){
                    self.journals = result
                    o = new Option(self.journals[i][1], self.journals[i][0]);
                    if (self.journals[i][0] === self.current_journal){
                        self.current_journal_type = self.journals[i][2];
                        $(o).attr('selected',true);
                    }
                    self.$el.parent().find('.oe_account_select_journal').append(o);                    
                }});
            self.$el.parent().find('.oe_account_select_period').children().remove().end();
            self.$el.parent().find('.oe_account_select_period').append(new Option('', ''));
            var year = (new Date()).getFullYear()
            for (var i = 0;i < 12;i++){
                o = new Option(String(i+1) + ' / '+ String(year),i);
                self.$el.parent().find('.oe_account_select_period').append(o);
            }    
            self.$el.parent().find('.oe_account_select_period').val(self.current_period).attr('selected',true);
            domain = self.search_by_journal_period();
            return self._super(domain, context, group_by)
        }
        return this._super.apply(this, arguments);
    },
    search_by_journal_period: function() {
        var self = this;
        var domain = [];
        if (self.current_journal){ domain.push(["journal_id", "=", self.current_journal])};
        if (self.current_period !== null) {
            var year = (new Date()).getFullYear()
            var firstDay = new Date(year, self.current_period, 1);
            var lastDay = new Date(year, self.current_period + 1, 0);
            domain.push(["date", ">=", firstDay])
            domain.push(["date", "<=", lastDay])
        };
        self.last_context["journal_id"] = self.current_journal? self.current_journal:false;
        self.last_context["journal_type"] = self.current_journal_type;
        var compound_domain = new data.CompoundDomain(self.last_domain, domain);
        self.dataset.domain = compound_domain.eval();
        return self.dataset.domain
    },
});

});

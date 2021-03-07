odoo.define('secondary_currency_of_accounting_report.main', function (require) {
'use strict';

var core = require('web.core');
var formats = require('web.formats');
var Model = require('web.Model');
var time = require('web.time');
var Dialog = require('web.Dialog');
var session = require('web.session');
var crash_manager = require('web.crash_manager');
var _t = core._t;
var QWeb = core.qweb;
var account_report_generic = require('account_reports.account_report_generic');

account_report_generic.include({
    render_searchview_buttons: function() {
        var self = this;
        var report_context_new ={}
        // Render the searchview buttons and bind them to the correct actions
        this.$searchview_buttons = $(QWeb.render("accountReports.searchView", {report_type: this.report_type, context: this.report_context}));
        var $dateFilter = this.$searchview_buttons.siblings('.o_account_reports_date-filter');
        var $dateFilterCmp = this.$searchview_buttons.siblings('.o_account_reports_date-filter-cmp');
        var $useCustomDates = $dateFilter.find('.o_account_reports_use-custom');
        var $CustomDates = $dateFilter.find('.o_account_reports_custom-dates');
        $useCustomDates.bind('click', function () {self.toggle_filter($useCustomDates, $CustomDates);});
        var $usePreviousPeriod = $dateFilterCmp.find('.o_account_reports_use-previous-period');
        var $previousPeriod = $dateFilterCmp.find('.o_account_reports_previous-period');
        $usePreviousPeriod.bind('click', function () {self.toggle_filter($usePreviousPeriod, $previousPeriod);});
        var $useSameLastYear = $dateFilterCmp.find('.o_account_reports_use-same-last-year');
        var $SameLastYear = $dateFilterCmp.find('.o_account_reports_same-last-year');
        $useSameLastYear.bind('click', function () {self.toggle_filter($useSameLastYear, $SameLastYear);});
        var $useCustomCmp = $dateFilterCmp.find('.o_account_reports_use-custom-cmp');
        var $CustomCmp = $dateFilterCmp.find('.o_account_reports_custom-cmp');
        $useCustomCmp.bind('click', function () {self.toggle_filter($useCustomCmp, $CustomCmp);});

        var $partnerFilter = this.$searchview_buttons.siblings('.o_account_reports_partner-filter');
        this.$searchview_buttons.find('.o_search_partner').bind('click', function (event) {
            var report_context = {};
            var value = $(event.target).parents('li').data('value');
            if(self.report_context.partner_ids.indexOf(value) === -1){
                report_context.add_partner_ids = value;
            }
            else {
                report_context.remove_partner_ids = value;
            }
            // Apply currency filter
             if (self.given_context && self.given_context['filter_original_currency'] == true) {
                 report_context.filter_original_currency = true;
             }else{
                 report_context.filter_original_currency = 0;
                 report_context.filter_local_currency = true;
             }
            self.restart(report_context);
        });

        /* Analytic Filter */
        var $levelFilter = this.$searchview_buttons.siblings('.o_account_reports_analytic_levels');
        this.$searchview_buttons.find('.o_search_analytic_level').bind('click', function (event) {
            var report_context = {};
            var value = $(event.target).parents('li').data('value');
            if(self.report_context.selected_analytic_level_id === value){
                report_context.analytic_level_id = false;
            }
            else {
                report_context.analytic_level_id = value;
            }
            self.restart(report_context);
        });

        var $partnerFilter = this.$searchview_buttons.siblings('.o_account_reports_tax_filter');
        this.$searchview_buttons.find('.o_search_tax').bind('click', function (event) {
            var report_context = {};
            var value = $(event.target).parents('li').data('value');
            if(self.report_context.tax_ids.indexOf(value) === -1){
                report_context.add_tax_ids = value;
            }
            else {
                report_context.remove_tax_ids = value;
            }
            self.restart(report_context);
        });

        this.$searchview_buttons.find('.o_search_change_currency').bind('click', function (event) {
            var report_context = {};
            var value = $(event.target).parents('li').data('value');
            var old_currency = self.report_context.change_currency_id
            if(self.report_context.change_currency_id == value){

                report_context.currency_remove_change_currency_id = value;
            }
            else {
                report_context.update_change_currency_id = value;
                report_context.old_update_current_currency_id = old_currency;
            }
            self.restart(report_context);
        });

        this.$searchview_buttons.find('.o_search_currency').bind('click', function (event) {
            var report_context = {};

            var value = $(event.target).parents('li').data('value');
            if(self.report_context.currency_ids.indexOf(value) === -1){
                report_context.add_currency_ids = value;
            }
            else {
                report_context.remove_currency_ids = value;
            }
            // Apply currency filter
             if (self.given_context && self.given_context['filter_original_currency'] == true) {
                 report_context.filter_original_currency = true;
             }else{
                 report_context.filter_original_currency = 0;
                 report_context.filter_local_currency = true;
             }
            self.restart(report_context);
        });

        //Forecast Filter Changes
        this.$searchview_buttons.find('.o_search_forecast_filter').bind('click', function (event) {
            var report_context = {};
            var value = $(event.target).parents('li').data('value');
            if(self.report_context.forecast_report === value){
                report_context.forecast_report = false;
            }
            else {
                report_context.forecast_report = value;
            }
            console.log('Report Forecast Context : ', value)
            self.restart(report_context);
        });

        this.$searchview_buttons.find('li.o_search_aging').bind('click', function (event) {
             var report_context = {};
             // Aging filter
             if (self.given_context && self.given_context['aging_filter_cmp'] == true) {
                 report_context.aging_filter_cmp = 0;
             }else{
                 report_context.aging_filter_cmp = true;
                 report_context.aging_due_filter_cmp = 0;
             }
             // Apply currency filter
             if (self.given_context && self.given_context['filter_original_currency'] == true) {
                 report_context.filter_original_currency = true;
             }else{
                 report_context.filter_original_currency = 0;
                 report_context.filter_local_currency = true;
             }
             self.restart(report_context);
        });

        this.$searchview_buttons.find('li.o_search_due_aging').bind('click', function (event) {
             var report_context = {};
             // Due aging filter
             if (self.given_context && self.given_context['aging_due_filter_cmp'] == true) {
                 report_context.aging_due_filter_cmp = 0;
             }else{
                 report_context.aging_due_filter_cmp = true;
                 report_context.aging_filter_cmp = 0;
             }
             // Apply currency filter
             if (self.given_context && self.given_context['filter_original_currency'] == true) {
                 report_context.filter_original_currency = true;
             }else{
                 report_context.filter_original_currency = 0;
                 report_context.filter_local_currency = true;
             }
             self.restart(report_context);
        });

        this.$searchview_buttons.find('li.o_search_local_currency').bind('click', function (event) {
             var report_context = {};
             // Aging filter
             if (self.given_context && self.given_context['aging_filter_cmp'] == true) {
                 report_context.aging_filter_cmp = true;
             }else{
                 report_context.aging_filter_cmp = 0;
             }
             // Due aging filter
             if (self.given_context && self.given_context['aging_due_filter_cmp'] == true) {
                 report_context.aging_due_filter_cmp = true;
             }else{
                 report_context.aging_due_filter_cmp = 0;
             }
             // Local currency filter
             if (self.given_context && self.given_context['filter_local_currency'] == true) {
                 report_context.filter_local_currency = 0;
             }else{
                 report_context.filter_local_currency = true;
             }
             self.restart(report_context);
        });

        this.$searchview_buttons.find('li.o_search_original_currency').bind('click', function (event) {
             var report_context = {};
             // Aging filter
             if (self.given_context && self.given_context['aging_filter_cmp'] == true) {
                 report_context.aging_filter_cmp = true;
             }else{
                 report_context.aging_filter_cmp = 0;
             }
             // Due aging filter
             if (self.given_context && self.given_context['aging_due_filter_cmp'] == true) {
                 report_context.aging_due_filter_cmp = true;
             }else{
                 report_context.aging_due_filter_cmp = 0;
             }
             // Original currency filter
             if (self.given_context && self.given_context['filter_original_currency'] == true) {
                 report_context.filter_original_currency = 0;
             }else{
                 report_context.filter_original_currency = true;
             }
             self.restart(report_context);
        });

        this.$searchview_buttons.find('.o_account_reports_one-filter').bind('click', function (event) {
            self.onChangeDateFilter(event); // First trigger the onchange
            var error = false;
            $('.o_account_reports_datetimepicker input').each(function () { // Parse all the values of the date pickers
                if (error) {return;}
                if ($(this).val() === ""){
                    crash_manager.show_warning({data: {message: _t('Date cannot be empty')}});
                    error = true
                    return;
                }
                $(this).val(formats.parse_value($(this).val(), {type: 'date'}));
            });
            if (error) {return;}
            var report_context = { // Create the context that will be given to the restart method
                date_filter: $(event.target).parents('li').data('value'),
                date_from: self.$searchview_buttons.find("input[name='date_from']").val(),
                date_to: self.$searchview_buttons.find("input[name='date_to']").val(),
            };
            if (self.date_filter_cmp !== 'no_comparison') { // Add elements to the context if needed
                report_context.date_from_cmp = self.$searchview_buttons.find("input[name='date_from_cmp']").val();
                report_context.date_to_cmp = self.$searchview_buttons.find("input[name='date_to_cmp']").val();
            }
            // Apply currency filter
             if (self.given_context && self.given_context['filter_original_currency'] == true) {
                 report_context.filter_original_currency = true;
             }else{
                 report_context.filter_original_currency = 0;
                 report_context.filter_local_currency = true;
             }
            self.restart(report_context); // Then restart the report
        });
        this.$searchview_buttons.find('.o_account_reports_one-filter-cmp').bind('click', function (event) { // Same for the comparison filter
            self.onChangeCmpDateFilter(event);
            $('.o_account_reports_datetimepicker input').each(function () {
                $(this).val(formats.parse_value($(this).val(), {type: 'date'}));
            });
            var filter = $(event.target).parents('li').data('value');
            var report_context = {
                date_filter_cmp: filter,
                date_from_cmp: self.$searchview_buttons.find("input[name='date_from_cmp']").val(),
                date_to_cmp: self.$searchview_buttons.find("input[name='date_to_cmp']").val(),
            };
            if (filter === 'previous_period' || filter === 'same_last_year') {
                report_context.periods_number = $(event.target).siblings("input[name='periods_number']").val();
            }
            // Apply currency filter
             if (self.given_context && self.given_context['filter_original_currency'] == true) {
                 report_context.filter_original_currency = true;
             }else{
                 report_context.filter_original_currency = 0;
                 report_context.filter_local_currency = true;
             }
            self.restart(report_context);
        });
        this.$searchview_buttons.find('.o_account_reports_one-filter-bool').bind('click', function (event) { // Same for the boolean filters
            var report_context = {};
            report_context[$(event.target).parents('li').data('value')] = !$(event.target).parents('li').hasClass('selected');
            self.restart(report_context);
        });
        this.$searchview_buttons.find('.o_account_reports_show').bind('click', function (event) {
            var report_context = {};
            report_context.show_all = true;
            self.restart(report_context);
        });
        this.$searchview_buttons.find('.o_account_reports_hide').bind('click', function (event) {
            var report_context = {};
            report_context.show_all = false;
            self.restart(report_context);
        });

        //for consolidate reports
        this.$searchview_buttons.find('.o_account_consolidate_reports').bind('click', function (event) {
            var report_context = {};
            report_context.consolidate_report = false;
            self.restart(report_context);
        });
        this.$searchview_buttons.find('.o_account_consolidate_reports_no').bind('click', function (event) {
            var report_context = {};
            report_context.consolidate_report = true;
            self.restart(report_context);
        });

//        this.$searchview_buttons.find('.o_account_reports_forecast').bind('click', function (event) {
//            var report_context = {};
//            report_context.forecast_report = false;
//            self.restart(report_context);
//        });
//        this.$searchview_buttons.find('.o_account_reports_no_forecast').bind('click', function (event) {
//            var report_context = {};
//            report_context.forecast_report = true;
//            self.restart(report_context);
//        });
        this.$searchview_buttons.find('li.o_search_tax_report_unpost').bind('click', function (event) {
            var report_context = {};
            report_context.tax_report_unpost = !self.report_context.tax_report_unpost;
            self.restart(report_context);
        });
        this.$searchview_buttons.find('li.o_search_tax_report_post').bind('click', function (event) {
            var report_context = {};
            report_context.tax_report_post = !self.report_context.tax_report_post;
            self.restart(report_context);
        });
        if (this.report_context.multi_company) { // Same for th ecompany filter
            this.$searchview_buttons.find('.o_account_reports_one-company').bind('click', function (event) {
                var report_context = {};
                var value = $(event.target).parents('li').data('value');
                if(self.report_context.company_ids.indexOf(value) === -1){
                    report_context.add_company_ids = value;
                }
                else {
                    report_context.remove_company_ids = value;
                }
                self.restart(report_context);
            });
        }
        if (this.report_context.journal_ids) { // Same for the journal
            this.$searchview_buttons.find('.o_account_reports_one-journal').bind('click', function (event) {
                var report_context = {};
                var value = $(event.target).parents('li').data('value');
                if(self.report_context.journal_ids.indexOf(value) === -1){
                    report_context.add_journal_ids = value;
                }
                else {
                    report_context.remove_journal_ids = value;
                }
                self.restart(report_context);
            });
        }
        if (this.report_context.account_ids) { // Same for the account
            this.$searchview_buttons.find('.o_account_reports_one-account').bind('click', function (event) {
                var report_context = {};
                var value = $(event.target).parents('li').data('value');
                if(self.report_context.account_ids.indexOf(value) === -1){
                    report_context.add_account_ids = value;
                }
                else {
                    report_context.remove_account_ids = value;
                }
                self.restart(report_context);
            });
        }
        if (this.report_context.account_type) { // Same for the account types
            this.$searchview_buttons.find('.o_account_reports_one-account_type').bind('click', function (event) {
                var value = $(event.target).parents('li').data('value');
                self.restart({'account_type': value});
            });
        }
        //Changes For Account Selection
        if (this.report_type.accounts) { // Same for the accounts
            this.$searchview_buttons.find(".o_account_reports_account_account_auto_complete").select2();
            var selection = [];
            for (i = 0; i < this.report_context.account_ids.length; i++) {
                var account = this.report_context.account_ids[i];
                selection.push({id:account[0], text:account[1] + account[2]});
            }
            this.$searchview_buttons.find('.o_account_reports_account_account_auto_complete').data().select2.updateSelection(selection);

            this.$searchview_buttons.find('.o_account_reports_add_account_account_tag').bind('click', function (event) {
                var report_context = {};
                var value = self.$searchview_buttons.find(".o_account_reports_account_account_auto_complete").select2("val");
                report_context.account_ids = value;
                self.restart(report_context);
            });
        }
        if (this.report_type.analytic && this.report_context.analytic) { // Same for the tags filter
            this.$searchview_buttons.find(".o_account_reports_analytic_account_auto_complete").select2();
            var selection = [];
            for (i = 0; i < this.report_context.analytic_account_ids.length; i++) {
                var analytic_account = this.report_context.analytic_account_ids[i];
                selection.push({id:analytic_account[0], text:analytic_account[1]});
            }
            this.$searchview_buttons.find('.o_account_reports_analytic_account_auto_complete').data().select2.updateSelection(selection);
            this.$searchview_buttons.find(".o_account_reports_analytic_tag_auto_complete").select2();
            selection = [];
            var i;
            for (i = 0; i < this.report_context.analytic_tag_ids.length; i++) {
                var analytic_tag = this.report_context.analytic_tag_ids[i];
                selection.push({id:analytic_tag[0], text:analytic_tag[1]});
            }
            this.$searchview_buttons.find('.o_account_reports_analytic_tag_auto_complete').data().select2.updateSelection(selection);
            this.$searchview_buttons.find('.o_account_reports_add_analytic_account_tag').bind('click', function (event) {
                var report_context = {};
                var value = self.$searchview_buttons.find(".o_account_reports_analytic_account_auto_complete").select2("val");
                report_context.analytic_account_ids = value;
                value = self.$searchview_buttons.find(".o_account_reports_analytic_tag_auto_complete").select2("val");
                report_context.analytic_tag_ids = value;
                self.restart(report_context);
            });
        }
        this.$searchview_buttons.find('li').bind('click', function (event) {event.stopImmediatePropagation();});
        var l10n = core._t.database.parameters; // Get the localisation parameters
        var $datetimepickers = this.$searchview_buttons.find('.o_account_reports_datetimepicker');
        var options = { // Set the options for the datetimepickers
            language : moment.locale(),
            format : time.strftime_to_moment_format(l10n.date_format),
            icons: {
                date: "fa fa-calendar",
            },
            pickTime: false,
        };
        $datetimepickers.each(function () { // Start each datetimepicker
            $(this).datetimepicker(options);
            if($(this).data('default-value')) { // Set its default value if there is one
                $(this).data("DateTimePicker").setValue(moment($(this).data('default-value')));
            }
        });
        if (this.report_context.date_filter !== 'custom') { // For each foldable element in the dropdowns
            this.toggle_filter($useCustomDates, $CustomDates, false); // First toggle it so it is closed
            $dateFilter.bind('hidden.bs.dropdown', function () {self.toggle_filter($useCustomDates, $CustomDates, false);}); // When closing the dropdown, also close the foldable element
        }
        if (this.report_context.date_filter_cmp !== 'previous_period') {
            this.toggle_filter($usePreviousPeriod, $previousPeriod, false);
            $dateFilterCmp.bind('hidden.bs.dropdown', function () {self.toggle_filter($usePreviousPeriod, $previousPeriod, false);});
        }
        if (this.report_context.date_filter_cmp !== 'same_last_year') {
            this.toggle_filter($useSameLastYear, $SameLastYear, false);
            $dateFilterCmp.bind('hidden.bs.dropdown', function () {self.toggle_filter($useSameLastYear, $SameLastYear, false);});
        }
        if (this.report_context.date_filter_cmp !== 'custom') {
            this.toggle_filter($useCustomCmp, $CustomCmp, false);
            $dateFilterCmp.bind('hidden.bs.dropdown', function () {self.toggle_filter($useCustomCmp, $CustomCmp, false);});
        }
        return this.$searchview_buttons;
    }
});
core.action_registry.add("account_report_generic", account_report_generic);
return account_report_generic;
});

odoo.define('sarangoci_purchase_direct.sarangoci_purchase_direct', function (require) {
    "use strict";

    var base = require('web_editor.base');
    var ajax = require('web.ajax');
    var utils = require('web.utils');
    var core = require('web.core');
    var config = require('web.config');
    var _t = core._t;

   
    

    if (!$('.oe_website_purchase').length) {
        return $.Deferred().reject("DOM doesn't contain '.oe_website_purchase'");
    }

    $('.oe_website_purchase').each(function () {
        var oe_website_purchase = this;
        var clickwatch = (function () {
            var timer = 0;
            return function (callback, ms) {
                clearTimeout(timer);
                timer = setTimeout(callback, ms);
            };
        })();
        
        $(oe_website_purchase).on("change", "select.branch", function () {
            var $input = $(this);
            var x = document.getElementsByName("branch");
            if ($(x)[0].value == 'Please Select Branch')
            {
                alert('Please Select Branch')
            }


            if ($input.data('update_change')) {
                return;
            }
            var value = $input.val();
            clickwatch(function () {
                $input.data('update_change', true);

                ajax.jsonRpc("/purchase/direct/branch/update_json", 'call', {
                    'branch_id': value
                }).then(function (data) {
                    $input.data('update_change', false);
                    if (value !== $input.val()) {
                        $input.trigger('change');
                        return;
                    }
                });
            }, 500);
        });
    });
});
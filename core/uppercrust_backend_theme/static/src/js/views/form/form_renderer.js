// odoo Form view inherit for teb view change and form first panel create.

odoo.define('uppercrust_backend_theme.FormView', function (require) {
    "use strict";

    var core = require('web.core');
    var FormView = require('web.FormView');
    var common = require('web.form_common');
    var config = require('web.config');
    var FormRenderingEngine = require('web.FormRenderingEngine');
    var FormRenderingEngineMobile = require('uppercrust_backend_theme.FormRenderingEngineMobile');

    var _t = core._t;
    var Qweb = core.qweb;

    FormRenderingEngine.include({
        process: function ($tag) {
            var self = this;
            var tagname = $tag[0].nodeName.toLowerCase();
            if (tagname === 'header') {
                self._processHeader($tag);
            }
            if ($tag.attr('name') === 'button_box') {
                this.view.is_initialized.then(function () {
                    var $buttons = $tag.children();
                    self.organize_button_box($tag, $buttons);

                    self.view.on('view_content_has_changed', self, function () {
                        this.organize_button_box($tag, $buttons);
                    });
                    core.bus.on('size_class', self, function () {
                        this.organize_button_box($tag, $buttons);
                    });
                });
            }
            return this._super($tag);
        },
        _processHeader: function($statusbar){
            this.fill_statusbar_buttons($statusbar, $statusbar.contents('button'));
        },
        fill_statusbar_buttons: function ($statusbar_buttons, $buttons) {
            $statusbar_buttons.append($buttons);
        },
        organize_button_box: function ($button_box, $buttons) {
            var $visible_buttons = $buttons.not('.o_form_invisible');
            var $invisible_buttons = $buttons.filter('.o_form_invisible');

            // Get the unfolded buttons according to window size
            var nb_buttons = [2, 4, 6, 7][config.device.size_class];
            var $unfolded_buttons = $visible_buttons.slice(0, nb_buttons).add($invisible_buttons);

            // Get the folded buttons
            var $folded_buttons = $visible_buttons.slice(nb_buttons);
            if ($folded_buttons.length === 1) {
                $unfolded_buttons = $buttons;
                $folded_buttons = $();
            }

            // Empty button box and toggle class to tell if the button box is full (LESS requirement)
            $buttons.detach();
            $button_box.empty();
            var full = ($visible_buttons.length > nb_buttons);
            $button_box.toggleClass('o_full', full).toggleClass('o_not_full', !full);

            // Add the unfolded buttons
            $unfolded_buttons.each(function (index, elem) {
                $(elem).appendTo($button_box);
            });

            // Add the dropdown with unfolded buttons if any
            if ($folded_buttons.length) {
                $button_box.append($("<button/>", {
                    type: 'button',
                    'class': "btn btn-sm oe_stat_button o_button_more dropdown-toggle",
                    'data-toggle': "dropdown",
                    text: _t("More"),
                }));

                var $ul = $("<ul/>", {'class': "dropdown-menu o_dropdown_more", role: "menu"}).appendTo($button_box);
                $folded_buttons.each(function (i, elem) {
                    $('<li/>').appendTo($ul).append(elem);
                });
            }
        },
        process_notebook: function ($notebook) {
            var self = this;

            // Extract useful info from the notebook xml declaration
            var pages = [];
            $notebook.find('> page').each(function () {
                var $page = $(this);
                var page_attrs = $page.getAttributes();
                page_attrs.id = _.uniqueId('notebook_page_');
                page_attrs.contents = $page.html();
                page_attrs.ref = $page;  // reference to the current page node in the xml declaration
                pages.push(page_attrs);
            });

            // Render the notebook and replace $notebook with it
            var $new_notebook = self.render_element('FormRenderingNotebook', {'pages': pages});
            $notebook.before($new_notebook).remove();
            $new_notebook.find('a.o_tab_page').click(function () {
                $(this).parent('li')
                        .toggleClass("ad_close");
            });
            // Bind the invisibility changers and find the page to display
            var pageid_to_display;
            _.each(pages, function (page) {
                var $tab = $new_notebook.find('a[href=#' + page.id + ']').parent();
                var $content = $new_notebook.find('#' + page.id);

                // Case: <page autofocus="autofocus">;
                // We attach the autofocus attribute to the node because it can be useful during the
                // page execution
                self.attach_node_attr($tab, page.ref, 'autofocus');
                self.attach_node_attr($content, page.ref, 'autofocus');
                if (!pageid_to_display && page.autofocus) {
                    // If multiple autofocus, keep the first one
                    pageid_to_display = page.id;
                }

                // Case: <page attrs="{'invisible': domain}">;
                self.handle_common_properties($tab, page.ref, common.NotebookInvisibilityChanger);
                self.handle_common_properties($content, page.ref, common.NotebookInvisibilityChanger);
            });
            if (!pageid_to_display) {
                pageid_to_display = $new_notebook.find('div[role="tabpanel"]:not(.o_form_invisible):first').attr('id');
            }

            // Display page. Note: we can't use bootstrap's show function because it is looking for
            // document attached DOM, and the form view is only attached when everything is processed
            $new_notebook.find('a[href=#' + pageid_to_display + ']').parent().addClass('active');
            $new_notebook.find('#' + pageid_to_display).addClass('active');

            self.process($new_notebook.children());
            self.handle_common_properties($new_notebook, $notebook);

            return $new_notebook;
        },
    });
    FormView.include({
        defaults: _.extend({}, FormView.prototype.defaults, {
            disable_autofocus: config.device.touch,
        }),
        init: function () {
            this._super.apply(this, arguments);
            if (config.device.size_class <= config.device.SIZES.XS) {
                this.rendering_engine = new FormRenderingEngineMobile(this);
            }
        },
        _doUpdateSidebar: function (mode) {
            if (mode === 'view' && this.sidebar.$el.hasClass('o_drw_in')) {
                $('body').find('.ad_rightbar').addClass('o_open_sidebar');
            } else {
                $('body').find('.ad_rightbar').removeClass('o_open_sidebar');
            }
        },
        do_show: function(){
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if (self.sidebar) {
                    self._doUpdateSidebar(self.get("actual_mode"));
                }
            })
        },
    });
});
odoo.define('uppercrust_backend_theme.FormRenderingEngineMobile', function (require) {
    "use strict";

    var FormRenderingEngine = require('web.FormRenderingEngine');

    return FormRenderingEngine.extend({
        fill_statusbar_buttons: function ($statusbar_buttons, $buttons) {
            if (!$buttons.length) {
                return;
            }
            var $statusbar_buttons_dropdown = this.render_element('FormRenderingStatusBar_DropDown', {});
            $buttons.each(function (i, el) {
                $statusbar_buttons_dropdown.find('.dropdown-menu').append($('<li/>').append(el));
            });
            $statusbar_buttons.append($statusbar_buttons_dropdown);
        },
    });
});
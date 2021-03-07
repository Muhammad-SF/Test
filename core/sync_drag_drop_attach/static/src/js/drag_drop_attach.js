odoo.define('sync_drag_drop_attach.drag_drop_attach', function (require) {
"use strict";

    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;
    var FormView = require('web.FormView');
    var Sidebar = require('web.Sidebar');
    var framework = require('web.framework');
    
    FormView.include({
        toggle_buttons: function() {
            var self = this;
            this._super.apply(this, arguments);
            if(this.get("actual_mode") === "view") {
                self.$el.find('div.o_form_sheet').on('dragover',function(e) {
                    e.preventDefault();e.stopPropagation();
                    self.$el.find('.o_form_sheet').addClass('adjust_sheet');
                    self.$el.find('div.hidden_formview_drop').addClass('hidden_drop_formview_highlight');
                })
                .on('dragleave', function(e){self.toggle_effect(e)})
                .on('drop',function(e) {
                    if(e.originalEvent.dataTransfer && e.originalEvent.dataTransfer.files.length){
                        self.toggle_effect(e);
                        framework.blockUI();
                        self.upload_files(e.originalEvent.dataTransfer.files);
                    }
                });
            } else {
                self.$el.find('div.o_form_sheet').off('dragover').off('dragleave').off('drop');
            }
        },
        toggle_effect: function(e){
            var self = this;
            e.preventDefault();e.stopPropagation();
            self.$el.find('div.hidden_formview_drop').removeClass('hidden_drop_formview_highlight');
            self.$el.find('.o_form_sheet').removeClass('adjust_sheet');
        },
        upload_files: function(files){
            var self = this;
            var flag = 1;
            var total_attachements = 0;
            _.each(files, function(file){
                var querydata = new FormData();
                querydata.append('callback', 'oe_fileupload_temp2');
                querydata.append('model', self.dataset.model);
                querydata.append('id', self.datarecord.id);
                querydata.append('ufile',file);
                querydata.append('multi', 'true');
                querydata.append('csrf_token', core.csrf_token);
                $.ajax({
                    url: '/web/binary/upload_attachment',
                    type: 'POST',
                    data: querydata,
                    cache: false,
                    processData: false,
                    contentType: false,
                    success: function(id){
                        self.load_record(self.datarecord);
                        if(files.length == flag) framework.unblockUI();
                        flag += 1;
                    }
                });
            });
        }
    });
    Sidebar.include({
        on_attachment_changed: function(e) {
            var $e = $(e.target);
            if ($e.val() !== '') {
                this.getParent().upload_files(e.target.files);
            }
        }
    });
});
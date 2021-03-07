/*
 * @file image paste plugin for CKEditor
 Feature introduced in: https://bugzilla.mozilla.org/show_bug.cgi?id=490879
 doesn't include images inside HTML (paste from word): https://bugzilla.mozilla.org/show_bug.cgi?id=665341
 * Copyright (C) 2011-13 Alfonso Martínez de Lizarrondo
 *
 * == BEGIN LICENSE ==
 *
 * Licensed under the terms of any of the following licenses at your
 * choice:
 *
 *  - GNU General Public License Version 2 or later (the "GPL")
 *    http://www.gnu.org/licenses/gpl.html
 *
 *  - GNU Lesser General Public License Version 2.1 or later (the "LGPL")
 *    http://www.gnu.org/licenses/lgpl.html
 *
 *  - Mozilla Public License Version 1.1 or later (the "MPL")
 *    http://www.mozilla.org/MPL/MPL-1.1.html
 *
 * == END LICENSE ==
 *
 * version 1.1.1: Added allowedContent settings in case the Advanced tab has been removed from the image dialog
 */

// Handles image pasting in Firefox
CKEDITOR.plugins.add('imagepaste',
    {
        init: function (editor) {
            setTimeout(function () {
                jQuery.each(editor.document, function (key, value) {
                    if (key == '$') {
                        value.onpaste = function (event) {
                            console.log(event, 'event');
                            var items = (event.clipboardData || event.originalEvent.clipboardData).items;
                            for (index in items) {
                                var item = items[index];
                                if (item.kind === 'file') {
                                    var blob = item.getAsFile();
                                    var reader = new FileReader();
                                    reader.onload = function (revent) {
                                        var imageURL = reader.result;
                                        console.log('self.editor', editor);
                                        editor.setData('<img src="' + imageURL + '"/>');
                                    };
                                    reader.readAsDataURL(blob);
                                    return false;
                                }
                            }
                            console.log(event, 'event');
                        };
                    }
                });
            }, 3000);
        } //Init
    });

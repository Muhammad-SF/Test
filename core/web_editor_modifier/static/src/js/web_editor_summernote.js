odoo.define('web_editor_modifier.editor_modifier', function (require) {
    "use strict";


    var core = require('web.core');
    require('summernote/summernote'); // wait that summernote is loaded

    var _t = core._t;

    //////////////////////////////////////////////////////////////////////////////////////////////////////////
    /* Summernote Lib (neek hack to make accessible: method and object) */

    var dom = $.summernote.core.dom;
    var range = $.summernote.core.range;
    var eventHandler = $.summernote.eventHandler;
    var editor = eventHandler.modules.editor;

    var xEDITOR = require('web_editor.summernote')
    console.log('an hanh');

    xEDITOR.pluginEvents.visible = function (event, editor, layoutInfo) {
        console.log('visible');
        var $editable = layoutInfo.editable();
        $editable.data('NoteHistory').recordUndo($editable, "visible");
        var r = range.create();
        if (!r) return;

        if (!r.isCollapsed()) {
            if (dom.isCell(dom.node(r.sc)) || dom.isCell(dom.node(r.ec))) {
                remove_table_content(r);
                r = range.create(r.ec, 0).select();
            }
            r.select();
        }

        // don't write in forbidden tag (like span for font awsome)
        var node = dom.firstChild(r.sc.tagName && r.so ? r.sc.childNodes[r.so] || r.sc : r.sc);
        while (node.parentNode) {
            if (dom.isForbiddenNode(node)) {
                var text = node.previousSibling;
                if (text && dom.isText(text) && dom.isVisibleText(text)) {
                    range.create(text, text.textContent.length, text, text.textContent.length).select();
                } else {
                    text = node.parentNode.insertBefore(document.createTextNode( "." ), node);
                    range.create(text, 1, text, 1).select();

                    setTimeout(function () {
                        try{
                            var text = range.create().sc;
                            text.textContent = text.textContent.replace(/^./, '');
                            range.create(text, text.textContent.length, text, text.textContent.length).select();
                        }catch(err) {}
                    },0);
                }
                break;
            }
            node = node.parentNode;
        }

        return true;
    };
})
odoo.define('uppercrust_backend_theme.uppercrust_backend', function (require) {
"use strict";

	var core = require('web.core');
	var Dialog = require('web.Dialog')
	var web_calendar = require('web_calendar.CalendarView')
	$(document).ready(function(){ 

    

		shortcut.add("Alt+I", function() {
            $('.main_calendar').click()
        });
        shortcut.add("Alt+V", function() {
            // $(".oe_cp_view_btn").click()
            if($('.oe_cp_view_btn').hasClass('open')){
                $('.oe_cp_view_btn').removeClass('open')
            }
            else{
                $('.oe_cp_view_btn').addClass('open')
            }
            
        });


        shortcut.add("Alt+A", function() {
            $('#children_toggle').click()
        });


        shortcut.add("Alt+W", function() {
            $('.o_searchview_more').click()
        });
        
        // Alt+N===========main menu=============
        shortcut.add("Alt+Q", function() {
            $('#menu_toggle').click()
        });

        // Alt+Q===========main menu=============
        shortcut.add("Alt+Z", function() {
            
        	if($('.o_gb_search').hasClass('open')){
        		$('.o_gb_search').removeClass('open')
        	}
        	else{
        		$('.o_gb_search').addClass('open')
                $('.global-search').focus()
                $('.global-search').val('')


                var $body = $('body'),
                $main_menu = $('#menu_toggle'),
                $child_menu = $('#children_toggle'),
                $full_view = $('#av_full_view'),
                $right_panel = $('.ad_rightbar');

                $body.removeClass('nav-sm ad_open_childmenu');
                // $('#menu_toggle').removeClass('nav-sm').toggleClass('ad_open_childmenu');
                // $('#menu_toggle').removeClass('active')                
        	}
            
        });
        shortcut.add("Alt+U", function() {
        	if($('.o_user_menu').hasClass('open')){
        		$('.o_user_menu').removeClass('open')
        	}
        	else{
        		$('.o_user_menu').addClass('open')
        	}
        });

        // Alt+M=============Edit============
        shortcut.add("Alt+R", function() {
            $('.o_form_button_edit ').click()
        });

        // =============Previous record============
        shortcut.add("Alt+1", function() {
            if ($('button.o_pager_previous').length != 0){
                $('button.o_pager_previous').trigger('click');
            }
        });

        // =============next record============
        shortcut.add("Alt+2", function() {
            if ($('button.o_pager_next').length != 0){
                $('button.o_pager_next').trigger('click');
            }
        });

        // =====for duplicate action============
        shortcut.add("Alt+6", function() {
            $('.dropdown-menu li a').each(function() {
                if($(this).data('section') == 'other' && $(this).text().trim() == 'Duplicate'){
                    $(this).trigger('click');
                }
            });
            $('button.o_dropdown_toggler_btn').each(function() {
                if($(this).text().trim() == 'Action'){
                    $(this).find('.dropdown-menu li a').each(function() {
                        if($(this).text().trim() == 'Duplicate'){
                            $(this).trigger('click');
                        }
                    });
                }
            });
        });


        shortcut.add("Alt+X", function() {
            $('.o_form_button_cancel ').click()
        });
        
        // Alt+k===========pivot view=============
        shortcut.add("Alt+5", function() {
            $('.o_cp_switch_pivot ').click()
        });
        // ===========list view=============
        shortcut.add("Alt+4", function() {
            $('.o_cp_switch_list ').click()
        });
        // ==========kanban  view=============
        shortcut.add("Alt+6", function() {
            $('.o_cp_switch_kanban ').click()
        });
        // ==========place cursor on the search bar=============
        shortcut.add("Alt+B", function() {
            $('.o_searchview_input').focus()
        });




        shortcut.add("Alt+G", function() {
            $('.o_cp_switch_graph ').click()
        });


        shortcut.add("Alt+T", function() {
            $('.o_sidebar_drw ').click()
        });

        // shortcut.add("Alt+P", function() {
        //     $('.o_sidebar_drw ').click()
        //     $('button.o_dropdown_toggler_btn').each(function() {
        //         if($(this).text().trim() == 'Print'){
        //             $(this).parents('div.o_dropdown').addClass('open');
        //         }
        //     });
        // });
       
        // shortcut.add("Alt 38", function(){
        //     console.log("}}}}}}}}}}}}}}}}}}}}}}}}")
        //     // $('.o_cp_switch_graph ').click()
        // });

        // shortcut.add("left", function() {
        //     console.log("SSSSSSSWWWWWWWWWWWWWWWWW")
        //     $('.o_pager_previous ').click()
        // });



        shortcut.add("Alt+Y", function() {
            window.location = $.param.querystring( window.location.href, '?debug=')
        });



        
	});
	
    $.ctrl = function(key, callback, args) {
        $(document).keydown(function(e) {
            if(!args) args=[]; // IE barks when args is null
            if((e.keyCode == key.charCodeAt(0) || e.keyCode == key) && e.altKey) {
                callback.apply(this, args);
            }
        });        
    };
    // Ctrl Key + < : Previous Record
    // 37================Previous Record========
    // $.ctrl('37', function() {
    //     if ($('button.o_pager_previous').length != 0){
    //         $('button.o_pager_previous').trigger('click');
    //     }
    // });

    $.ctrl('38', function() {
        $('ol.breadcrumb li.active').each(function() {

            if($(this).prev('li')){
                $(this).prev('li').trigger('click');
            }
        });
    });

});

$(document).ready(function () {
    var $body = $('body'),
            $main_menu = $('#menu_toggle'),
            $child_menu = $('#children_toggle'),
            $full_view = $('#av_full_view'),
            $right_panel = $('.ad_rightbar');
            $s_manu = $('.show_shortcuts');
    $width = $(document).width();

    // $s_manu.click(function () {
    //    console.log("mmmmmmmmmmmmmmmmmmmmmmm")
    // });

    // Main menu button click [start]
    $main_menu.click(function () {
        $('#appDrawerSearchInput').focus();
        $('#appDrawerSearchInput').val('');
        $('.menus_list').hide();
        $('#sidebar-menu').show();
        let image_src = $('.ad-sm-logo img').attr('src');
        $('.o_sub_menu_logo:not(.o_menu_logo) img').attr('src', image_src);
        $('.menu_section').show();
        $body.removeClass('ad_open_childmenu').toggleClass('nav-sm');
        $(this).toggleClass('active');
        $child_menu.removeClass('active');
    });
    // Main menu button click [stop]

    // Child menu button click [start]
    $child_menu.click(function () {
        $body.removeClass('nav-sm').toggleClass('ad_open_childmenu');
        $(this).toggleClass('active');
        $main_menu.removeClass('active');
    });
    // Child menu button click [stop]

    // Create a full view [start]
    // $full_view.click(function () {
    //     $body.removeClass('nav-sm ad_open_childmenu').toggleClass('ad_full_view');
    // });

    $('.oe_back_btn').click(function (e) {
        $body.removeClass('nav-sm ad_open_childmenu');
        $main_menu.removeClass('active');
        $child_menu.removeClass('active');
    });

    // Right panel click time left menu close [start]
    $right_panel.click(function () {
        if ($body.hasClass('nav-sm') || $body.hasClass('ad_open_childmenu')) {
            $body.removeClass('nav-sm ad_open_childmenu');
            $main_menu.removeClass('active');
            $child_menu.removeClass('active');
        }
    });
    // Right panel click time left menu close [stop]

    $(document).click(function (e) {
        if (!$(e.target).hasClass('cp_open')) {
            $('.o_cp_buttons').removeClass('cp_open');
        }
    });
});
/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
odoo.define('website_product_videos.wk_product_video', function (require) {
    "use strict";
    var ajax = require('web.ajax');
    $(document).ready(function() {
        $("div.wk_provideo").parents('div').css("text-align", "center");
        var url = $(".descriptionVideo").attr('src');
        $('.wk_provideo').on('click', '.wk_image', function(e) {
            url = $(this).parent().find('.wk_video_url').val();
        });
        $("#popupvideo").on('hide.bs.modal', function(){
            $(".descriptionVideo").attr('src', '');
        });
        $("#popupvideo").on('show.bs.modal', function(){
            $(".descriptionVideo").attr('src', url);
        });
        var videourl = $('.wkmultivideo').attr('src');
        var wkhover = $('input.wk_hover').val();
        if (wkhover) {
            $(".wk_descvideo" ).hover(
                function() {
                    videourl = $(this).find('.wkmultivideo').attr('src');
                    $(this).find('.wkmultivideo').attr('src', videourl + '&autoplay=1');
                }, function() {
                $(this).find('.wkmultivideo').attr('src', videourl);
                });
            $(".item" ).hover(
                function() {
                    videourl = $(this).find('.wkmultivideo').attr('src');
                    $(this).find('.wkmultivideo').attr('src', videourl + '&autoplay=1');
                }, function() {
                $(this).find('.wkmultivideo').attr('src', videourl);
                });
        }
        });
})
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import api, fields, models, _

class WebsiteConfigSettings(models.TransientModel):
    _inherit = 'website.config.settings'

    group_website_multi_video = fields.Boolean(string="Multi-Videos", implied_group='website_product_videos.group_website_multi_video', group='base.group_portal,base.group_user,base.group_public,website_sale.group_website_multi_image',
                                  help="""Enabling this setting will also enable multi image setting on your Odoo website.""")
    
    @api.multi
    def set_default_website_config_configuration(self):
        irValues = self.env['ir.values'].sudo()
        irValues.set_default('website.config.settings','group_website_multi_video', self.group_website_multi_video)
        return True

    @api.multi
    def get_default_website_config_configuration(self, fields):
        irValues = self.env['ir.values'].sudo()
        return {
            'group_website_multi_video':irValues.get_default('website.config.settings','group_website_multi_video'),
        }

    @api.onchange('group_website_multi_video')
    def _onchange_group_website_multi_video(self):
        if self.group_website_multi_video:
            self.update({
                'group_website_multiimage': 1,
            })

class WebsiteProductVideoSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'website.product.video.settings'

    youtube_api_key = fields.Char(string="YouTube API Key",
                                  help="""YouTube API Key""")
    autoplay = fields.Boolean(string="Autoplay Video",
                                  help="""This parameter specifies whether the initial video will automatically start to play when the player loads.""")
    controls = fields.Selection([('1', 'Show'), ('0', 'Hide')], string="Video Controls",
                                  help="""This parameter indicates whether the video player controls are displayed""")
    showinfo = fields.Selection([('1', 'Show'), ('0', 'Hide')], string="Show Video Info",
                                  help="""showinfo code shows and hides the YouTube header bar""")
    rel = fields.Selection([('1', 'Show'), ('0', 'Hide')], string="Related Video",
                                  help="""This parameter indicates whether the player should show related videos when playback of the initial video ends.""")
    fullscreen_video = fields.Boolean(string="Allow fullscreen Video",
                                  help="""Enable to fullscreen button from displaying in the player""")
    video_frameborder = fields.Integer(string="Video frameborder",
                                  help="""Add frameborder for youtube/vimeo videos""")
    modestbranding = fields.Boolean(string="Modestbranding",
                                  help="""Modestbranding lets you use a YouTube player that does not show a YouTube logo.
                                  Note that a small YouTube text label will still display in the upper-right corner of a paused video when the user's mouse pointer hovers over the player.""")
    loop = fields.Boolean(string="Loop Video",
                                  help="""Enable to set your video to repeat ad infinitum related videos.
                                  This parameter has limited support in the AS3 player and in IFrame embeds, which could load either the AS3 or HTML5 player.
                                  Currently, the loop parameter only works in the AS3 player when used in conjunction with the playlist parameter. """)
    iv_load_policy = fields.Selection([('1', 'Show'), ('3', 'Hide')], string="Annotations Video",
                                  help="""Enable to show/hide annotations""")
    disablekb = fields.Boolean(string="Disable Keyboard Controls",
                                  help="""Enable to disable keyboard control on video.
                                  Currently supported keyboard controls are:
                                    * Spacebar or [k]: Play / Pause
                                    * Arrow Left: Jump back 5 seconds in the current video
                                    * Arrow Right: Jump ahead 5 seconds in the current video
                                    * Arrow Up: Volume up
                                    * Arrow Down: Volume Down
                                    * [f]: Toggle full-screen display
                                    * [j]: Jump back 10 seconds in the current video
                                    * [l]: Jump ahead 10 seconds in the current video
                                    * [m]: Mute or unmute the video
                                    * [0-9]: Jump to a point in the video.
                                            0 jumps to the beginning of the video, 1 jumps to the point 10% into the video, 2 jumps to the point 20% into the video, and so forth.""")
    video_height = fields.Integer(string="Video Height",
                                  help="""Video Height for youtube/vimeo videos""")
    video_width = fields.Integer(string="Video Width",
                                  help="""Video Width for youtube/vimeo videos""")
    popup_video = fields.Boolean(string="Allow Popup Video",
                                  help="""Enable to popup video on video click""")
    autoplay_hover = fields.Boolean(string="Autoplay On Hover",
                                  help="""This parameter specifies whether the mouse hover video will automatically start to play when the player loads.""")

    @api.multi
    def set_default_website_video_config_configuration(self):
        irValues = self.env['ir.values'].sudo()
        irValues.set_default('website.product.video.settings','youtube_api_key', self.youtube_api_key)
        irValues.set_default('website.product.video.settings','autoplay', self.autoplay)
        irValues.set_default('website.product.video.settings','controls', self.controls)
        irValues.set_default('website.product.video.settings','showinfo', self.showinfo)
        irValues.set_default('website.product.video.settings','rel', self.rel)
        irValues.set_default('website.product.video.settings','fullscreen_video', self.fullscreen_video)
        irValues.set_default('website.product.video.settings','video_frameborder', self.video_frameborder)
        irValues.set_default('website.product.video.settings','modestbranding', self.modestbranding)
        irValues.set_default('website.product.video.settings','loop', self.loop)
        irValues.set_default('website.product.video.settings','iv_load_policy', self.iv_load_policy)
        irValues.set_default('website.product.video.settings','disablekb', self.disablekb)
        irValues.set_default('website.product.video.settings','video_height', self.video_height)
        irValues.set_default('website.product.video.settings','video_width', self.video_width)
        irValues.set_default('website.product.video.settings','popup_video', self.popup_video)
        irValues.set_default('website.product.video.settings','autoplay_hover', self.autoplay_hover)
        return True

    @api.multi
    def get_default_website_video_config_configuration(self, fields):
        irValues = self.env['ir.values'].sudo()
        res = {
            'youtube_api_key':irValues.get_default('website.product.video.settings','youtube_api_key'),
            'autoplay':irValues.get_default('website.product.video.settings','autoplay'),
            'controls':irValues.get_default('website.product.video.settings','controls'),
            'showinfo':irValues.get_default('website.product.video.settings','showinfo'),
            'rel':irValues.get_default('website.product.video.settings','rel'),
            'fullscreen_video':irValues.get_default('website.product.video.settings','fullscreen_video'),
            'modestbranding':irValues.get_default('website.product.video.settings','modestbranding'),
            'loop':irValues.get_default('website.product.video.settings','loop'),
            'iv_load_policy':irValues.get_default('website.product.video.settings','iv_load_policy'),
            'disablekb':irValues.get_default('website.product.video.settings','disablekb'),
            'popup_video':irValues.get_default('website.product.video.settings','popup_video'),
            'autoplay_hover':irValues.get_default('website.product.video.settings','autoplay_hover'),
        }
        return res

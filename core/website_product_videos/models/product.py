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

from odoo import api, fields, models
import re
from odoo.exceptions import UserError
import requests
import json
import binascii

class ProductVideo(models.Model):
    _name = "product.video"

    video_url = fields.Char(
        string='Url',
        required=True,
        help="Video Url of youtube or vimeo")
    video_id = fields.Char(
        string='Video Id',
        help="Video Id of youtube or vimeo")
    video_description = fields.Text(
        string='Description',
        help="Video description of youtube or vimeo")
    name = fields.Char('Title')
    use_description = fields.Boolean(string="Use as product description", default=True)
    exclude = fields.Boolean(string="Exclude from product multi videos", default=False)
    image = fields.Binary('Thumbnail', attachment=True)
    image_large = fields.Binary('Large Image', attachment=True)
    product_tmpl_id = fields.Many2one('product.template', 'Related Product', copy=True)

    @api.onchange("image")
    def setImage(self):
        if self.image:
            self.image_large = self.image

    @api.onchange("video_url")
    def getDetails(self):
        videoUrl = self.video_url
        if videoUrl:
            if "vimeo" in videoUrl:
                videoUri = videoUrl.split("/")
                if len(videoUri) > 1:
                    videoId = videoUri[-1]
                    self.getVimeoData(videoId)
                else:
                    raise UserError("Video cant be shown due to the following reason: Invalid vimeo url")
            else:
                youtubeApiKey = self.env['ir.values'].sudo().get_default('website.product.video.settings', 'youtube_api_key', True)
                if not youtubeApiKey:
                    raise UserError("Video cant be shown due to the following reason: Youtube API key is invalid")
                youtubeId = self.getVideoId()
                if youtubeId:
                    self.getYoutubeData(youtubeId, youtubeApiKey)

    def getVimeoData(self, videoId):
        apiUrl = "http://vimeo.com/api/v2/video/{}.json".format(videoId)
        videoObj = requests.get(apiUrl)
        if videoObj.status_code == 200:
            videoInfo = json.loads(videoObj.text)
            if videoInfo:
                items = videoInfo[0]
                if items:
                    title = items.get('title')
                    description = items.get('description')
                    imageLargeUrl = items.get('thumbnail_large')
                    imageUrl = items.get('thumbnail_medium')
                    proImageLarge = binascii.b2a_base64(requests.get(imageLargeUrl).content)
                    proImage = binascii.b2a_base64(requests.get(imageUrl).content)
                    self.name = title
                    self.video_id = videoId
                    self.video_description = description
                    self.image_large = proImageLarge
                    self.image = proImage
        return True

    def getYoutubeData(self, youtubeId, youtubeApiKey):
        youtubeUrl = "https://www.googleapis.com/youtube/v3/videos?part=snippet&id={}&key={}".format(youtubeId, youtubeApiKey)
        videoObj = requests.get(youtubeUrl)
        if videoObj.status_code == 200:
            videoInfo = json.loads(videoObj.text)
            if videoInfo.get('items'):
                items = videoInfo.get('items')[0]
                if items:
                    title = items.get('snippet').get('title')
                    description = items.get('snippet').get('description')
                    imageLargeUrl = items.get('snippet').get('thumbnails').get("high").get("url")
                    imageUrl = items.get('snippet').get('thumbnails').get("medium").get("url")
                    proImageLarge = binascii.b2a_base64(requests.get(imageLargeUrl).content)
                    proImage = binascii.b2a_base64(requests.get(imageUrl).content)
                    self.name = title
                    self.video_id = youtubeId
                    self.video_description = description
                    self.image_large = proImageLarge
                    self.image = proImage
        return True

    def getVideoId(self):
        youtubeId = False
        linkPattern = r'(?:https?:\/\/)?(?:[0-9A-Z-]+\.)?(?:youtube|youtu|youtube-nocookie)\.(?:com|be)\/(?:watch\?v=|watch\?.+&v=|embed\/|v\/|.+\?v=)?([^&=\n%\?]{11})'
        result = re.findall(linkPattern, self.video_url, re.MULTILINE | re.IGNORECASE)
        if result:
            youtubeId = result[0]
        return youtubeId

    def getEmbedUrl(self):
        videoUrl = self.video_url
        videoId = self.video_id
        if "vimeo" in videoUrl:
            if not videoId:
                videoUri = videoUrl.split("/")
                if len(videoUri) > 1:
                    videoId = videoUri[-1]
            url = "https://player.vimeo.com/video/{}?".format(videoId)
        else:
            if not videoId:
                videoId = self.getVideoId()
            url = "https://www.youtube.com/embed/{}?".format(videoId)
        url = self.getUpdatedUrl(url)
        return url

    def getUpdatedUrl(self, url):
        options = ['autoplay', 'controls', 'showinfo', 'rel', 'modestbranding', 'loop', 'iv_load_policy', 'disablekb']
        for option in options:
            optionVal = self.env['ir.values'].sudo().get_default('website.product.video.settings', option, True)
            if optionVal:
                url = "{}&{}={}".format(url, option, optionVal)
        return url

class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_video_ids = fields.One2many('product.video', 'product_tmpl_id', string='Videos')

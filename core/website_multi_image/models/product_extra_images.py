# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
from odoo import api, fields, models
from odoo import tools
import logging
_logger = logging.getLogger(__name__)

class ProductExtraImages(models.Model):
	_name = 'product.extra.images'
	_description = "Product Extra Images"

	name = fields.Char(string='Image Title',help="A Title shows when you mouse over an image.")
	image_alt = fields.Text(string='Image ALT Text', help="The alt text within the ALT tag should let the user know"\
		"what an image’s content and purpose are. It will shows if the image doesn't appear on a page. "\
		"Search engines may also use alt text to index your site.")
	image = fields.Binary(string='Image', required=True)
	image_small = fields.Binary(compute='_compute_images', inverse='_inverse_image_small', attachment=True,
		help="Small-sized image of the product. It is automatically "\
            "resized as a 64x64px image, with aspect ratio preserved. "\
            "Use this field anywhere a small image is required.", string='Image Small')
	template_id = fields.Many2one(comodel_name='product.template', string='Product Template')
	sequence = fields.Integer(string='Sequence', required=True)

	@api.depends('image')
	def _compute_images(self):
		for rec in self:
			rec.image_small = tools.image_resize_image_small(rec.image)

	def _inverse_image_small(self):
		for rec in self:
			rec.image = tools.image_resize_image_big(rec.image_small)

class ProductTemplate(models.Model):
	_inherit = 'product.template'
	
	template_extra_images = fields.One2many(comodel_name ='product.extra.images',inverse_name='template_id',string='Product Extra Images')
	



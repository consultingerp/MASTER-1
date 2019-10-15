# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, datetime, timedelta
import werkzeug.urls
import hashlib



class MerchantCetner(models.Model):
    _name = 'merchant.center'

    def _compute_product_count(self):
        read_group_res = self.env['product.template'].read_group([('google_merchant_center_id', 'in', self.ids)], ['google_merchant_center_id'], ['google_merchant_center_id'])
        group_data = dict((data['google_merchant_center_id'][0], data['google_merchant_center_id_count']) for data in read_group_res)
        for brand in self:
            brand.product_count = group_data.get(brand.id, 0)

    name = fields.Char(size=256, string='Center Id', required=True)
    website = fields.Char(size=256, string='Website', required=True)
    product_count = fields.Integer(
        '# Products', compute='_compute_product_count',
        help="The number of products under this Brand")

class MerchantCetnerBrand(models.Model):
    _name = 'merchant.center.brand'

    def _compute_product_count(self):
        read_group_res = self.env['product.template'].read_group([('google_product_brand_id', 'in', self.ids)], ['google_product_brand_id'], ['google_product_brand_id'])
        group_data = dict((data['google_product_brand_id'][0], data['google_product_brand_id_count']) for data in read_group_res)
        for brand in self:
            brand.product_count = group_data.get(brand.id, 0)

    name = fields.Char(size=256, string='Brand Name', required=True)
    product_count = fields.Integer(
        '# Products', compute='_compute_product_count',
        help="The number of products under this Brand")

class MerchantCetnerCategory(models.Model):
    _name = 'merchant.center.category'

    @api.multi
    def _get_display_name(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.parent_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res
        return [(cat.id, " > ".join(reversed(get_names(cat)))) for cat in self]

    def _compute_product_count(self):
        read_group_res = self.env['product.template'].read_group([('google_product_category_id', 'in', self.ids)], ['google_product_category_id'], ['google_product_category_id'])
        group_data = dict((data['google_product_category_id'][0], data['google_product_category_id_count']) for data in read_group_res)
        for categ in self:
            categ.product_count = group_data.get(categ.id, 0)

    name = fields.Char(size=256, string='Category Name', required=True)
    parent_id = fields.Many2one('merchant.center.category',string='Parent Category', select=True)
    display_name = fields.Char('Name',compute="_get_display_name" ,readonly=True)
    product_count = fields.Integer(
        '# Products', compute='_compute_product_count',
        help="The number of products under this category (Does not consider the children categories)")

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive categories.'))
        return True

    @api.multi
    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.parent_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res

        return [(cat.id, " > ".join(reversed(get_names(cat)))) for cat in self]


class product_template(models.Model):
    _inherit = 'product.template'

    @api.multi
    def _get_google_content_uri(self):
        ir_config = self.env['ir.config_parameter']
        web_base_url = ir_config.sudo().get_param("web.base.url")
        params = {
            'scope': 'https://www.googleapis.com/auth/content',
            'redirect_uri': web_base_url + '/google_content/authentication',
            'client_id': ir_config.sudo().get_param('google_content_client_id'),
            'response_type': 'code',
            #'approval_prompt': 'force',
            'access_type': 'offline',
        }
        for rec in self:
            rec.google_content_uri = 'https://accounts.google.com/o/oauth2/auth?%s' % werkzeug.url_encode(params)

    @api.model
    def _get_target_country(self):
        return self.env.user.company_id and self.env.user.company_id.country_id and self.env.user.company_id.country_id.code or 'US'

    @api.model
    def _compute_google_auth_code(self):
        return self.env['ir.config_parameter'].sudo().get_param('google_content_tocken_id')

    @api.model
    def _get_product_category(self):
        if self._context.get('google_product_category_id') or self._context.get('default_google_product_category_id'):
            return self._context.get('google_product_category_id') or self._context.get('default_google_product_category_id')
        category = self.env.ref('website_google_merchant_center.product_merchant_category_sports_athletics_cricket', raise_if_not_found=False)
        return category and category.id or False

    google_merchant_center_id = fields.Many2one('merchant.center', string='Center Id',
        help="Select your merchant center where you want to upload product")
    google_website =  fields.Char(related='google_merchant_center_id.website', string='Website', 
        readonly=True, help="Give your website URL for which product is related. To support multiple websites.")
    google_content_uri = fields.Char(string='Google Content Authorization', compute='_get_google_content_uri', readonly=True)
    google_content_authorization_code = fields.Char(string='Google Content Authorization Code', default=_compute_google_auth_code)
    sync_with_mc = fields.Boolean("Sync with Google Merchant Center?", default=True,
        help="Set True if want to sync product to google merchant center.")
    google_product_category_id = fields.Many2one('merchant.center.category', string='Product Category',
        help="Create and set proper category of your product compitable with google product categories.")
    google_product_brand_id = fields.Many2one('merchant.center.brand', string='Brand',
        help="Use the brand attribute to indicate the product's brand name. The brand is used"
        " to help identify your product and will be shown to users who view your ad."
        " If dont have brand set identifies false.")
    google_condition = fields.Char(string='Product Condition', default='new',
        help="Tell users about the condition of the product you're selling. Setting this value correctly"
        " is important since we use it to refine search results. supported values new, refurbished, used")
    google_shipping = fields.Char(string='Shipping Service', default='Standard shipping',
        help="Shipping service related information for target country.")
    google_shipping_amount = fields.Char(string='Shipping Amount', default='14',
        help="Shipping charges for target country")
    google_tax_rate = fields.Char(string='Tax Rate', default='7.75',
        help="Give tax rate applicable on your product for target country.")
    google_channel = fields.Char(string='Channel', default='online',
        help="Set value how you want to sale product. online, offline")
    google_content_language = fields.Char(string='Content Language', default='en')
    google_target_country = fields.Char(string='Target Country', default=_get_target_country)

    @api.multi
    def sync_temp_products_with_gmc(self):
        products = self.env['product.product'].search([('sync_with_mc','=',True), ('product_tmpl_id','in',self.ids)])
        self.env['google.merchant.center.service'].sync_product_with_gmc(products)

    @api.multi
    def delete_temp_products_from_gmc(self):
        products = self.env['product.product'].search([('sync_with_mc','=',True), ('google_mcid','!=',False), ('product_tmpl_id','in',self.ids)])
        self.env['google.merchant.center.service'].delete_product_from_gmc(products)

class MerchantCetnerColor(models.Model):
    _name = 'merchant.center.color'

    def _compute_product_count(self):
        read_group_res = self.env['product.product'].read_group([('google_product_color_id', 'in', self.ids)], ['google_product_color_id'], ['google_product_color_id'])
        group_data = dict((data['google_product_color_id'][0], data['google_product_color_id_count']) for data in read_group_res)
        for color in self:
            color.product_count = group_data.get(color.id, 0)

    name = fields.Char(size=256, string='Color', required=True)
    product_count = fields.Integer(
        '# Products', compute='_compute_product_count',
        help="The number of products under this color")


class MerchantCetnerSize(models.Model):
    _name = 'merchant.center.size'

    def _compute_product_count(self):
        read_group_res = self.env['product.product'].read_group([('google_product_size_id', 'in', self.ids)], ['google_product_size_id'], ['google_product_size_id'])
        group_data = dict((data['google_product_size_id'][0], data['google_product_size_id_count']) for data in read_group_res)
        for size in self:
            size.product_count = group_data.get(size.id, 0)

    name = fields.Char(size=256, string='Size', required=True)
    product_count = fields.Integer(
        '# Products', compute='_compute_product_count',
        help="The number of products under this size")


class product_product(models.Model):
    _inherit = 'product.product'

    google_mcid = fields.Char(string='Center Product ID',
        help="Product id whihc will be used on merchant center as id.")
    google_identifier_exists = fields.Boolean("Identifier exists", default=True,
        help="In special case if GTIN or MPIN or BRAND not exist set False to avoid disaproval on center")
    google_barcode_as_gtin = fields.Boolean("Use Barcode as GTIN", default=True,
        help="If want to use product barcode synced as GTIN mark as true.")
    google_gtin = fields.Char(string='Product GTIN',
        help="Enter your products GTIN no.")
    google_product_color_id = fields.Many2one('merchant.center.color', string='Color',
        help="Set color of your product. On some product like shoes or clothes we need to define color.")
    google_availability = fields.Char(string='Product Availability', default='in stock',
        help="Product availability in your stock. accepted values: in stock, out of stock, preorder")
    google_product_size_id = fields.Many2one('merchant.center.size', string='Size',
        help="Size of your product. required for clothes and shoe like products.")
    google_gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('unisex', 'unisex'),
    ], string='Gender', help="Product is for which gender")
    google_age_group = fields.Selection([
        ('adult', 'Adult'),
        ('newborn', 'Newborn'),
        ('infant', 'Infant'),
        ('toddler', 'Toddler'),
        ('kids', 'Kids'),
    ], string='Age Group', help="Product if for which age group.")
    google_sync_date = fields.Date('Last Sync Date')
    google_expiration_date = fields.Date('Expiration Date',
        help="Set product expiration date if it is going to expire before 30 days. "
        "there is no meaning of setting expiration date after 30 days")

    #Display OR Dynamic Marketing relates fields
    google_display_ads_id = fields.Char(string='Display Ads ID', 
        help="This attribute will override the ‘id’ attribute in your products feed for your"
        " dynamic remarketing campaigns only. The 'display ads id' for each item has to be"
        " unique within your account, and cannot be re-used between feeds. If you have multiple"
        " feeds, the 'display ads id' of items within different feeds must still be unique.")
    google_display_ads_similar_ids = fields.Many2many('product.product', 'google_product_product_rel', 'product_id', 'prod_id', 
        string='Similar Recommended Prodcuts', domain=[('google_mcid', '!=', False)],
        help="Recommended if you want to provide your own product recommendations to be considered by our recommendation engine."
        " You can submit this attribute up to 10 times per item.")
    google_display_ads_title = fields.Char(string='Display Ads Tital', 
        help="Recommended if the title you want to use for an item in your dynamic remarketing campaign is "
        "different than the ‘title’ attribute you submit for Google Shopping.")
    google_display_ads_link = fields.Char(string='Display Ads Link', 
        help="Recommended if the URL you want to use for an item in your dynamic remarketing campaign is "
        "different than the ‘link’ attribute you submit for Google Shopping.")
    google_display_ads_value = fields.Float(string='Display Ads Value', 
        help="Optional attribute to indicate the margin of an item.")
    google_excluded_destination = fields.Boolean("Exclude from Dynamic Remarketing", default=False,
        help="If you are whitelisted for the Display Ads destination and you would like to exclude"
        " the item from showing in a dynamic remarketing campaign.")

    @api.multi
    def sync_product_with_gmc(self):
        self.env['google.merchant.center.service'].sync_product_with_gmc(self)

    @api.multi
    def delete_product_from_gmc(self):
        self.env['google.merchant.center.service'].delete_product_from_gmc(self)

    #Sync products automatically once after 25 days as it will need to resync after 1 motnh.
    @api.multi
    def resync_products_with_gmc(self):
        products = self.search([('sync_with_mc','=',True), ('google_mcid','!=',False), ('google_sync_date', '<=', fields.date.today() - timedelta(days=25)),], order='google_sync_date asc')
        _logger.info('Total products to be resynced------ %s', len(products))
        self.env['google.merchant.center.service'].sync_product_with_gmc(products)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################
from xmlrpc.client import Error
import logging
from odoo import api, fields, models, _
from odoo.addons.prestashop_odoo_bridge.models.prestapi import PrestaShopWebService,PrestaShopWebServiceDict
_logger = logging.getLogger(__name__)


class ExportPrestashopAttribute(models.TransientModel):
    _inherit = ['export.operation']
    _name = "export.prestashop.attribute"


    @api.model
    def export_now(self):
        context = self.env.context.copy() or {}
        map = []
        map_dict = {}
        type = 0
        add_data, add_value = False, False
        value = 0
        error_message = ''
        status = 'yes'
        for record in self:
            channel_id = record.channel_id
            try:
                prestashop = PrestaShopWebServiceDict(channel_id.prestashop_base_uri, channel_id.prestashop_api_key)
            except Exception as e:
                raise UserError(_('Error %s')%str(e))
            try:
                add_data = prestashop.get('product_options', options = {'schema': 'blank'})
            except Exception as e:
                raise UserError(_('Error %s')%str(e))
            try:
                add_value = prestashop.get('product_option_values', options = {'schema': 'blank'})
            except Exception as e:
                raise UserError(_('Error %s')%str(e))
            if prestashop and add_data and add_value:
                mapping_obj = self.env['channel.attribute.mappings']
                map_ids = mapping_obj.search([('channel_id', '=', self.channel_id.id)])
                for m in map_ids:
                    map.append(m.odoo_attribute_id)
                    map_dict.update({m.odoo_attribute_id:m.store_attribute_id})
                erp_pro = self.env['product.attribute'].search([]).ids
                if erp_pro:
                    for type_id in erp_pro:
                        obj_dimen_opt = self.env['product.attribute'].browse(type_id)
                        if type_id not in map:
                            name = obj_dimen_opt.name
                            create_dim_type = self.create_dimension_type(prestashop,
                             add_data, obj_dimen_opt, name)
                            type += 1
                        else:
                            presta_id = map_dict.get(type_id)
                            create_dim_type = [int(presta_id)]
                        if create_dim_type[0] == 0:
                            status = 'no'
                            error_message = error_message + create_dim_type[1]
                        else:
                            presta_id = create_dim_type[0]
                            for value_id in obj_dimen_opt.value_ids:
                                if not self.env['channel.attribute.value.mappings'].search([
                                    ('odoo_attribute_value_id', '=', value_id.id)]):
                                    name = self.env['product.attribute.value'].browse(value_id.id).name
                                    create_dim_opt = self.create_dimension_option(prestashop, type_id,
                                     add_value, presta_id, value_id, name)
                                    if create_dim_opt[0] == 0:
                                        status = 'no'
                                        error_message = error_message + create_dim_opt[1]
                                    else:
                                        value += 1
                if status == 'yes':
                    error_message += " %s Dimension(s) and their %s value(s) has been created. "%(type, value)
                if not erp_pro:
                    error_message = "No new Dimension(s) found !!!"
                return self.env['multi.channel.sale'].display_message(message = error_message)

    @api.multi
    def create_dimension_type(self, prestashop, add_data, erp_dim_type_id, name):
        if add_data:
            add_data['product_option'].update({
                                        'group_type': 'select',
                                        'position':'0'
                                    })
            if type(add_data['product_option']['name']['language']) == list:
                for i in range(len(add_data['product_option']['name']['language'])):
                    add_data['product_option']['name']['language'][i]['value'] = name
                    add_data['product_option']['public_name']['language'][i]['value'] = name
            else:
                add_data['product_option']['name']['language']['value'] = name
                add_data['product_option']['public_name']['language']['value'] = name
            try:
                returnid = prestashop.add('product_options', add_data)
            except Exception as e:
                return [0, ' Error in creating Dimension Type(ID: %s).%s'%(str(erp_dim_type_id), str(e))]
            if returnid:
                pid = returnid
                mapping_id = self.channel_id.create_attribute_mapping(erp_dim_type_id, pid)
                return [pid, '']

    @api.multi
    def create_dimension_option(self, prestashop, erp_attr_id, add_value, presta_attr_id, erp_dim_opt_id, name):
        if add_value:
            add_value['product_option_value'].update({
                                        'id_attribute_group': presta_attr_id,
                                        'position':'0'
                                    })
            if type(add_value['product_option_value']['name']['language']) == list:
                for i in range(len(add_value['product_option_value']['name']['language'])):
                    add_value['product_option_value']['name']['language'][i]['value'] = name
            else:
                add_value['product_option_value']['name']['language']['value'] = name
            try:
                returnid = prestashop.add('product_option_values', add_value)
            except Exception as e:
                return [0, ' Error in creating Dimension Option(ID: %s).%s'%(str(erp_dim_opt_id), str(e))]
            if returnid:
                pid = returnid
                mapping_id = self.channel_id.create_attribute_value_mapping(erp_dim_opt_id, pid)
                return [pid, '']

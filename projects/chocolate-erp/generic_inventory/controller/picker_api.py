import pytz
from odoo.addons.pos_sale_rest_api.controller.main import SalesAPIController
from odoo.addons.pos_sale_rest_api.controller.token_utils import validate_token
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError
import json
from datetime import datetime, timedelta


class PickerApi(SalesAPIController):
    @http.route('/picker/sale_all_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_all_picker_delivery_tasks(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('picker_id', '=', user.id), ('sale_id', '!=', False), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain).search(domain).filtered(lambda x: x.sale_id.date_order.date() == x.scheduled_date.date()).sorted(key='create_date',reverse=True)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'on_hand_qty': line.product_id.with_context(location=picking.location_id.id).qty_available,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason if line.task_state == 'reassigned' else '',
                        'reassign_qty': line.reassign_qty if line.task_state == 'reassigned' else 0,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "All Task fetched Successfully", picking_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/picker/history', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_all_picker_history(self):
        try:
            picker = getattr(request, 'validated_token', {})
            today = datetime.now().date()
            last_week = today - timedelta(days=7)
            domain = [('picker_id', '=', picker.id), ('task_state', 'in', ['picker_done', 'checker_verified']), 
                      ('create_date', '>=', last_week), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain)
            picking_list = []
            user_tz = pytz.timezone(picker.tz or 'UTC')
            for picking in pickings:
                picking_type = ''

                if picking.picking_type_id.code == 'outgoing':
                    sale_order = request.env['sale.order'].sudo().search([('name', '=', picking.origin)], limit=1)
                    if sale_order:
                        picking_date = picking.scheduled_date.date() if picking.scheduled_date else None
                        sale_date = sale_order.date_order.date() if sale_order.date_order else None
                        if picking_date == sale_date:
                            picking_type = 'Sale'
                        elif picking_date != sale_date:
                            picking_type = 'Scheduled'
                elif picking.picking_type_id.code == 'internal':
                    picking_type = 'Zone'
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin or picking.name,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'state': 'done' if (picking.task_state == 'checker_verified' and picking.state == 'done') else picking.state, 
                    'products': picking.move_ids_without_package.mapped('product_id.display_name'),
                    'date': picking.create_date.astimezone(user_tz).strftime('%d/%m/%Y %H:%M:%S'),
                    'type': picking_type,
                }
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "History fetched Successfully", picking_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))

    @http.route('/picker/sale_pending_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_pending_picker_delivery_tasks(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('picker_id', '=', user.id), ('task_state', '=', 'picker_pending'), ('sale_id', '!=', False), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "Pending Task fetched Successfully", picking_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/picker/sale_completed_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_completed_picker_delivery_tasks(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('picker_id', '=', user.id), ('state', '=', 'done'), ('sale_id', '!=', False)]
            pickings = request.env['stock.picking'].sudo().search(domain)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "Completed Task fetched Successfully", picking_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/picker/zone_all_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_all_picker_zone_transfer(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('picker_id', '=', user.id), ('picking_type_code', '=', 'internal'), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain).sorted(key='create_date', reverse=True)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin if picking.origin else picking.name,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'on_hand_qty': line.product_id.with_context(location=picking.location_id.id).qty_available,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason if line.task_state == 'reassigned' else '',
                        'reassign_qty': line.reassign_qty if line.task_state == 'reassigned' else 0,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "Task fetched Successfully", picking_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/picker/zone_pending_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_pending_picker_zone_transfer(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('picker_id', '=', user.id), ('task_state', '=', 'picker_pending'), ('picking_type_code', '=', 'internal'), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin if picking.origin else picking.name,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "Task fetched Successfully", picking_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/picker/zone_completed_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_completed_picker_zone_transfer(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('picker_id', '=', user.id), ('state', '=', 'done'), ('picking_type_code', '=', 'internal')]
            pickings = request.env['stock.picking'].sudo().search(domain)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin if picking.origin else picking.name,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "Task fetched Successfully", picking_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/picker/scheduled_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_all_scheduled_delivery_tasks(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('picker_id', '=', user.id), ('sale_id', '!=', False), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain).filtered(lambda x: x.sale_id.date_order.date() != x.scheduled_date.date()).sorted(key='scheduled_date', reverse=True)
            user_tz = pytz.timezone(user.tz or 'UTC')
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin,
                    'location_id': picking.location_id.id,
                    "picker_name": picking.picker_id.name,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state,
                    'scheduled_date': picking.scheduled_date.astimezone(user_tz).strftime('%d/%m/%Y'),
                    'scheduled_time': picking.scheduled_date.astimezone(user_tz).strftime('%H:%M:%S')
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'on_hand_qty': line.product_id.with_context(location=picking.location_id.id).qty_available,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason if line.task_state == 'reassigned' else '',
                        'reassign_qty': line.reassign_qty if line.task_state == 'reassigned' else 0,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "All Task fetched Successfully", picking_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/picker/pending_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_all_picker_pending_transfer(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('picker_id', '=', user.id), ('task_state', '=', 'picker_pending'), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin if picking.origin else picking.name,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'on_hand_qty': line.product_id.with_context(location=picking.location_id.id).qty_available,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason if line.task_state == 'reassigned' else '',
                        'reassign_qty': line.reassign_qty if line.task_state == 'reassigned' else 0,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "Pending Task fetched Successfully", picking_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/picker/completed_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_all_picker_completed_transfer(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('picker_id', '=', user.id), ('task_state', '=', 'picker_done'), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin if picking.origin else picking.name,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'on_hand_qty': line.product_id.with_context(location=picking.location_id.id).qty_available,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason if line.task_state == 'reassigned' else '',
                        'reassign_qty': line.reassign_qty if line.task_state == 'reassigned' else 0,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "Completed Task fetched Successfully", picking_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/picker/update_product_pick_status/<move_id>', type='http', auth='public', methods=['PATCH'], csrf=False)
    @validate_token
    def update_product_pick_status(self, move_id):
        try:
            if not move_id:
                return self._prepare_response(False, 400, None, None, "ID not passed.")
            if not isinstance(move_id, int):
                move_id = int(move_id)
            move_line = request.env['stock.move'].sudo().browse([move_id])
            move_line.sudo().write({
                'quantity': move_line.product_uom_qty,
                'task_state': 'picker_done'
            })
            return self._prepare_response(True, 200, "Success", None, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
    
    @http.route('/checker/update_product_verify_status/<move_id>', type='http', auth='public', methods=['PATCH'], csrf=False)
    @validate_token
    def update_product_verify_pick_status(self, move_id):
        try:
            if not move_id:
                return self._prepare_response(False, 400, None, None, "ID not passed.")
            if not isinstance(move_id, int):
                move_id = int(move_id)
            move_line = request.env['stock.move'].sudo().browse([move_id])
            move_line.sudo().write({
                'task_state': 'checker_verified'
            })
            return self._prepare_response(True, 200, "Success", None, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))

    @http.route('/picker/get_picker_locations', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_picker_locations(self):
        try:
            user = getattr(request, 'validated_token', {})
            locations = request.env['stock.location'].sudo().search([('picker_ids', '=', user.id)])
            location_list = [{'id': location.id, 'name': location.display_name} for location in locations]
            return self._prepare_response(True, 200, "Locations fetched Successfully", location_list, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
    
    @http.route('/picker/get_product_qty', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_product_qty(self):
        try:
            user = getattr(request, 'validated_token', {})
            location = request.env['stock.location'].sudo().search([('picker_id', '=', user.id)])
            if location:
                stock_quants = request.env['stock.quant'].sudo().search([('location_id', 'in', location.ids)], order='location_id')
                stock_quant_list = [
                    {
                        'product_id': quant.product_id.id,
                        'product_name': quant.product_id.display_name,
                        'on_hand_qty': quant.inventory_quantity_auto_apply,
                        'reserved_qty': quant.reserved_quantity,
                        'available_qty': quant.available_quantity,
                        'location_id': quant.location_id.id,
                        'location_name': quant.location_id.display_name,
                        'lot_id': quant.lot_id.id,
                        'lot_name': quant.lot_id.name,
                        'id': quant.id,
                        'show_actual_qty': user in user.company_id.allowed_user_ids
                    }
                    for quant in stock_quants
                ]
            else:
                stock_quant_list = []
            return self._prepare_response(True, 200, "Quantity fetched Successfully", stock_quant_list, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/checker/sale_all_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_all_checker_delivery_tasks(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('checker_id', '=', user.id), ('sale_id', '!=', False), ('state', '!=', 'cancel'), 
                      ('task_state', 'in', ['picker_done', 'checker_verified', 'reassigned'])]
            pickings = request.env['stock.picking'].sudo().search(domain)
            sale_orders = pickings.mapped('sale_id')
            sale_orders = sale_orders.sorted(key='date_order', reverse=True)
            task_list = []
            for sale_order in sale_orders:
                task_states = sale_order.picking_ids.mapped('task_state')
                done_states = sale_order.picking_ids.mapped('state')
                if any(state == 'picker_pending' for state in  task_states):
                    continue
                if task_states and all(state == 'picker_done' for state in task_states) and all(not picking.is_reassigned for picking in sale_order.picking_ids):
                    task_state = 'picker_done'
                elif task_states and all(state == 'checker_verified' for state in task_states) and all(state == 'done' for state in done_states):
                    task_state = 'done'
                elif task_states and all(state == 'checker_verified' for state in task_states):
                    task_state = 'checker_verified'
                elif task_states and (any(state == 'reassigned' for state in task_states) or (any(picking.is_reassigned for picking in sale_order.picking_ids) and all(state == 'picker_done' for state in task_states))):
                    task_state = 'reassigned'
                elif task_states and any(state == 'picker_pending' for state in task_states):
                    task_state = 'picker_pending'
                values = {
                    'sale_id': sale_order.id,
                    'order_no': sale_order.name,
                    'pickings': [],
                    'state': task_state
                }
                for picking in sale_order.picking_ids:
                    picking_values = {
                        'id': picking.id,
                        'order_no': picking.origin,
                        'location_id': picking.location_id.id,
                        'location_name': picking.location_id.display_name,
                        'location_dest_id': picking.location_dest_id.id,
                        'location_dest_name': picking.location_dest_id.display_name,
                        'product_lines': [],
                        'state': picking.task_state,
                        'picker_id': picking.picker_id.id,
                        'picker_name': picking.picker_id.name
                    }
                    for line in picking.move_ids_without_package:
                        line_values = {
                            'move_id': line.id,
                            'product_id': line.product_id.id,
                            'product_name': line.product_id.display_name,
                            'on_hand_qty': line.product_id.with_context(location=picking.location_id.id).qty_available,
                            'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                            'qty': line.product_uom_qty,
                            'uom_name': line.product_uom.name,
                            'uom_id': line.product_uom.id,
                            'state': line.task_state,
                            'reassign_reason': line.reassign_reason,
                            'reassign_qty': line.reassign_qty,
                            'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                            'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                        }
                        picking_values['product_lines'].append(line_values)
                    values['pickings'].append(picking_values)
                task_list.append(values)
            return self._prepare_response(True, 200, "All Task fetched Successfully", task_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/checker/pending_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_pending_checker_tasks(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('checker_id', '=', user.id), ('task_state', '=', 'picker_done'), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state,
                    'picker_id': picking.picker_id.id,
                    'picker_name': picking.picker_id.name
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "Pending Task fetched Successfully", picking_list, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/checker/completed_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_completed_checker_tasks(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('checker_id', '=', user.id), ('task_state', '=', 'checker_verified'), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state,
                    'picker_id': picking.picker_id.id,
                    'picker_name': picking.picker_id.name
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "Completed Task fetched Successfully", picking_list, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))

    @http.route('/checker/reassigned_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_reassigned_checker_tasks(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('checker_id', '=', user.id), ('task_state', '=', 'reassigned'), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state,
                    'picker_id': picking.picker_id.id,
                    'picker_name': picking.picker_id.name
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "Reassigned Task fetched Successfully", picking_list, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/checker/sale_pending_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_pending_checker_delivery_tasks(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('picker_id', '=', user.id), ('task_state', '=', 'picker_done'), ('sale_id', '!=', False), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state,
                    'picker_id': picking.picker_id.id,
                    'picker_name': picking.picker_id.name
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "Pending Task fetched Successfully", picking_list, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/checker/zone_all_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_all_checker_zone_transfer(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('checker_id', '=', user.id), ('picking_type_code', '=', 'internal'), ('state', '!=', 'cancel'),('task_state', 'in', ['picker_done','reassigned'])]
            pickings = request.env['stock.picking'].sudo().search(domain).sorted(key='create_date', reverse=True)
            picking_list = []
            for picking in pickings:
                state = picking.task_state
                done_state = picking.state
                if picking.is_reassigned and picking.task_state == 'picker_done':
                    state = 'reassigned'
                elif state and state == 'checker_verified' and done_state == 'done':
                    state = 'done'
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin if picking.origin else picking.name,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': state,
                    'picker_id': picking.picker_id.id,
                    'picker_name': picking.picker_id.name
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'on_hand_qty': line.product_id.with_context(location=picking.location_id.id).qty_available,
                        'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason,
                        'reassign_qty': line.reassign_qty,
                        'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                        'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "Task fetched Successfully", picking_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/checker/scheduled_delivery', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_all_checker_scheduled_delivery_tasks(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('checker_id', '=', user.id), ('sale_id', '!=', False), ('state', '!=', 'cancel'), 
                      ('task_state', 'in', ['picker_done', 'checker_verified', 'reassigned'])]
            pickings = request.env['stock.picking'].sudo().search(domain).filtered(lambda x: x.sale_id.date_order.date() != x.scheduled_date.date()).sorted(key='scheduled_date', reverse=True)
            sale_orders = pickings.mapped('sale_id')
            task_list = []
            user_tz = pytz.timezone(user.tz or 'UTC') 
            for sale_order in sale_orders:
                task_states = sale_order.picking_ids.mapped('task_state')
                done_states = sale_order.picking_ids.mapped('state')
                if any(state == 'picker_pending' for state in  task_states):
                    continue
                if task_states and all(state == 'picker_done' for state in task_states) and all(not picking.is_reassigned for picking in sale_order.picking_ids):
                    task_state = 'picker_done'
                elif task_states and all(state == 'checker_verified' for state in task_states) and all(state == 'done' for state in done_states):
                    task_state = 'done'
                elif task_states and all(state == 'checker_verified' for state in task_states):
                    task_state = 'checker_verified'
                elif task_states and (any(state == 'reassigned' for state in task_states) or (any(picking.is_reassigned for picking in sale_order.picking_ids) and all(state == 'picker_done' for state in task_states))):
                    task_state = 'reassigned'
                elif task_states and any(state == 'picker_pending' for state in task_states):
                    task_state = 'picker_pending'
                values = {
                    'sale_id': sale_order.id,
                    'order_no': sale_order.name,
                    'pickings': [],
                    'state': task_state,
                    'scheduled_date': sale_order.commitment_date.astimezone(user_tz).strftime('%d/%m/%Y') if sale_order.commitment_date else '',
                    'scheduled_time': sale_order.commitment_date.astimezone(user_tz).strftime('%H:%M:%S') if sale_order.commitment_date else ''
                }
                for picking in sale_order.picking_ids:
                    picking_values = {
                        'id': picking.id,
                        'order_no': picking.origin,
                        'location_id': picking.location_id.id,
                        'location_name': picking.location_id.display_name,
                        'location_dest_id': picking.location_dest_id.id,
                        'location_dest_name': picking.location_dest_id.display_name,
                        'product_lines': [],
                        'state': picking.task_state,
                        'picker_id': picking.picker_id.id,
                        'picker_name': picking.picker_id.name,
                        'scheduled_date': picking.scheduled_date.astimezone(user_tz).strftime('%d/%m/%Y'),
                        'scheduled_time': picking.scheduled_date.astimezone(user_tz).strftime('%H:%M:%S')
                    }
                    for line in picking.move_ids_without_package:
                        line_values = {
                            'move_id': line.id,
                            'product_id': line.product_id.id,
                            'product_name': line.product_id.display_name,
                            'on_hand_qty': line.product_id.with_context(location=picking.location_id.id).qty_available,
                            'expiry_date': line.restrict_lot_id.expiration_date.strftime('%d/%m/%Y') if line.restrict_lot_id.expiration_date else '',
                            'qty': line.product_uom_qty,
                            'uom_name': line.product_uom.name,
                            'uom_id': line.product_uom.id,
                            'state': line.task_state,
                            'reassign_reason': line.reassign_reason,
                            'reassign_qty': line.reassign_qty,
                            'lot_id': line.restrict_lot_id.id if line.restrict_lot_id else '',
                            'lot_name': line.restrict_lot_id.name if line.restrict_lot_id else ''
                        }
                        picking_values['product_lines'].append(line_values)
                    values['pickings'].append(picking_values)
                task_list.append(values)
            return self._prepare_response(True, 200, "All Scheduled Task fetched Successfully", task_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/checker/verify_picking/<picking_id>', type='http', auth='public', methods=['PATCH'], csrf=False)
    @validate_token
    def verify_picking(self, picking_id):
        try:
            if not picking_id:
                return self._prepare_response(False, 400, None, None, "ID not passed.")
            if not isinstance(picking_id, int):
                picking_id = int(picking_id)
            picking = request.env['stock.picking'].sudo().browse([picking_id])
            picking.sudo().button_validate()
            for move in picking.move_ids_without_package:
                move.write({
                    'task_state': 'checker_verified'
                })
            return self._prepare_response(True, 200, "Success", None, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/checker/verify_sale_picking/<sale_id>', type='http', auth='public', methods=['PATCH'], csrf=False)
    @validate_token
    def verify_sale_picking(self, sale_id):
        try:
            if not sale_id:
                return self._prepare_response(False, 400, None, None, "ID not passed.")
            if not isinstance(sale_id, int):
                sale_id = int(sale_id)
            pickings = request.env['stock.picking'].sudo().search([('sale_id', '=', sale_id)])
            for picking in pickings:
                picking.sudo().button_validate()
                for move in picking.move_ids_without_package:
                    move.write({
                        'task_state': 'checker_verified'
                    })
            return self._prepare_response(True, 200, "Success", None, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
    
    @http.route('/checker/reassign/<move_id>', type='http', auth='public', methods=['PATCH'], csrf=False)
    @validate_token
    def reassign_picker(self, move_id):
        try:
            data = json.loads(request.httprequest.data)
            if not data.get('note'):
                return self._prepare_response(False, 400, None, None, "Please provide Re assign reason")
            if not data.get('quantity'):
                return self._prepare_response(False, 400, None, None, "Please provide Re assign Quantity")
            if not move_id:
                return self._prepare_response(False, 400, None, None, "ID not passed.")
            if not isinstance(move_id, int):
                move_id = int(move_id)
            move = request.env['stock.move'].sudo().browse([move_id])
            move.write({
                'task_state': 'reassigned',
                'reassign_reason': data.get('note', ''),
                'reassign_qty': data.get('quantity', 0),
                'quantity': move.quantity - data.get('quantity', 0),
            })
            move.picking_id.write({
                'is_reassigned': True
            })
            return self._prepare_response(True, 200, "Success", None, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/picker/update_quantity/<id>', type='http', auth='public', methods=['PATCH'], csrf=False)
    @validate_token
    def update_stock_quantity(self, id):
        try:
            data = json.loads(request.httprequest.data)
            if not data.get('quantity'):
                return self._prepare_response(False, 400, None, None, "Required fields missing")
            if not id:
                return self._prepare_response(False, 400, None, None, "ID not passed.")
            if not isinstance(id, int):
                id = int(id)
            quant = request.env['stock.quant'].sudo().browse([id])
            if quant.product_id.tracking == 'lot' and not quant.lot_id:
                return self._prepare_response(False, 400, None, None, "Please select lot for the product which is tracked by lot")
            if not quant.exists():
                return self._prepare_response(False, 404, None, None, "Quant not found")
            if quant:
                quant.sudo().write({
                    'inventory_quantity': data['quantity']
                })
                quant.sudo().action_apply_inventory()

            return self._prepare_response(True, 200, "Quantity updated successfully", None, None)

        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))    

    @http.route('/picker/receipts_all_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_all_picker_receipts_tasks(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('picker_id', '=', user.id), ('purchase_id', '!=', False), ('state', '!=', 'cancel')]
            pickings = request.env['stock.picking'].sudo().search(domain).sorted(key='create_date',reverse=True)
            picking_list = []
            for picking in pickings:
                picking_values = {
                    'id': picking.id,
                    'order_no': picking.origin,
                    'location_id': picking.location_id.id,
                    'location_name': picking.location_id.display_name,
                    'location_dest_id': picking.location_dest_id.id,
                    'location_dest_name': picking.location_dest_id.display_name,
                    'product_lines': [],
                    'state': picking.task_state
                }
                for line in picking.move_ids_without_package:
                    line_values = {
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'qty': line.product_uom_qty,
                        'uom_name': line.product_uom.name,
                        'uom_id': line.product_uom.id,
                        'state': line.task_state,
                        'reassign_reason': line.reassign_reason if line.task_state == 'reassigned' else '',
                        'reassign_qty': line.reassign_qty if line.task_state == 'reassigned' else 0,
                    }
                    picking_values['product_lines'].append(line_values)
                picking_list.append(picking_values)
            return self._prepare_response(True, 200, "All Task fetched Successfully", picking_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))  
        
    @http.route('/checker/receipts_all_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_all_checker_receipts_tasks(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('checker_id', '=', user.id), ('purchase_id', '!=', False), ('state', '!=', 'cancel'), 
                      ('task_state', 'in', ['picker_done', 'checker_verified', 'reassigned'])]
            pickings = request.env['stock.picking'].sudo().search(domain).sorted(key='create_date',reverse=True)
            purchase_orders = pickings.mapped('purchase_id')
            task_list = []
            for purchase_order in purchase_orders:
                task_states = purchase_order.picking_ids.mapped('task_state')
                if any(state == 'picker_pending' for state in  task_states):
                    continue
                if task_states and all(state == 'picker_done' for state in task_states) and all(not picking.is_reassigned for picking in purchase_order.picking_ids):
                    task_state = 'picker_done'
                elif task_states and all(state == 'checker_verified' for state in task_states):
                    task_state = 'checker_verified'
                elif task_states and (any(state == 'reassigned' for state in task_states) or (any(picking.is_reassigned for picking in purchase_order.picking_ids) and all(state == 'picker_done' for state in task_states))):
                    task_state = 'reassigned'
                elif task_states and any(state == 'picker_pending' for state in task_states):
                    task_state = 'picker_pending'
                values = {
                    'purchase_id': purchase_order.id,
                    'order_no': purchase_order.name,
                    'pickings': [],
                    'state': task_state
                }
                for picking in purchase_order.picking_ids:
                    picking_values = {
                        'id': picking.id,
                        'order_no': picking.origin,
                        'location_id': picking.location_id.id,
                        'location_name': picking.location_id.display_name,
                        'location_dest_id': picking.location_dest_id.id,
                        'location_dest_name': picking.location_dest_id.display_name,
                        'product_lines': [],
                        'state': picking.task_state,
                        'picker_id': picking.picker_id.id,
                        'picker_name': picking.picker_id.name
                    }
                    for line in picking.move_ids_without_package:
                        line_values = {
                            'move_id': line.id,
                            'product_id': line.product_id.id,
                            'product_name': line.product_id.display_name,
                            'qty': line.product_uom_qty,
                            'uom_name': line.product_uom.name,
                            'uom_id': line.product_uom.id,
                            'state': line.task_state,
                            'reassign_reason': line.reassign_reason,
                            'reassign_qty': line.reassign_qty,
                        }
                        picking_values['product_lines'].append(line_values)
                    values['pickings'].append(picking_values)
                task_list.append(values)
            return self._prepare_response(True, 200, "All Task fetched Successfully", task_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/picker/update_receipt_product_pick_status/<move_id>', type='http', auth='public', methods=['PATCH'], csrf=False)
    @validate_token
    def update_receipt_product_pick_status(self, move_id):
        try:
            if not move_id:
                return self._prepare_response(False, 400, None, None, "ID not passed.")
            if not isinstance(move_id, int):
                move_id = int(move_id)
            data = json.loads(request.httprequest.data)
            move_line = request.env['stock.move'].sudo().browse([move_id])
            if data.get('expiry_date'):
                if move_line.sudo().product_id.use_expiration_date:
                    line = request.env['stock.move.line'].sudo().search([('move_id', '=', move_line.id)])
                    if line:
                        line.write({'expiration_date': data.get('expiry_date')})
            move_line.sudo().write({
                'quantity': move_line.product_uom_qty,
                'task_state': 'picker_done',
            })
            return self._prepare_response(True, 200, "Success", None, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/checker/verify_purchase_receipt/<purchase_id>', type='http', auth='public', methods=['PATCH'], csrf=False)
    @validate_token
    def verify_purchase_receipt(self, purchase_id):
        try:
            if not purchase_id:
                return self._prepare_response(False, 400, None, None, "ID not passed.")
            if not isinstance(purchase_id, int):
                purchase_id = int(purchase_id)
            pickings = request.env['stock.picking'].sudo().search([('purchase_id', '=', purchase_id)])
            for picking in pickings:
                picking.write({'grn_received': True})
                for move in picking.move_ids_without_package:
                    move.write({
                        'task_state': 'checker_verified',
                    })
            return self._prepare_response(True, 200, "Success", None, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))


    @http.route('/checker_picker/pending_tasks', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_all_pending_task_count(self):
        try:
            user = getattr(request, 'validated_token', {})
            Picking = request.env['stock.picking'].sudo()

            picker_domain = [
                ('picker_id', '=', user.id),
                ('task_state', '=', 'picker_pending'),
                ('state', '!=', 'cancel')
            ]
            checker_domain = [
                ('checker_id', '=', user.id),
                ('state', 'not in', ['cancel', 'done']),
                ('task_state', 'in', ['picker_done', 'checker_verified', 'reassigned'])
            ]

            picker_pickings = Picking.search(picker_domain)
            checker_pickings = Picking.search(checker_domain)

            picker_zone_domain = [
                ('picker_id', '=', user.id),
                ('task_state', '=', 'picker_pending'),
                ('picking_type_code', '=', 'internal'),
                ('state', '!=', 'cancel')
            ]
            picker_zone_pickings = Picking.search(picker_zone_domain)
            picker_zone_count = len(picker_zone_pickings)

            picker_pending_sale = Picking.search_count([
                ('picker_id', '=', user.id),
                ('task_state', '=', 'picker_pending'),
                ('sale_id', '!=', False),
                ('state', '!=', 'cancel')
            ])

            picker__pending_scheduled_domain = [
                ('picker_id', '=', user.id),
                ('sale_id', '!=', False),
                ('state', '!=', 'cancel'),
                ('task_state', '=', 'picker_pending'),
            ]
             
            picker_pending_scheduled_pickings = Picking.search(picker__pending_scheduled_domain)
            picker_pending_scheduled_delivery = len(picker_pending_scheduled_pickings.filtered(
                lambda p: p.sale_id and p.sale_id.date_order and p.scheduled_date and
                            p.sale_id.date_order.date() != p.scheduled_date.date()
                )
            )
 
            picker_receipts_domain = [
                ('picker_id', '=', user.id),
                ('purchase_id', '!=', False),
                ('state', '!=', 'cancel'),
                ('task_state', '=', 'picker_pending'),
            ]
            picker_receipts_pickings = Picking.search(picker_receipts_domain)
            picker_receipts_tasks = len(picker_receipts_pickings)


            checker_receipts_domain = [
                ('checker_id', '=', user.id),
                ('purchase_id', '!=', False),
                ('state', '!=', 'cancel'),
                ('grn_received', '=', False)
            ]
            checker_receipts_pickings = Picking.search(checker_receipts_domain)
            checker_receipts_tasks = len(checker_receipts_pickings)

            

            checker_pending_sale = Picking.search_count([
                ('checker_id', '=', user.id),
                ('task_state', 'in', ['picker_done', 'checker_verified', 'reassigned']),
                ('sale_id', '!=', False),
                ('state', 'not in', ['cancel', 'done'], )
            ])

            checker_pending_zone_domain = [
                ('checker_id', '=', user.id),
                ('picking_type_code', '=', 'internal'),
                ('state', 'not in', ['cancel', 'done']),
                ('task_state', 'in', ['picker_done', 'checker_verified', 'reassigned'])
            ]
            checker_zone_pickings = Picking.search(checker_pending_zone_domain)
            checker_pending_zone_count = len(checker_zone_pickings)

            checker_pending_scheduled_domain = [
                ('checker_id', '=', user.id),
                ('sale_id', '!=', False),
                ('state', 'not in', ['cancel', 'done']),
                ('task_state', 'in', ['picker_done', 'checker_verified', 'reassigned']),
            ]

            checker_scheduled_delivery = Picking.search(checker_pending_scheduled_domain)
            checker_pending_scheduled_delivery = len(checker_scheduled_delivery)

            return self._prepare_response(True, 200, "Pending Task Count fetched Successfully", {
                'name': user.name,
                'picker_sale_invoice_count': picker_pending_sale,
                'picker_zone_count': picker_zone_count,
                'picker_pending_scheduled_delivery': picker_pending_scheduled_delivery,
                'picker_receipts_tasks': picker_receipts_tasks,
                'checker_receipts_tasks': checker_receipts_tasks,
                'checker_sale_invoice_count': checker_pending_sale,
                'checker_pending_zone_count': checker_pending_zone_count,
                'checker_pending_scheduled_delivery': checker_pending_scheduled_delivery,
            }, None)

        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
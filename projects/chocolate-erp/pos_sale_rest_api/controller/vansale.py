from datetime import date, timedelta, datetime, time
from . token_utils import validate_token
from . main import SalesAPIController
from odoo import http, fields
from odoo.http import request, Controller
from odoo.exceptions import AccessError, ValidationError
import json
import base64
import magic
import calendar
import pytz



class VanSalesAPIController(SalesAPIController):
    @http.route('/van/trip_routes', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_van_trip_routes(self, **kwargs):
        try:
            domain = [('date', '=', date.today())]
            user = getattr(request, 'validated_token', {})
            sales_person = kwargs.get('salesperson_id', user.id)
            if sales_person:
                domain += [('salesperson_id', '=', int(sales_person))]
            salesperson_trip = request.env['sales.person.trip'].sudo().search(domain)
            route_lines = salesperson_trip.route_ids
            routes = route_lines.mapped('route_id')
            route_list = []
            for route in routes:
                route_values = {
                    'id': route.id,
                    'name': route.name,
                    'shop_ids': []
                }
                for line in route_lines:
                    route_values['shop_ids'].append({
                        'id': line.shop_id.id,
                        'name': line.shop_id.name,
                        'order_taken': line.order_taken if line.order_taken else '',
                    })
                route_list.append(route_values)
            return self._prepare_response(True, 200, "Routes fetched Successfully", route_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/routes', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_van_routes(self, **kwargs):
        try:
            user = getattr(request, 'validated_token', {})
            sales_person = kwargs.get('salesperson_id', user.id)
            domain = []
            if sales_person:
                domain += [('salesperson_id', '=', int(sales_person))]
            routes = request.env['sales.route.assignment'].sudo().search(domain).mapped('route_ids')
            routes_list = []
            for route in routes:
                route_values = {
                    'id': route.id,
                    'name': route.name,
                    'shop_ids': []
                }
                for shop in route.shops_ids:
                    route_values['shop_ids'].append({
                        'id': shop.id,
                        'name': shop.name,
                    })
                routes_list.append(route_values)
            return self._prepare_response(True, 200, "Routes fetched Successfully", routes_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/start_trip', type='http', auth='public', methods=['POST'], csrf=False)
    @validate_token
    def create_van_login(self):
        try:
            data = json.loads(request.httprequest.data)
            start_kilometer = data.get('start_kilometer', None)
            start_km_image = data.get('start_image', None)
            start_location_id = data.get('start_location_id', None)
            user = getattr(request, 'validated_token', {})
            sales_person = data.get('salesperson_id', user.id)
            if request.env['sales.person.trip'].sudo().search([('salesperson_id', '=', sales_person), ('date', '=', date.today())]):
                return self._prepare_response(False, 400, "User already has a trip started", None, None)
            if not start_kilometer:
                return self._prepare_response(False, 400, "Missing start kilometer", None, None)
            values = {
                'start_kilometer': start_kilometer,
                'start_location_id': start_location_id,
                'date': date.today(),
                'salesperson_id': data.get('salesperson_id', user.id),
                'start_km_image': start_km_image
            }
            salesperson_route = request.env['sales.route.assignment'].sudo().search([('salesperson_id', '=', user.id)])
            if not salesperson_route:
                return self._prepare_response(False, 400, "No route assigned for this user", None, None)
            van_login = request.env['sales.person.trip'].sudo().create(values)
            van_login.action_start()
            return self._prepare_response(
                True, 201, "Trip Started", None, None
                )        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/end_trip', type='http', auth='public', methods=['POST'], csrf=False)
    @validate_token
    def create_van_end_trip(self):
        try:
            data = json.loads(request.httprequest.data)
            end_kilometer = data.get('end_kilometer', None)
            end_km_image = data.get('end_image', None)
            end_location_id = data.get('end_location_id', None)
            user = getattr(request, 'validated_token', {})
            sales_person = data.get('salesperson_id', user.id)
            trip = request.env['sales.person.trip'].sudo().search([('salesperson_id', '=', sales_person), ('date', '=', date.today())])
            if not end_kilometer:
                return self._prepare_response(False, 400, "Missing end kilometer", None, None)
            if not end_km_image:
                return self._prepare_response(False, 400, "Missing end kilometer image", None, None)
            if not trip:
                return self._prepare_response(False, 400, "No trip started for this user", None, None)
            if trip:
                trip.write({
                    'end_location_id': end_location_id,
                    'end_kilometer': end_kilometer,
                    'end_km_image': end_km_image,
                })
                trip.action_stop()            
            return self._prepare_response(
                True, 201, "Trip Ended", None, None
                )        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/sales_history', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_van_sales_history(self, **kwargs):
        try:
            domain = [('state', '=', 'sale')]
            user = getattr(request, 'validated_token', {})
            product_id = kwargs.get('product_id', None)
            partner_id = kwargs.get('customer_id', None)
            today = date.today()
            date_str = kwargs.get('date', None)
            if date_str:
                today = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            domain += [('date_order', '>=', start_of_day), ('date_order', '<=', end_of_day)]
            user_id = kwargs.get('salesperson_id', user.id)
            id = kwargs.get('id', None)
            if user_id:
                domain += [('user_id', '=', int(user_id))]
            if product_id:
                domain += [('order_line.product_id', '=', int(product_id))]
            if partner_id:
                domain += [('partner_id', '=', int(partner_id))]
            if id:
                domain += [('id', '=', int(id))]

            sale_orders = request.env['sale.order'].sudo().search(domain, order='id DESC')
            sale_history = []
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            user_tz = pytz.timezone(user.tz or 'UTC')
            for sale_order in sale_orders:
                invoices = sale_order.invoice_ids.filtered(lambda x: x.line_ids.sale_line_ids.order_id == sale_order)
                sale_values = {
                    'order_id': sale_order.id,
                    'order': sale_order.name,
                    'order_date': sale_order.date_order.astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S'),
                    'customer_id': sale_order.partner_id.id,
                    'customer': sale_order.partner_id.name,
                    'amount_untaxed': sale_order.amount_untaxed,
                    'amount_tax': sale_order.amount_tax,
                    'amount_total': sale_order.amount_total,
                    'amount_invoiced': sale_order.amount_invoiced,
                    'amount_due': sum(invoices.mapped('amount_residual')),
                    'margin': sale_order.margin,
                    'order_lines': [],
                    'invoice_ids': [{'id': invoice.id, 'name': invoice.name} for invoice in invoices],
                    }
                order_lines = sale_order.order_line
                if kwargs.get('product_id'):
                    order_lines.filtered(lambda x: x.product_id.id == int(product_id))
                for line in order_lines:
                    sale_values['order_lines'].append({
                        'id': line.id,
                        'product': line.product_id.id,
                        'product_code': line.product_id.default_code,
                        'product_name': line.product_id.display_name,
                        'quantity': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'purchase_price': line.purchase_price,
                        'margin': line.margin,
                        'sub_total': line.price_subtotal,
                        'price_tax': line.price_tax,
                        'price_total': line.price_total,
                        'discount':line.discount,
                        'discount_amount':line.discount_amount,
                        'lot_id': line.lot_id.id,
                        'lot_name': line.lot_id.name,
                        'image_url': f'{base_url}/web/image?model=product.product&id={line.product_id.id}&field=image_1920' if line.product_id.image_1920 else '',
                        'uom_id': line.product_uom.id,
                        'uom_name': line.product_uom.name
                        })
                sale_history.append(sale_values)    
            return self._prepare_response(True, 200, "Sales history fetched Successfully", sale_history, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/purchase_history', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_van_purchase_history(self, **kwargs):
        try:
            domain = [('state', '=', 'sale')]
            product_id = kwargs.get('product_id', None)
            partner_id = kwargs.get('customer_id', None)
            user_id = kwargs.get('salesperson_id', None)
            id = kwargs.get('id', None)
            if user_id:
                domain += [('user_id', '=', int(user_id))]
            if product_id:
                domain += [('order_line.product_id', '=', int(product_id))]
            if partner_id:
                domain += [('partner_id', '=', int(partner_id))]
            if id:
                domain += [('id', '=', int(id))]

            base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
            sale_orders = request.env['sale.order'].sudo().search(domain, order='id DESC')
            user = getattr(request, 'validated_token', {})
            user_tz = pytz.timezone(user.tz or 'UTC')
            sale_history = []
            for sale_order in sale_orders:
                sale_values = {
                    'order_id': sale_order.id,
                    'order': sale_order.name,
                    'order_date': sale_order.date_order.astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S'),
                    'customer_id': sale_order.partner_id.id,
                    'customer': sale_order.partner_id.name,
                    'amount_untaxed': sale_order.amount_untaxed,
                    'amount_tax': sale_order.amount_tax,
                    'amount_total': sale_order.amount_total,
                    'amount_invoiced': sale_order.amount_invoiced,
                    'amount_due': sum(sale_order.invoice_ids.mapped('amount_residual')),
                    'margin': sale_order.margin,
                    'order_lines': [],
                    }
                order_lines = sale_order.order_line
                if kwargs.get('product_id'):
                    order_lines.filtered(lambda x: x.product_id.id == int(product_id))
                for line in order_lines:
                    sale_values['order_lines'].append({
                        'id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'default_code': line.product_id.default_code if line.product_id.default_code else '',
                        'image': f"{base_url}/web/image/product.product/{line.product_id.id}/image_1920" if line.product_id.id else '',
                        'quantity': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'purchase_price': line.purchase_price,
                        'margin': line.margin,
                        'discount':line.discount,
                        'discount_amount':line.discount_amount,
                        'sub_total': line.price_subtotal,
                        'price_tax': line.price_tax,
                        'price_total': line.price_total,
                        'lot_id' : line.lot_id.id if line.lot_id else '',
                        'lot_name' : line.lot_id.name if line.lot_id else '',
                        'uom_id': line.product_uom.id,
                        'uom_name': line.product_uom.name
                        })
                sale_history.append(sale_values)
            return self._prepare_response(True, 200, "Customer Purchases history fetched Successfully", sale_history, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/sales_target', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_sales_target(self, **kwargs):
        try:
            user = getattr(request, 'validated_token', {})
            today = date.today()
            domain = [('start_date', '<=', today), ('end_date', '>=', today), ('commission_plan_salesperson_id.salesperson_id', '=', user.id)]
            sales_targets = request.env['salesperson.target.line'].sudo().search(domain)
            start_date = today.replace(day=1)
            end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
            invoice_bonus = request.env['incentive.bonus'].sudo().search([('sales_person', '=', user.id), ('date', '>=', start_date), ('date', '<=', end_date)])
            sale_orders = request.env['sale.order'].sudo().search([('user_id', '=',user.id), ('state', '=', 'sale'), ('date_order', '>=', start_date), ('date_order', '<=', end_date)])
            total_sales_amount = sum(sale_orders.mapped('amount_total')) if sale_orders else 0
            target_amount = sum(sales_targets.mapped('target_amount')) if sales_targets else 0
            percentage = 0
            if target_amount > 0:
                percentage = round((total_sales_amount / target_amount) * 100, 2)
            target_value = {
                'target': target_amount,
                'sales_amount': total_sales_amount,
                'percentage': percentage,
                'incentive': sum(invoice_bonus.mapped('incentive_bonus')),
            }
            return self._prepare_response(True, 200, "Target fetched Successfully", target_value, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/customer', type='http', auth='public', methods=['POST'], csrf=None)
    @validate_token
    def create_van_customer(self):
        try:
            user = getattr(request, 'validated_token', {})
            data = json.loads(request.httprequest.data)
            name = data.get('name')
            mobile = data.get('mobile')
            company_type = data.get('company_type')
            route_id = data.get('route_id')
            customer_code = data.get('customer_code', None)

            if not customer_code:
                return self._prepare_response(False, 400, "", None, "Missing customer code")
                    
            if not name:
                return self._prepare_response(
                    False, 400, "", None, "Missing name"
                )
            
            if not mobile:
                return self._prepare_response(
                    False, 400, "", None, "Missing mobile"
                )
            
            if not company_type:
                return self._prepare_response(
                    False, 400, "", None, "Missing company type"
                )
        
            if company_type not in ['person', 'company']:
                return self._prepare_response(
                    False, 400, "", None, "Company type should be either person or company"
                )
            
            if not route_id:
                return self._prepare_response(
                    False, 400, "", None, "Missing Route"
                )
        
            # Validate partner exists
            partner = request.env['res.partner'].sudo().search([('mobile', '=', mobile)]).exists()
            if partner:
                return self._prepare_response(
                    False, 409, "", None, "A customer with this mobile already exists"
                )
            
            partner = request.env['res.partner'].sudo().search([('customer_code', '=', customer_code)]).exists()
            if partner:
                return self._prepare_response(
                    False, 409, "", None, "A customer with this code already exists"
                )
            
            child_list = []
            for record in data.get('child_ids', []):
                if not record.get('type'):
                    return self._prepare_response(
                        False, 400, "", None, "Missing Address Type"
                    )
                if record.get('type') not in ['contact', 'invoice', 'delivery', 'other']:
                    return self._prepare_response(
                        False, 400, "", None, "Address Type should be either contact/ invoice/ delivery/ other"
                    )
                child_list.append(
                    {
                        'name': record.get('name'),
                        'type': record.get('type'),
                        'phone': record.get('phone'),
                        'mobile': record.get('mobile'),
                        'email': record.get('email'),
                        'company_type': record.get('company_type'),
                        'customer_rank': 1,
                        'company_id': record.get('company_id'),
                        'street': record.get('street'),
                        'street2': record.get('street2'),
                        'zip': record.get('zip'),
                        'city': record.get('city'),
                        'country_id': record.get('country_id'),
                        'state_id': record.get('state_id'),
                        'vat': record.get('vat'),
                        'route_id': route_id,
                        'customer_code': record.get('customer_code'),
                    }
                )
            values = {
                'name': name,
                'phone': data.get('phone'),
                'mobile': mobile,
                'email': data.get('email'),
                'company_type': company_type,
                'customer_rank': 1,
                'company_id': data.get('company_id'),
                'street': data.get('street'),
                'street2': data.get('street2'),
                'zip': data.get('zip'),
                'city': data.get('city'),
                'country_id': data.get('country_id'),
                'state_id': data.get('state_id'),
                'vat': data.get('vat'),
                'child_ids': [(0, 0, child) for child in child_list],
                'route_id': route_id,
                'customer_code': data.get('customer_code'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'cr_number': data.get('cr_number')
            }
            # Create customer
            customer = request.env['res.partner'].sudo().create(values)
            customer.message_post(body="Customer created by Van Sales API")
            payload_data = {
                    'customer_id': customer.id,
                    'name': customer.name,
                }
            
            return self._prepare_response(
                True, 201, "Customer created", payload_data, None
                )
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        

    @http.route('/van/product', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_product_details(self, **kwargs):
        try:
            domain = [('sale_ok', '=', True)]
            p_id = kwargs.get('id', None)
            user = getattr(request, 'validated_token', {})
            today = date.today()
            offer_domain = [('start_date', '<=', today), ('end_date', '>=', today)]
            product_offers = request.env['product.offer'].sudo().search(offer_domain)
            salesperson_route = request.env['sales.route.assignment'].sudo().search([('salesperson_id', '=', user.id)])
            van_branch_id = salesperson_route.van_id.company_id.id
            
            if not van_branch_id:
                return self._prepare_response(False, 404, "", None, "User is not associated with Van")
                
            warehouse = request.env['stock.warehouse'].sudo().search([('company_id', '=', van_branch_id)])
            if not warehouse:
                return self._prepare_response(False, 404, "", None, "Invalid warehouse")
                
            locations = request.env['stock.location'].sudo().search([('warehouse_id', '=', warehouse.id), ('usage', '=', 'internal')])
            product_ids = request.env['product.product'].sudo().search([])

            base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
            product_list = []

            if p_id:
                products_to_process = product_ids.sudo().filtered(lambda x: x.id == int(p_id))
                if not products_to_process:
                    return self._prepare_response(False, 404, "", None, "Product not found")
            else:
                products_to_process = product_ids
                
            for product in products_to_process:
                stock_quants = request.env['stock.quant'].sudo().search([
                    ('product_id', '=', product.id),
                    ('location_id', 'in', locations.ids)
                ])
                
                lot_data = []
                for quant in stock_quants:
                    if quant.lot_id:
                        lot_data.append({
                            'id': quant.lot_id.id,
                            'name': quant.lot_id.name,
                            'expiry': quant.lot_id.expiration_date.strftime('%Y-%m-%d') if quant.lot_id.expiration_date else '',
                            'on_hand': quant.quantity,
                            'location_id':quant.location_id.id,
                            'location_name': quant.location_id.display_name,
                            'purchase_price': quant.lot_id.standard_price + quant.lot_id.margin,
                        })
                available_uom = product.product_uom_ids
                product_offer = product_offers.filtered(lambda po: po.product_id.id == product.id)
                discount = 0
                offer_id = False
                if product_offer:
                    discount = product_offer[0].discount_percentage
                    offer_id = product_offer[0].id
                product_list.append({
                    'id': product.id,
                    'name': product.display_name,
                    'default_code': product.default_code if product.default_code else '',
                    'barcode': product.barcode if product.barcode else '',
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'product_template_variant_value_ids': product.product_template_variant_value_ids.ids,
                    'type': product.type,
                    'invoice_policy': product.invoice_policy,
                    'is_storable': product.is_storable,
                    'list_price': product.list_price,
                    'standard_price': product.standard_price,
                    'taxes_id': product.taxes_id.ids,
                    'supplier_taxes_id': product.supplier_taxes_id.ids,
                    'categ_id': product.categ_id.id,
                    'image': f"{base_url}/web/image/product.product/{product.id}/image_1920" if product.id else '',
                    'tracking': product.tracking,
                    'lots': lot_data if lot_data else [],
                    'expense_policy': product.expense_policy,
                    'purchase_method': product.purchase_method,
                    'uom_id': product.uom_id.id,
                    'uom_ids': [{'id': uom.id, 'name': uom.name} for uom in available_uom],
                    'uom_name': product.uom_id.name,
                    'price_locked':True if product.is_price_locked else False,
                    'discount': discount,
                    'offer_id': offer_id,
                })
            return self._prepare_response(True, 200, "Product Fetched successfully", product_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))



    @http.route('/van/available_products', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_available_product_details(self, **kwargs):
        try:
            user = getattr(request, 'validated_token', {})
            today = date.today()
            domain = [('start_date', '<=', today), ('end_date', '>=', today)]
            product_offers = request.env['product.offer'].sudo().search(domain)
            company_id = user.company_id.id if user and user.company_id else None

            if not company_id:
                return self._prepare_response(False, 404, "", None, "User is not associated with any company")

            internal_locations = request.env['stock.location'].sudo().search([
                ('usage', '=', 'internal'),
                ('company_id', '=', company_id)
            ])
            if not internal_locations:
                return self._prepare_response(True, 200, "No internal locations found", [], None)

            stock_quants = request.env['stock.quant'].sudo().search([
                ('location_id', 'in', internal_locations.ids),
                ('available_quantity', '>', 0)
            ])

            product_ids_in_stock = list(set(stock_quants.mapped('product_id.id')))

            
            product_ids = product_ids_in_stock

            if not product_ids:
                return self._prepare_response(True, 200, "No products with available stock", [], None)

            products_to_process = request.env['product.product'].sudo().browse(product_ids)
            base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")

            product_list = []

            for product in products_to_process:
                product_quants = stock_quants.filtered(lambda q: q.product_id.id == product.id)

                lot_data = []
                for quant in product_quants:
                    if quant.lot_id:
                        lot_data.append({
                            'id': quant.lot_id.id,
                            'name': quant.lot_id.name,
                            'expiry': quant.lot_id.expiration_date.strftime('%Y-%m-%d') if quant.lot_id.expiration_date else '',
                            'on_hand': quant.quantity,
                            'location_id': quant.location_id.id,
                            'location_name': quant.location_id.display_name,
                            'purchase_price': quant.lot_id.standard_price + quant.lot_id.margin,
                        })

                available_uom = product.product_uom_ids
                product_offer = product_offers.filtered(lambda po: po.product_id.id == product.id)
                discount = 0
                offer_id = False
                if product_offer:
                    discount = product_offer[0].discount_percentage
                    offer_id = product_offer[0].id
                product_list.append({
                    'id': product.id,
                    'name': product.display_name,
                    'default_code': product.default_code or '',
                    'barcode': product.barcode or '',
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'product_template_variant_value_ids': product.product_template_variant_value_ids.ids,
                    'type': product.type,
                    'invoice_policy': product.invoice_policy,
                    'is_storable': product.is_storable,
                    'list_price': product.list_price,
                    'standard_price': product.standard_price,
                    'taxes_id': product.taxes_id.ids,
                    'supplier_taxes_id': product.supplier_taxes_id.ids,
                    'categ_id': product.categ_id.id,
                    'image': f"{base_url}/web/image/product.product/{product.id}/image_1920",
                    'tracking': product.tracking,
                    'lots': lot_data,
                    'expense_policy': product.expense_policy,
                    'purchase_method': product.purchase_method,
                    'uom_id': product.uom_id.id,
                    'uom_ids': [{'id': uom.id, 'name': uom.name} for uom in available_uom],
                    'uom_name': product.uom_id.name,
                    'price_locked': True if product.is_price_locked else False,
                    'discount': discount,
                    'offer_id': offer_id,
                })

            return self._prepare_response(True, 200, "Products with available stock fetched successfully", product_list, None)

        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))


    @http.route('/van/product/search', type='http', auth='public', methods=['GET'])
    @validate_token
    def search_product_details(self, **kwargs):
        try:
            domain = [('sale_ok', '=', True)]
            
            keyword = kwargs.get('keyword', '').strip()
            if keyword:
                domain.append('|')
                domain.append('|')
                domain.append(('name', 'ilike', keyword))
                domain.append(('default_code', 'ilike', keyword))
                domain.append(('barcode', 'ilike', keyword))

            products = request.env['product.product'].sudo().search(domain)
            if not products:
                return self._prepare_response(True, 200, "No products found", [], None)
            
            user = getattr(request, 'validated_token', {})
            salesperson_route = request.env['sales.route.assignment'].sudo().search([('salesperson_id', '=', user.id)], limit=1)
            van_branch_id = salesperson_route.van_id.company_id.id if salesperson_route else None
            if not van_branch_id:
                return self._prepare_response(False, 404, "", None, "User is not associated with Van")
            
            warehouse = request.env['stock.warehouse'].sudo().search([('company_id', '=', van_branch_id)], limit=1)
            if not warehouse:
                return self._prepare_response(False, 404, "", None, "Invalid warehouse")
            
            locations = request.env['stock.location'].sudo().search([('warehouse_id', '=', warehouse.id), ('usage', '=', 'internal')])
            location_ids = locations.ids

            base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
            product_list = []
            for product in products:
                stock_quants = request.env['stock.quant'].sudo().search([
                    ('product_id', '=', product.id),
                    ('location_id', 'in', location_ids)
                ])
                lot_data = [{
                    'id': quant.lot_id.id,
                    'name': quant.lot_id.name,
                    'expiry': quant.lot_id.expiration_date.strftime('%Y-%m-%d') if quant.lot_id.expiration_date else '',
                    'on_hand': quant.quantity,
                    'location_id': quant.location_id.id,
                    'location_name': quant.location_id.display_name,
                    'purchase_price': quant.lot_id.standard_price + quant.lot_id.margin,
                } for quant in stock_quants if quant.lot_id]

                available_uom = product.product_uom_ids
                product_list.append({
                    'id': product.id,
                    'name': product.display_name,
                    'default_code': product.default_code if product.default_code else '',
                    'barcode': product.barcode if product.barcode else '',
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'product_template_variant_value_ids': product.product_template_variant_value_ids.ids,
                    'type': product.type,
                    'invoice_policy': product.invoice_policy,
                    'is_storable': product.is_storable,
                    'list_price': product.list_price,
                    'standard_price': product.standard_price,
                    'taxes_id': product.taxes_id.ids,
                    'supplier_taxes_id': product.supplier_taxes_id.ids,
                    'categ_id': product.categ_id.id,
                    'image': f"{base_url}/web/image/product.product/{product.id}/image_1920" if product.id else '',
                    'tracking': product.tracking,
                    'lots': lot_data if lot_data else [],
                    'expense_policy': product.expense_policy,
                    'purchase_method': product.purchase_method,
                    'uom_id': product.uom_id.id,
                    'uom_ids': [{'id': uom.id, 'name': uom.name} for uom in available_uom],
                    'uom_name': product.uom_id.name
                })

            return self._prepare_response(True, 200, "Products fetched successfully", product_list, None)

        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))


        
    @http.route('/van/payment_history', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_customer_payment_history(self, **kwargs):
        try:
            domain = [('state', '=', 'paid')]
            customer_id = kwargs.get('customer_id', None)
            if customer_id:
                domain.append(('partner_id', '=', int(customer_id)))
            if not customer_id:
                return self._prepare_response(
                    False, 400, "", None, "Missing customer"
                )
            payments = request.env['account.payment'].sudo().search(domain)
            payment_history_list = []
            for payment in payments:
                payment_history_list.append({
                    'id': payment.id,
                    'name': payment.name,
                    'amount': payment.amount,
                    'date': payment.date.strftime('%Y-%m-%d'),
                    'memo': payment.memo,
                    'invoice_ids': payment.invoice_ids.ids,
                    'journal_id': payment.journal_id.id,
                    'journal': payment.journal_id.name
                })
            return self._prepare_response(True, 200, "Success", payment_history_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/due_amount', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_customer_due_amount(self, **kwargs):
        try:
            domain = [('amount_residual', '>', 0), ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')]
            customer_id = kwargs.get('customer_id', None)
            if customer_id:
                domain.append(('partner_id', '=', int(customer_id)))
            if not customer_id:
                return self._prepare_response(
                    False, 400, "", None, "Missing customer"
                )
            invoices = request.env['account.move'].sudo().search(domain, order='id DESC')
            total_due = sum(invoices.mapped('amount_residual'))
            total_paid = sum(invoices.mapped('amount_paid'))
            due_list = []
            for invoice in invoices:
                due_list.append({
                    'invoice_id': invoice.id,
                    'number': invoice.name,
                    'due_date': invoice.invoice_date_due.strftime('%Y-%m-%d'),
                    'amount_residual': invoice.sudo().amount_residual,
                })
            return self._prepare_response(True, 200, "Success", due_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/invoices', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_customer_invoice_history(self, **kwargs):
        try:
            domain = [('move_type', '=', 'out_invoice')]
            customer_id = kwargs.get('customer_id', None)
            if customer_id:
                domain.append(('partner_id', '=', int(customer_id)))
            invoices = request.env['account.move'].sudo().search(domain, order='invoice_date DESC')
            invoice_list = []
            for invoice in invoices:
                invoice_list.append({
                    'id': invoice.id,
                    'name': invoice.name,
                    'total_amount': invoice.amount_total,
                    'date': invoice.date.strftime('%Y-%m-%d'),
                    'paid': sum(invoice.matched_payment_ids.filtered(lambda x: x.state == 'paid').mapped('amount')),
                    'due': invoice.amount_residual
                })
            return self._prepare_response(True, 200, "Success", invoice_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))


    @http.route('/van/due_summary', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_invoice_summary(self, **kwargs):
        try:
            domain = [('move_type', '=', 'out_invoice')]
            partner_id = kwargs.get('customer_id', None)
            if partner_id:
                domain.append(('partner_id', '=', int(partner_id)))
            else:
                return self._prepare_response(
                    False, 400, "", None, "Missing customer"
                )
            invoices = request.env['account.move'].sudo().search(domain)
            total_residual = sum(invoices.mapped('amount_residual'))
            last_transaction_date = None
            last_transaction = request.env['sale.order'].sudo().search(
                [('partner_id', '=', int(partner_id)),('invoice_status', '=', 'invoiced') ],
                order='date_order DESC',
                limit=1
            )
            if last_transaction:
                last_transaction_date = last_transaction.date_order.strftime('%Y-%m-%d %H:%M:%S')

            result = {
                'total_residual': total_residual,
                'last_transaction_date': last_transaction_date
            }

            return self._prepare_response(True, 200, "Success", result, None)

        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))

        
    @http.route('/van/invoice', type='http', auth='public', methods=['POST'], csrf=False)
    @validate_token
    def create_van_invoice(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
            sale_order_id = data.get('sale_order_id', None)
            if not sale_order_id:
                return self._prepare_response(False, 400, None, None, "Missing sale order")
            sale_order = request.env['sale.order'].sudo().browse([sale_order_id])
            if not sale_order:
                return self._prepare_response(False, 400, None, None, "Invalid sale order")
            sale_order._create_invoices()
            for invoice in sale_order.invoice_ids:
                invoice.message_post(body="Invoice created by Van Sales API")
                invoice.action_post()
            return self._prepare_response(True, 201, "Invoice created", None, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/payment_terms', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_payment_terms(self, **kwargs):
        try:
            domain = []
            payment_terms = request.env['account.payment.term'].sudo().search(domain)
            payment_term_list = []
            for payment_term in payment_terms:
                payment_term_list.append({
                    'id': payment_term.id,
                    'name': payment_term.name
                })
            return self._prepare_response(True, 200, "Success", payment_term_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/payment', type='http', auth='public', methods=['POST'], csrf=False)
    @validate_token
    def create_payment(self):
        try:
            user = getattr(request, 'validated_token', {})
            data = json.loads(request.httprequest.data)
            payment_method_id = data.get('payment_method_id', None)
            if not payment_method_id:
                return self._prepare_response(False, 400, "", None, "Missing payment method")
            payment_amount = data.get('payment_amount', None)
            if not payment_amount:
                return self._prepare_response(False, 400, "", None, "Missing payment amount")
            invoice_ids = data.get('invoice_ids', None)
            if not invoice_ids:
                return self._prepare_response(False, 400, "", None, "Missing invoice ids")
            partner_id = data.get('customer_id', None)
            if not partner_id:
                return self._prepare_response(False, 400, "", None, "Missing customer")
            invoices = request.env['account.move'].sudo().browse(invoice_ids)
            payload = []
            journal = request.env['account.journal'].sudo().browse([int(payment_method_id)])
            if payment_amount > sum(invoices.mapped('amount_residual')):
                return self._prepare_response(False, 400, "", None, "Payment amount exceeds invoice balance")
            for invoice in invoices:
                amount = invoice.amount_residual if invoice.amount_residual < payment_amount else payment_amount
                payment_values = {
                    'invoice_ids': [(6, 0, [invoice.id])],
                    'payment_type': 'inbound',
                    'partner_id': invoice.partner_id.id,
                    'amount': amount,
                    'journal_id': int(payment_method_id),
                    'activity_user_id': user.id,
                    'memo': invoice.name
                }
                payment = request.env['account.payment'].sudo().create(payment_values)
                payment.sudo().action_post()
                payment.sudo().action_validate()
                payment.message_post(body="Payment created by Van Sales API")
                # Payment reconcilation with invoice
                json_invoice_outstanding_data = []
                if invoice.invoice_outstanding_credits_debits_widget:
                    json_invoice_outstanding_data = (
                        invoice.invoice_outstanding_credits_debits_widget.get("content", [])
                    )
                for data in json_invoice_outstanding_data:
                    if data.get("move_id") in payment.mapped('move_id').ids:
                        invoice.js_assign_outstanding_line(line_id=data.get("id"))
                payload.append({
                    'id': payment.id,
                    'name': payment.name,
                })
            return self._prepare_response(True, 201, "Payment Successfull", payload, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        

    @http.route('/van/quotation', type='http', auth='public', methods=['POST'], csrf=False)
    @validate_token
    def van_quotation(self):
        try:
            user = getattr(request, 'validated_token', {})
            salesperson_route = request.env['sales.route.assignment'].sudo().search([('salesperson_id', '=', user.id)])
            data = json.loads(request.httprequest.data)
            partner_id = data.get('customer_id')
            order_lines = data.get('order_lines', [])
            sale_type = 'vansale'
            if not partner_id:
                    return self._prepare_response(
                        False, 400, "", None, "Missing partner_id"
                    )
                
            if not order_lines:
                return self._prepare_response(
                    False, 400, "", None, "No order lines provided"
                )
            
            partner = request.env['res.partner'].browse(partner_id).exists()
            if not partner:
                return self._prepare_response(
                    False, 404, "", None, "Invalid partner"
                )
            van_branch_id = salesperson_route.van_id.company_id.id
            if not van_branch_id:
                return self._prepare_response(False, 404, "", None, "User is not associated with Van")
            warehouse = request.env['stock.warehouse'].sudo().search([('company_id', '=', van_branch_id)])
            if not warehouse:
                return self._prepare_response(False, 404, "", None, "Invalid warehouse")
            sale_order_vals = {
                'partner_id': partner_id,
                'company_id': van_branch_id or user.company_id.id,
                'user_id': user.id,
                'client_order_ref': data.get('customer_reference', ''),
                'state': 'draft',
                'order_line': [],
                "sale_type": sale_type,
                "payment_term_id": data.get('payment_term', None),
                'warehouse_id': warehouse.id
            }
            # Validate and prepare order lines
            for line in order_lines:
                product_id = line.get('product_id')
                quantity = line.get('product_uom_qty', 1)
                price_unit = line.get('price_unit')
                lot = line.get('lot_id', None)
                
                # Validate product
                product = request.env['product.product'].browse(product_id).exists()
                if not product:
                    return self._prepare_response(False, 400, None, None, f'Invalid product ID: {product_id}')
                if product.tracking == 'lot' and not line.get('lot_id', None):
                    return self._prepare_response(
                        False, 400, None, None, f'Missing lot for product: {product.name}'
                    )
                lot = request.env['stock.lot'].sudo().browse([lot])
                if not lot:
                    return self._prepare_response(False, 400, None, None, f'Invalid lot ID: {lot}')
                if lot.product_id != product:
                    return self._prepare_response(False, 400, None, None, f'Invalid lot for product: {product.name}')
                purchase_price = line.get('purchase_price', None) or lot.standard_price
                sale_order_vals['order_line'].append((0, 0, {
                    'product_id': product_id,
                    'product_uom_qty': quantity,
                    'price_unit': price_unit or product.list_price,
                    'name': product.name,
                    'discount': line.get('discount', 0),
                    'discount_fixed': line.get('discount_fixed', 0),
                    'offer_id': line.get('offer_id', None),
                    'product_uom': line.get('uom_id') if line.get('uom_id') else product.uom_id.id,
                    'lot_id': line.get('lot_id'),
                    'purchase_price': purchase_price if purchase_price else 0,
                }))
                    
            # Create Quotation
            sale_order = request.env['sale.order'].sudo().create(sale_order_vals)
            global_discount = data.get('global_discount_percentage', 0.0)
            global_discount_amount = data.get('global_discount_amount', 0.0)
            if global_discount > 0:
                subtotal = sum(line.price_subtotal for line in sale_order.order_line)
                discount_amount = subtotal * (global_discount / 100)
                company = sale_order.company_id
                discount_product = sale_order.company_id.sale_discount_product_id
                if not discount_product:
                    discount_product = request.env['product.product'].sudo().create({  # created discount product
                        'name': 'Discount',
                        'type': 'service',
                        'invoice_policy': 'order',
                        'company_id': company.id,
                        'taxes_id': [(6, 0, [])],
                        'list_price': 0.0,
                        'sale_ok': True,
                        'purchase_ok': False,
                    })
                order_line_vals = {
                    'order_id': sale_order.id,
                    'product_id': discount_product.id,
                    'name': f'Discount {global_discount}%',
                    'price_unit': -discount_amount,
                    'product_uom_qty': 1,
                    'product_uom': discount_product.uom_id.id,
                    'tax_id': [(6, 0, [])],
                    'is_discount': True
                }

                request.env['sale.order.line'].sudo().create(order_line_vals)
            if global_discount_amount > 0:
                company = sale_order.company_id
                discount_product = sale_order.company_id.sale_discount_product_id
                if not discount_product:
                    discount_product = request.env['product.product'].sudo().create({  # created discount product
                        'name': 'Discount',
                        'type': 'service',
                        'invoice_policy': 'order',
                        'company_id': company.id,
                        'taxes_id': [(6, 0, [])],
                        'list_price': 0.0,
                        'sale_ok': True,
                        'purchase_ok': False,
                    })
                order_line_vals = {
                    'order_id': sale_order.id,
                    'product_id': discount_product.id,
                    'name': discount_product.name,
                    'price_unit': -global_discount_amount,
                    'product_uom_qty': 1,
                    'name': 'Discount',
                    'product_uom': discount_product.uom_id.id,
                    'tax_id': [(6, 0, [])],
                    'is_discount': True
                }

                request.env['sale.order.line'].sudo().create(order_line_vals)
            sale_order.message_post(body="Quotation created From Van Sales")
            today = date.today()
            domain = [('salesperson_id', '=', user.id), ('date', '=', today)]
            trip = request.env['sales.person.trip'].sudo().search(domain)
            if trip:
                shop = trip.route_ids.filtered(lambda r: r.shop_id.id == partner_id)
                if shop:
                    shop.sudo().write({'order_taken': 'yes'})
            payload_data = {
                'order_id': sale_order.id,
                'order_name': sale_order.name
                }
            return self._prepare_response(True, 201, "Quotation Created", payload_data, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/sale_order/<order_id>', type='http', auth='public', methods=['PATCH'], csrf=False)
    @validate_token
    def van_sale_order(self, order_id):
        try:
            user = getattr(request, 'validated_token', {})
            data = json.loads(request.httprequest.data)
            if not order_id:
                return self._prepare_response(False, 400, None, None, "Order ID not passed.")
            if not isinstance(order_id, int):
                order_id = int(order_id)
            sale_order = request.env['sale.order'].sudo().browse([order_id])
            if not sale_order:
                return self._prepare_response(False, 404, None, None, "Invalid order ID")
            sale_order.action_confirm()
            for picking in sale_order.picking_ids:
                for move_line in picking.move_ids:
                    move_line.quantity = move_line.product_uom_qty
                picking.sudo().button_validate()
            sale_order._create_invoices()
            for invoice in sale_order.invoice_ids:
                invoice.action_post()
            payload_data = {
                'order_id': sale_order.id,
                'order_name': sale_order.name,
                'invoices': [{'id': invoice.id, 'name': invoice.name} for invoice in sale_order.invoice_ids]
                }
            return self._prepare_response(True, 200, "Sale Order Created", payload_data, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/quotation/<order_id>', type='http', auth='public', methods=['PATCH'], csrf=False)
    @validate_token
    def update_quotation(self, order_id):
        try:
            user = getattr(request, 'validated_token', {})
            if not order_id:
                return self._prepare_response(False, 400, None, None, "Order ID not passed.")
            if not isinstance(order_id, int):
                order_id = int(order_id)
            sale_order = request.env['sale.order'].sudo().browse([order_id])
            if not sale_order:
                return self._prepare_response(False, 404, None, None, "Invalid order ID")
            data = json.loads(request.httprequest.data)
            payment_term_id = data.get('payment_term_id', None)
            if payment_term_id:
                sale_order.payment_term_id = payment_term_id
            
            order_lines = data.get('order_lines', [])
            for line in order_lines:
                if 'id' in line and line.get('remove'):  # Remove line
                    line_to_remove = sale_order.order_line.filtered(lambda l: l.id == line['id'])
                    if line_to_remove:
                        line_to_remove.sudo().unlink()
                elif 'id' in line:  # Update existing line
                    line_to_update = sale_order.order_line.filtered(lambda l: l.id == line['id'])
                    if line_to_update:
                        values = {}
                        if line.get('product_id'):
                            values['product_id'] = line['product_id']
                        if line.get('lot_id'):
                            values['lot_id'] = line['lot_id']
                            lot = request.env['stock.lot'].sudo().browse([int(line['lot_id'])])
                            values['purchase_price'] = lot.standard_price
                        if line.get('product_uom_qty'):
                            values['product_uom_qty'] = line['product_uom_qty']
                        if line.get('uom_id'):
                            values['product_uom'] = line['uom_id']
                        if line.get('price_unit'):
                            values['price_unit'] = line['price_unit']
                        line_to_update.sudo().write(values)
                else:  # Add new line
                    product_id = line.get('product_id')
                    quantity = line.get('product_uom_qty', 1)
                    price_unit = line.get('price_unit')
                    
                    # Validate product
                    product = request.env['product.product'].sudo().browse(product_id).exists()
                    if not product:
                        return self._prepare_response(False, 400, None, None, f'Invalid product ID: {product_id}')
                    if product.tracking == 'lot' and not line.get('lot_id', None):
                        return self._prepare_response(
                            False, 400, None, None, f'Missing lot for product: {product.name}'
                        )
                    lot = request.env['stock.lot'].sudo().browse([int(line.get('lot_id'))])
                    purchase_price = line.get('purchase_price', None) or lot.standard_price
                    sale_order.sudo().write({
                        'order_line': [
                            (0, 0, {
                                'product_id': product_id,
                                'product_uom_qty': quantity,
                                'price_unit': price_unit or product.list_price,
                                'name': product.name,
                                'discount': line.get('discount', 0),
                                'offer_id': line.get('offer_id', False),
                                'product_uom': line.get('uom_id') if line.get('uom_id') else product.uom_id.id,
                                'lot_id': line.get('lot_id'),
                                'purchase_price': purchase_price if purchase_price else 0,
                            })
                        ]
                    })
            return self._prepare_response(True, 200, "Success", None, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))

    @http.route('/van/sale_order', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_van_sale_order(self, **kwargs):
        try:
            id = kwargs.get('id', None)
            if not id:
                return self._prepare_response(
                    False, 400, "", None, "Sale Order Id is Missing"
                )
            sale_values = {}
            sale_order = request.env['sale.order'].sudo().browse([int(id)])
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            invoices = sale_order.invoice_ids.filtered(lambda x: x.line_ids.sale_line_ids.order_id == sale_order)
            if sale_order:
                sale_values = {
                    'id': sale_order.id,
                    'name': sale_order.name,
                    'partner_id': sale_order.partner_id.id,
                    'partner_name': sale_order.partner_id.name,
                    'date_order': sale_order.date_order.strftime('%Y-%m-%d %H:%M:%S'),
                    'amount_untaxed': sale_order.amount_untaxed,
                    'amount_tax': sale_order.amount_tax,
                    'amount_total': sale_order.amount_total,
                    'amount_invoiced': sale_order.amount_invoiced,
                    'amount_due': sum(invoices.mapped('amount_residual')),
                    'margin': sale_order.margin,
                    'order_lines': [],
                    'invoice_ids': [{'id': invoice.id, 'name': invoice.name} for invoice in invoices],
                }
                for line in sale_order.order_line:
                    sale_values['order_lines'].append({
                        'id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'quantity': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'tax_ids': line.tax_id.ids,
                        'discount': line.discount,
                        'margin': line.margin,
                        'price_subtotal': line.price_subtotal,
                        'purchase_price': line.purchase_price,
                        'discount_amount':line.discount_amount,
                        'sub_total': line.price_subtotal,
                        'price_tax': line.price_tax,
                        'price_total': line.price_total,
                        'lot_id': line.lot_id.id,
                        'lot_name': line.lot_id.name,
                        'image_url': f'{base_url}/web/image?model=product.product&id={line.product_id.id}&field=image_1920' if line.product_id.image_1920 else '',
                        'uom_id': line.product_uom.id,
                        'uom_name': line.product_uom.name
                    })
            return self._prepare_response(True, 200, "Success", sale_values, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/sale_order_delivery', type='http', auth='public', methods=['POST'], csrf=False)
    @validate_token
    def van_sale_order_delivery(self):
        try:
            user = getattr(request, 'validated_token', {})
            data = json.loads(request.httprequest.data)
            order_id = data.get('sale_order_id', None)
            sale_order = request.env['sale.order'].sudo().search([('id', '=', order_id), ('state', '=', 'sale')])
            if not sale_order:
                return self._prepare_response(False, 404, None, None, "Invalid order ID or Sale is not confirmed")
            for picking in sale_order.picking_ids:
                picking.button_validate()
                picking.message_post(body="Delivery confirmed by Van Sales")
            return self._prepare_response(True, 201, "Delivered", None, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        

    @http.route('/van/sales_profit', type='http', auth='public', methods=['GET'], csrf=False)
    @validate_token
    def van_sales_profit(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('user_id', '=', user.id)]
            today = date.today()
            target_domain = [('start_date', '<=', today), ('end_date', '>=', today), ('commission_plan_salesperson_id.salesperson_id', '=', user.id)]
            sales_targets = request.env['salesperson.target.line'].sudo().search(target_domain, limit=1)
            if not sales_targets:
                return self._prepare_response(False, 400, None, None, "No sales target found for today")
            start_date = datetime.combine(sales_targets.start_date, time.min)
            end_date = datetime.combine(sales_targets.end_date, time.max)
            if sales_targets:
                domain += [('date_order', '>=', start_date), ('date_order', '<=', end_date), ('invoice_status', '=', 'invoiced')]
            sale_orders = request.env['sale.order'].sudo().search(domain)
            profit = sum(sale_orders.mapped('margin'))
            payload = {
                'profit': profit
            }
            return self._prepare_response(True, 200, "", payload, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
    
    @http.route('/van/trip_status', type='http', auth='public', methods=['GET'], csrf=False)
    @validate_token
    def van_sales_trip_status(self):
        try:
            user = getattr(request, 'validated_token', {})
            today = date.today()
            domain = [('salesperson_id', '=', user.id), ('date', '=', today)]
            trip = request.env['sales.person.trip'].sudo().search(domain)
            values = {
                'trip_started': False,
                'trip_ended': False
            }
            if trip:
                values = {
                    'id': trip.id,
                    'date': trip.date.strftime('%Y-%m-%d'),
                    'start_kilometer': trip.start_kilometer,
                    'end_kilometer': trip.end_kilometer,
                    'sales_amount': trip.sales_amount,
                    'collected_amount': trip.collected_amount,
                    'route_ids': [],
                    'trip_started': True,
                    'trip_ended': True if trip.state == 'ended' else False,
                }

                for line in trip.route_ids:
                    values['route_ids'].append({
                        'id': line.id,
                        'route_id': line.route_id.id,
                        'route': line.route_id.name,
                        'shop_id': line.shop_id.id,
                        'shop': line.shop_id.name,
                        'order_taken': line.order_taken if line.order_taken else '',
                        'no_order_reason_id': line.no_order_reason_id.id if line.no_order_reason_id else None,
                        'no_order_reason': line.no_order_reason_id.name if line.no_order_reason_id else None,
                    })
            return self._prepare_response(True, 200, "", values, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/location_status', type='http', auth='public', methods=['PATCH'], csrf=False)
    @validate_token
    def update_location_status(self, **kwargs):
        try:
            user = getattr(request, 'validated_token', {})
            today = date.today()
            domain = [('salesperson_id', '=', user.id), ('date', '=', today)]
            trip = request.env['sales.person.trip'].sudo().search(domain)
            shop_id = kwargs.get('shop_id', None)
            data = json.loads(request.httprequest.data)
            if not shop_id:
                return self._prepare_response(False, 400, "", None, "Shop is missing")
            shop = request.env['sales.person.trip.line'].sudo().search([('shop_id', '=', int(shop_id)), ('sale_person_trip_id', '=', trip.id)])
            if not shop:
                return self._prepare_response(False, 404, "", None, "Shop not found in the trip")
            if shop:
                values = {
                    'order_taken': data.get('order_taken')
                }
                no_order_reason = data.get('no_order_reason_id', None)
                if no_order_reason:
                    values['no_order_reason_id'] = int(no_order_reason)
                other_reason = data.get('reason', None)
                if other_reason:
                    values['reason'] = other_reason
                shop.write(values)
            return self._prepare_response(True, 200, "Location Status Upadted", None, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))

    @http.route('/van/route_status', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_route_status(self, **kwargs):
        try:
            user = getattr(request, 'validated_token', {})
            today = date.today()
            domain = [('salesperson_id', '=', user.id), ('date', '=', today)]
            trip = request.env['sales.person.trip'].sudo().search(domain)
            if not trip:
                return self._prepare_response(False, 404, "", None, "Trip not found")
            route_id = kwargs.get('route_id', None)
            if not route_id:
                return self._prepare_response(False, 400, "", None, "Route is missing")
            routes = request.env['sales.person.trip.line'].sudo().search([('route_id', '=', int(route_id)), ('sale_person_trip_id', '=', trip.id)])
            route_status = []
            start_date = datetime.combine(today, time.min)
            end_date = datetime.combine(today, time.max)
            for route in routes:
                order_completed = False
                sale_order = request.env['sale.order'].sudo().search([('partner_id', '=', route.shop_id.id), ('state', '=', 'sale'), ('invoice_status', '=', 'invoiced'), 
                                                                      ('date_order', '>=', start_date), ('date_order', '<=', end_date), ('invoice_ids.payment_state', 'in', ['paid', 'in_payment'])])
                if sale_order:
                    order_completed = True
                route_status.append({
                    'shop_id': route.shop_id.id,
                    'shop': route.shop_id.name,
                    'order_taken': route.order_taken if route.order_taken else '',
                    'no_order_reason_id': route.no_order_reason_id.id if route.no_order_reason_id else None,
                    'no_order_reason': route.no_order_reason_id.name if route.no_order_reason_id else None,
                    'reason': route.reason if route.reason else None,
                    'order_completed': order_completed
                })
            return self._prepare_response(True, 200, "Success", route_status, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
     

    @http.route('/van/sales_return', type='http', auth='public', methods=['POST'], csrf=False)
    @validate_token
    def van_sale_return(self):
        try:
            user = getattr(request, 'validated_token', {})
            data = json.loads(request.httprequest.data)
            order_id = data.get('sale_order_id', None)
            if not order_id:
                return self._prepare_response(False, 400, None, None, "Sale order ID is missing")
            return_lines = data.get('return_lines', [])
            if not return_lines:
                return self._prepare_response(False, 400, None, None, "Return lines are missing")
            sale_order = request.env['sale.order'].sudo().search([('id', '=', order_id), ('state', '=', 'sale')])
            if not sale_order:
                return self._prepare_response(False, 404, None, None, "Invalid order ID or Sale is not confirmed")
            return_values = {
                'partner_id': sale_order.partner_id.id,
                'date': date.today(),
                'user_id': user.id,
                'sale_order_id': sale_order.id,
                'company_id': sale_order.company_id.id,
            }
            sale_return = request.env['sale.return'].sudo().create(return_values)
            sale_return.message_post(body="Sale Return created from Van Sales")
            return_sale_line_ids = [line['sale_line_id'] for line in return_lines]
            if sale_return:
                sale_return.user_id = user.id
                for return_line in sale_return.return_line_ids:
                    if return_line.sale_order_line_id.id not in return_sale_line_ids:
                        return_line.unlink()
                        continue
                    passed_return_line = next((line for line in return_lines if line['sale_line_id'] == return_line.sale_order_line_id.id), None)
                    return_line.quantity = passed_return_line.get('quantity')
            sale_return.request_approval()
            sale_return.approve()
            sale_return.confirm()
            return self._prepare_response(True, 201, "Returned", None, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/sales_returns', type='http', auth='public', methods=['GET'], csrf=False)
    @validate_token
    def get_van_sales_returns(self, **kwargs):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('state', '=', 'done')]
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            domain.append(('user_id', '=', user.id))
            today = date.today()
            date_str = kwargs.get('date', None)
            if date_str:
                today = datetime.strptime(date_str, "%Y-%m-%d").date()
            domain.append(('date', '=', today))
            partner_id = kwargs.get('customer_id', None)
            if partner_id:
                domain.append(('partner_id', '=', int(partner_id)))
            sales_returns = request.env['sale.return'].sudo().search(domain)
            sales_return_list = []
            for sale_return in sales_returns:
                return_vals = {
                    'id': sale_return.id,
                    'name': sale_return.display_name,
                    'order_id': sale_return.sale_order_id.id,
                    'order': sale_return.sale_order_id.name,
                    'partner_id': sale_return.partner_id.id,
                    'partner': sale_return.partner_id.name,
                    'date': sale_return.date.strftime('%Y-%m-%d'),
                    'create_date': sale_return.create_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'return_lines': []   
                }
                for line in sale_return.return_line_ids:
                    sale_line = line.sale_order_line_id
                    account_move_line = sale_return.credit_note_ids.invoice_line_ids.filtered(lambda x: x.sale_return_line_id == line)
                    return_vals['return_lines'].append({
                        'sale_line_id': line.sale_order_line_id.id,
                        'product_id': line.product_id.id,
                        'product': line.product_id.display_name,
                        'quantity': line.quantity,
                        'uom_id': line.uom_id.id,
                        'uom': line.uom_id.name,
                        'price_unit': sale_line.price_unit,
                        'lot_id': sale_line.lot_id.id,
                        'lot_name': sale_line.lot_id.name,
                        'total': account_move_line.price_total if account_move_line else 0,
                        'image_url': f'{base_url}/web/image?model=product.product&id={line.product_id.id}&field=image_1920' if line.product_id.image_1920 else '',
                    })
                sales_return_list.append(return_vals)
            return self._prepare_response(True, 200, "Success", sales_return_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e)) 

    @http.route('/van/expenses', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_van_sales_expenses(self, **kwargs):
        try:
            user = getattr(request, 'validated_token', {})
            employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
            user_tz = pytz.timezone(user.tz or 'UTC')
            if not employee_id:
                return self._prepare_response(False, 400, None, None, "Employee not found for this user")
            domain = [('employee_id', '=', employee_id.id)]
            id = kwargs.get('id', None)
            if id:
                domain.append(('id', '=', int(id)))
            expenses = request.env['hr.expense'].sudo().search(domain, order='date DESC')
            if not expenses:
                return self._prepare_response(False, 404, None, None, "No expenses found")
            expense_list = []
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            for expense in expenses:
                attachments = expense.attachment_ids
                expense_list.append({
                    'id': expense.id,
                    'description': expense.name,
                    'category_id': expense.product_id.id,
                    'category': expense.product_id.display_name,
                    'amount': expense.total_amount_currency,
                    'date': expense.create_date.astimezone(user_tz).strftime('%Y-%m-%d %H %M %S'),
                    'employee_id': expense.employee_id.id,
                    'employee': expense.employee_id.name,
                    'kilometer': expense.kilometer,
                    'attachments' : [ {'id': attachment.id, 'file_name' : attachment.name, 'url': base_url+attachment.image_src if attachment.image_src else ''} for attachment in attachments ]
                })
            return self._prepare_response(True, 200, "Success", expense_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/expense', type='http', auth='public', methods=['POST'], csrf=False)
    @validate_token
    def create_van_sale_expenses(self):
        try:
            user = getattr(request, 'validated_token', {})
            data = json.loads(request.httprequest.data)
            product_id = data.get('category_id', None)
            if not product_id:
                return self._prepare_response(False, 400, None, None, "Category ID is missing")
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
            if not employee:
                return self._prepare_response(False, 400, None, None, "Employee not found for this user")
            product = request.env['product.product'].sudo().browse(product_id)
            name = data.get('name') or product.name
            kilometer = data.get('kilometer') 
            values = {
                'total_amount_currency': data.get('amount'),
                'product_id': data.get('category_id'),
                'description': data.get('note'),
                'name': name,
                'employee_id': employee.id,
                'kilometer' : kilometer
                
            }
            expense = request.env['hr.expense'].sudo().create(values)
            expense.message_post(body="Expense created from Van Sales")
            for attachment in data.get('attachment_ids'):
                decoded_attachment = base64.b64decode(attachment.get('data'))
                file_name = attachment.get('file_name')
                file_type = magic.from_buffer(decoded_attachment, mime=True)
                encoded_data = base64.b64encode(decoded_attachment).decode('utf-8')
                request.env['ir.attachment'].sudo().create({
                    'name': file_name,
                    'type': 'binary',
                    'datas': encoded_data,
                    'res_model': 'hr.expense',
                    'res_id': expense.id, 
                    'mimetype': file_type
                })
            expense.action_submit_expenses()
            payload_data = {
                'id': expense.id,
                'date': expense.date.strftime('%Y-%m-%d')
                }
            return self._prepare_response(True, 201, "Success", payload_data, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/expense_category', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_expense_category(self, **kwargs):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('can_be_expensed', '=', True)]
            categories = request.env['product.product'].sudo().search(domain)
            category_list = []
            for category in categories:
                category_list.append({
                    'id': category.id,
                    'name': category.name
                })
            return self._prepare_response(True, 200, "Success", category_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/odometer_history', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_odometer_history(self):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('salesperson_id', '=', user.id)]
            trips = request.env['sales.person.trip'].sudo().search(domain, order='date DESC')
            trip_list = []
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            user_tz = pytz.timezone(user.tz or 'UTC')
            
            for trip in trips:
                collected = sum(request.env['account.payment'].sudo().search([('payment_type', '=', 'inbound'), ('activity_user_id', '=', user.id),  
                                                                          ('date', '=', trip.date)]).mapped('amount'))
                sales = request.env['account.move'].sudo().search([('move_type', '=', 'out_invoice'), ('invoice_user_id', '=', user.id),  
                                                               ('invoice_date', '=', trip.date)])
                start_time = trip.trip_start_time.astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S') if trip.trip_start_time else ''
                end_time = trip.trip_end_time.astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S') if trip.trip_end_time else ''

                trip_list.append({
                    'id': trip.id,
                    'date': trip.date.strftime('%Y-%m-%d'),
                    'odometer_start': trip.start_kilometer,
                    'odometer_end': trip.end_kilometer,
                    'collected': collected,
                    'sale_amount': sum(sales.mapped('amount_total')),
                    'start_km_image':f'{base_url}/web/image?model=sales.person.trip&id={trip.id}&field=start_km_image' if trip.start_km_image else '',
                    'end_km_image': f'{base_url}/web/image?model=sales.person.trip&id={trip.id}&field=end_km_image' if trip.end_km_image else '',
                    'start_location_id' : trip.start_location_id.id,
                    'start_location_name' : trip.start_location_id.name,
                    'end_location_id' : trip.end_location_id.id,
                    'end_location_name' : trip.end_location_id.name,
                    'trip_start_time': start_time,
                    'trip_end_time': end_time
                })
            return self._prepare_response(True, 200, "Success", trip_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/product_batch', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_product_batch(self, **kwargs):
        try:
            user = getattr(request, 'validated_token', {})
            salesperson_route = request.env['sales.route.assignment'].sudo().search([('salesperson_id', '=', user.id)])
            van_branch_id = salesperson_route.van_id.company_id.id
            if not van_branch_id:
                return self._prepare_response(False, 404, "", None, "User is not associated with Van")
            warehouse = request.env['stock.warehouse'].sudo().search([('company_id', '=', van_branch_id)])
            if not warehouse:
                return self._prepare_response(False, 404, "", None, "Invalid warehouse")
            location_id = warehouse.lot_stock_id.id
            product_id = kwargs.get('product_id', None)
            if not product_id:
                return self._prepare_response(False, 400, None, None, "Product ID is missing")
            domain = [('product_id', '=', int(product_id))]
            lots = request.env['stock.lot'].sudo().search(domain)
            lot_list = []
            for lot in lots:
                stock_quant = request.env['stock.quant'].sudo().search([('product_id', '=', lot.product_id.id), ('lot_id', '=', lot.id),
                                                                        ('location_id', '=', location_id)])
                lot_list.append({
                    'id': lot.id,
                    'name': lot.name,
                    'expiration_date': lot.expiration_date.strftime('%Y-%m-%d') if lot.expiration_date else '',
                    'quantity': stock_quant.available_quantity if stock_quant else 0,
                    'purchase_price':lot.standard_price + lot.margin
                })
            return self._prepare_response(True, 200, "Success", lot_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/payment_method', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_payment_method(self, **kwargs):
        try:
            user = getattr(request, 'validated_token', {})
            company_ids = [user.company_id.id]
            parent = user.company_id.parent_id
            while parent:
                company_ids.append(parent.id)
                parent = parent.parent_id
            domain = [('type', 'in', ['bank', 'cash']), ('company_id', 'in', company_ids)]
            journals = request.env['account.journal'].sudo().search(domain)
            journal_list = []
            for journal in journals:
                journal_list.append(
                    {'id': journal.id, 'name': journal.name}
                )
            return self._prepare_response(True, 200, "Success", journal_list, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/ageing_report', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_ageing_report(self, **kwargs):
        try:
            user = getattr(request, 'validated_token', {})
            today = date.today()
            domain = [('invoice_user_id', '=', user.id), ('payment_state', 'not in', ['paid']), 
                      ('move_type', '=', 'out_invoice'), ('invoice_date_due', '<', today)]
            partner_id = kwargs.get('partner_id', None)
            if partner_id:
                domain.append(('partner_id', '=', int(partner_id)))
            invoices = request.env['account.move'].sudo().search(domain)
            invoice_list = []
            for invoice in invoices:
                days_old = (today - invoice.invoice_date_due).days if invoice.invoice_date_due else 0
                invoice_list.append({
                    'id': invoice.id,
                    'number': invoice.name,
                    'date_due': invoice.invoice_date_due.strftime('%Y-%m-%d'),
                    'amount_total': invoice.amount_total,
                    'amount_residual': invoice.amount_residual,
                    'partner_id': invoice.partner_id.id,
                    'partner': invoice.partner_id.name,
                    'days_old': days_old
                })
            return self._prepare_response(True, 200, "Success", invoice_list, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/no_order_reason', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_no_order_reason(self, **kwargs):
        try:
            reasons = request.env['order.reason'].sudo().search([])
            reason_list = []
            for reason in reasons:
                reason_list.append({
                    'id': reason.id,
                    'name': reason.name
                })
            return self._prepare_response(True, 200, "Success", reason_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/country', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_res_country(self):
        try:
            model = 'res.country'
            country_list = []
            countries = request.env[model].sudo().search([])
            for country in countries:
                country_list.append({
                    'id': country.id,
                    'name': country.name,
                    'code': country.code,
                })
            # self.update_last_sync_date(model)
            return self._prepare_response(True, 200, "Success", country_list, None)

        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/country_state', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_res_country_state(self):
        try:
            model = 'res.country.state'
            
            state_list = []
            states = request.env[model].sudo().search([])
            for state in states:
                state_list.append({
                    'id': state.id,
                    'name': state.name,
                    'code': state.code,
                    'country_id': state.country_id.id,
                })
            # self.update_last_sync_date(model)
            return self._prepare_response(True, 200, "Success", state_list, None)

        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/uom', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_van_uom(self):
        try:
            model = 'uom.uom'
            uoms = request.env[model].sudo().search_read([], ['name'])
            return self._prepare_response(True, 200, "UoM Fetched successfully", uoms, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e)) 
        
    @validate_token
    @http.route('/van/order_history/<partner_id>', type='http', auth='public', methods=['GET'])
    def get_order_history(self, partner_id, **kwargs):
        try:
            if not partner_id:
                return self._prepare_response(False, 400, None, None, "Partner ID is missing")
            if not isinstance(partner_id, int):
                partner_id = int(partner_id)
            domain = [('partner_id', '=', partner_id)]
            user_id = kwargs.get('salesperson_id', None)
            if user_id:
                domain.append(('user_id', '=', int(user_id)))
            sale_orders = request.env['sale.order'].sudo().search(domain)
            order_list = []
            for sale_order in sale_orders:
                invoices = sale_order.invoice_ids.filtered(lambda x: x.line_ids.sale_line_ids.order_id == sale_order)
                invoices_list = []
                for invoice in invoices:
                    invoices_list.append({
                        'id': invoice.id,
                        'number': invoice.name,
                        'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
                        'state': invoice.state,
                        'amount_total': invoice.amount_total,
                        'partner_id': invoice.partner_id.id,
                        'partner': invoice.partner_id.name,
                        'payment_state': invoice.payment_state,
                        'paid_amount': sum(invoice.matched_payment_ids.sudo().filtered(lambda x: x.state == 'paid').mapped('amount')),
                        'invoice_date_due': invoice.invoice_date_due.strftime('%Y-%m-%d') if invoice.invoice_date_due else '',
                        'amount_residual': invoice.amount_residual
                    })
                order_list.append({
                    'id': sale_order.id,
                    'number': sale_order.name,
                    'date_order': sale_order.date_order.strftime('%Y-%m-%d') if sale_order.date_order else '',
                    'state': sale_order.state,
                    'amount_total': sale_order.amount_total,
                    'invoice_status': sale_order.invoice_status,
                    'partner_id': sale_order.partner_id.id,
                    'partner': sale_order.partner_id.name,
                    'margin': sale_order.margin,
                    'amount_invoiced': sale_order.amount_invoiced,
                    'amount_to_invoice': sale_order.amount_to_invoice,
                    'invoice_details': invoices_list,
                })
            return self._prepare_response(True, 200, "Success", order_list, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @validate_token
    @http.route('/van/customers', type='http', auth='public', methods=['GET'])
    def get_van_customers(self, **kwargs):
        try:
            user = getattr(request, 'validated_token', {})
            domain = [('salesperson_id', '=', int(user.id))]
            routes = request.env['sales.route.assignment'].sudo().search(domain).mapped('route_ids')
            customer_list = []
            customer_id = kwargs.get('id', None)
            customers = routes.shops_ids
            if customer_id:
                customer_id = int(customer_id)
                customers = routes.shops_ids.filtered(lambda c: c.id == customer_id)
            
            for customer in customers:
                sale_order = request.env['sale.order'].sudo().search([('partner_id', '=', customer.id)], order='date_order DESC', limit=1)
                customer_list.append({
                    'id': customer.id,
                    'name': customer.name,
                    'customer_code': customer.customer_code,
                    'cr_number': customer.cr_number,
                    'email': customer.email,
                    'mobile': customer.mobile,
                    'street': customer.street,
                    'city': customer.city,
                    'zip': customer.zip,
                    'route_id': customer.route_id.id,
                    'route': customer.route_id.name,
                    'vat': customer.vat,
                    'purchase_date': sale_order.date_order.strftime('%Y-%m-%d %H:%M:%S') if sale_order else '',
                    'amount': sale_order.amount_total if sale_order else 0
                    
                })
            return self._prepare_response(True, 200, "Success", customer_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @validate_token
    @http.route('/van/product_offer/<product_id>', type='http', auth='public', methods=['GET'])
    def get_product_offer(self, product_id):
        try:
            if not product_id:
                return self._prepare_response(False, 400, None, None, "Product ID is missing")
            if not isinstance(product_id, int):
                product_id = int(product_id)
            today = date.today()
            user = getattr(request, 'validated_token', {})
            company_id = user.company_id.id
            location_ids = request.env['stock.location'].sudo().search([
                ('company_id', '=', company_id),
                ('usage', '=', 'internal')
            ]).ids

            quants = request.env['stock.quant'].sudo().search([ ('location_id', 'in', location_ids),
            ('lot_id', '!=', False),('product_id', '=', product_id)])
            lot_ids = list(set(quants.mapped('lot_id.id')))
            domain = [('product_id', '=', product_id), ('start_date', '<=', today), ('end_date', '>=', today)]
            product_offer = request.env['product.offer'].sudo().search(domain)
            product_obj = request.env['product.product'].sudo().browse(product_id)
            product_uom_ids = product_obj.product_uom_ids.ids
            values = {}
            if product_offer:
                values = {
                    'name': product_offer.name,
                    'product_id': product_offer.product_id.id,
                    'discount_percentage': product_offer.discount_percentage,
                    'start_date': product_offer.start_date.strftime('%Y-%m-%d'),
                    'end_date': product_offer.end_date.strftime('%Y-%m-%d'),
                    'lot_ids':lot_ids,
                    'product_uom_ids': product_uom_ids,
                }
            return self._prepare_response(True, 200, "Success", values, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @validate_token
    @http.route('/van/sale_order_by_day', type='http', auth='public', methods=['GET'])
    def get_sale_order_by_day(self, **kwargs):
        try:
            period_days = kwargs.get('days', 30)
            today = datetime.today()
            start_date = today - timedelta(days=int(period_days))
            user = getattr(request, 'validated_token', {})
            request.env.cr.execute("""
                SELECT 
                    DATE(date_order) AS sale_date, 
                    SUM(amount_total) AS total_sales
                FROM 
                    sale_order
                WHERE 
                    state IN ('sale') 
                    AND date_order >= %s
                    AND user_id = %s
                GROUP BY 
                    DATE(date_order)
                ORDER BY 
                    sale_date
            """, (start_date, user.id))
            
            result = request.env.cr.fetchall()
            values = [{'date': row[0].strftime('%Y-%m-%d'), 'total_sales': row[1]} for row in result]
            return self._prepare_response(True, 200, "Success", values, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @validate_token
    @http.route('/van/sale_summary', type='http', auth='public', methods=['GET'])
    def get_sale_summary(self, **kwargs):
        try:
            today = date.today()
            user = getattr(request, 'validated_token', {})
            collected = sum(request.env['account.payment'].sudo().search([('payment_type', '=', 'inbound'), ('activity_user_id', '=', user.id),  
                                                                          ('date', '=', today)]).mapped('amount'))
            sales = request.env['account.move'].sudo().search([('move_type', '=', 'out_invoice'), ('invoice_user_id', '=', user.id),  
                                                               ('invoice_date', '=', today)])
            sale_list = []
            for sale in sales:
                sale_list.append({
                    'id': sale.id,
                    'number': sale.name,
                    'date': sale.invoice_date.strftime('%Y-%m-%d'),
                    'amount_total': sale.amount_total,
                    'partner_id': sale.partner_id.id,
                    'partner': sale.partner_id.name,
                    'payment_state': sale.payment_state,
                    'paid_amount': sum(sale.matched_payment_ids.sudo().filtered(lambda x: x.state == 'paid').mapped('amount')),
                    'payment_mode': sale.matched_payment_ids.sudo().filtered(lambda x: x.state == 'paid').mapped('journal_id.name'),
                    'invoice_date_due': sale.invoice_date_due.strftime('%Y-%m-%d'),
                    'amount_residual': sale.amount_residual,
                })
            values = {
                'collected': collected,
                'sale_amount': sum(sales.mapped('amount_total')),
                'sales': sale_list
            }
            return self._prepare_response(True, 200, "Success", values, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))

    @validate_token
    @http.route('/credit_approve', type='http', auth='public', methods=['POST'], csrf=False)
    def approve_credit(self):
        try:
            user = getattr(request, 'validated_token', {})
            data = json.loads(request.httprequest.data)
            move_id = data.get('move_id', None)
            if not move_id:
                return self._prepare_response(False, 400, None, None, "Invoice ID is missing")
            invoice = request.env['account.move'].sudo().browse(move_id)
            credit = request.env['credit.approval'].sudo().create({'move_id': invoice.id})
            credit.message_post(body="Credit Approval created from Van Sales")
            payload_data = {
                'id': credit.id,
                'date': credit.create_date.strftime('%Y-%m-%d')
                }
            return self._prepare_response(True, 201, "Credit Approval Created", payload_data, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @validate_token
    @http.route('/van/allocation_request', type='http', auth='public', methods=['POST'], csrf=False)
    def allocate_van_request(self):
        try:
            user = getattr(request, 'validated_token', {})
            data = json.loads(request.httprequest.data)
            
            lines = data.get('order_line', [])
            if not lines:
                return self._prepare_response(False, 400, None, None, "Order Line is Missing")
            user_route = request.env['sales.route.assignment'].sudo().search([('salesperson_id', '=', user.id)], limit=1)
            order_line = []
            for line in lines:
                if not line.get('product_id'):
                    return self._prepare_response(
                        False, 400, "", None, "Product ID is missing"
                    )
                if not line.get('quantity'):
                    return self._prepare_response(
                        False, 400, "", None, "Quantity is missing"
                    )
                product = request.env['product.product'].sudo().browse(line.get('product_id'))
                if not product:
                    return self._prepare_response(False, 400, "", None, "Product ID is not Valid")
                order_line.append({
                    'product_id': product.id,
                    'quantity': line.get('quantity'),
                    'uom_id': line.get('uom_id') if line.get('uom_id') else product.uom_id.id,
                })
            values = {
                'user_id': user.id,
                'van_id': user_route.van_id.id,
                'date': date.today(),
                'order_line': [(0, 0, line) for line in order_line]
            }
            allocation_request = request.env['van.allocation.request'].sudo().create(values)
            payload_data = {
                'id': allocation_request.id,
                'date': allocation_request.date.strftime('%Y-%m-%d')
                }
            return self._prepare_response(True, 201, "Van Allocation Request Created", payload_data, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))

    @validate_token   
    @http.route('/van/product_offers', type='http', auth='public', methods=['GET'])
    def get_product_offers(self):
        try:
            today = date.today()
            domain = [('start_date', '<=', today), ('end_date', '>=', today)]
            product_offers = request.env['product.offer'].sudo().search(domain)
            user = getattr(request, 'validated_token', {})
            company_id = user.company_id.id
            location_ids = request.env['stock.location'].sudo().search([
                ('company_id', '=', company_id),
                ('usage', '=', 'internal')
            ]).ids

            offer_list = []
            for product_offer in product_offers:
                quants = request.env['stock.quant'].sudo().search([ ('location_id', 'in', location_ids),
                         ('lot_id', '!=', False),('product_id', '=', product_offer.product_id.id)])
                lot_ids = list(set(quants.mapped('lot_id.id')))
                offer_list.append(
                    {
                        'name': product_offer.name,
                        'product_id': product_offer.product_id.id,
                        'product_name': product_offer.product_id.display_name,
                        'discount_percentage': product_offer.discount_percentage,
                        'start_date': product_offer.start_date.strftime('%Y-%m-%d'),
                        'end_date': product_offer.end_date.strftime('%Y-%m-%d'),
                        'lot_ids':lot_ids,
                        'product_uom_ids' : product_offer.product_id.product_uom_ids.ids,
                    }
                )
            return self._prepare_response(True, 200, "Success", offer_list, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/quotations', type='http', auth='public', methods=['GET'])
    @validate_token
    def get_quotations(self, **kwargs):
        try:
            domain = []
            user = getattr(request, 'validated_token', {})
            product_id = kwargs.get('product_id', None)
            partner_id = kwargs.get('customer_id', None)
            today = date.today()
            date_str = kwargs.get('date', None)
            if date_str:
                today = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            domain += [('date_order', '>=', start_of_day), ('date_order', '<=', end_of_day)]
            user_id = kwargs.get('salesperson_id', user.id)
            id = kwargs.get('id', None)
            if user_id:
                domain += [('user_id', '=', int(user_id))]
            if product_id:
                domain += [('order_line.product_id', '=', int(product_id))]
            if partner_id:
                domain += [('partner_id', '=', int(partner_id))]
            if id:
                domain += [('id', '=', int(id))]

            sale_orders = request.env['sale.order'].sudo().search(domain, order='id DESC')
            sale_history = []
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            for sale_order in sale_orders:
                sale_values = {
                    'order_id': sale_order.id,
                    'order': sale_order.name,
                    'order_date': sale_order.date_order.strftime('%Y-%m-%d %H:%M:%S'),
                    'customer_id': sale_order.partner_id.id,
                    'customer': sale_order.partner_id.name,
                    'amount_untaxed': sale_order.amount_untaxed,
                    'amount_tax': sale_order.amount_tax,
                    'amount_total': sale_order.amount_total,
                    'amount_invoiced': sale_order.amount_invoiced,
                    'margin': sale_order.margin,
                    'order_lines': [],
                    }
                order_lines = sale_order.order_line
                if kwargs.get('product_id'):
                    order_lines.filtered(lambda x: x.product_id.id == int(product_id))
                for line in order_lines:
                    sale_values['order_lines'].append({
                        'id': line.id,
                        'product': line.product_id.id,
                        'product_code': line.product_id.default_code,
                        'product_name': line.product_id.display_name,
                        'quantity': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'purchase_price': line.purchase_price,
                        'margin': line.margin,
                        'sub_total': line.price_subtotal,
                        'price_tax': line.price_tax,
                        'discount':line.discount,
                        'discount_amount':line.discount_amount,
                        'price_total': line.price_total,
                        'lot_id': line.lot_id.id,
                        'lot_name': line.lot_id.name,
                        'image_url': f'{base_url}/web/image?model=product.product&id={line.product_id.id}&field=image_1920' if line.product_id.image_1920 else '',
                        'uom_id': line.product_uom.id,
                        'uom_name': line.product_uom.name,
                        'expiry': line.lot_id.expiration_date.strftime('%Y-%m-%d') if line.lot_id.expiration_date else '',
                        })
                sale_history.append(sale_values)    
            return self._prepare_response(True, 200, "Quotations fetched Successfully", sale_history, None)
        
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))
        
    @http.route('/van/expense/<id>', type='http', auth='public', methods=['PATCH'], csrf=False)
    @validate_token
    def update_van_sale_expense(self, id):
        try:
            data = json.loads(request.httprequest.data)
            if not data:
                return self._prepare_response(False, 400, None, None, "Request Data is missing")
            if not id:
                return self._prepare_response(False, 400, None, None, "Expense ID is missing")
            if not isinstance(id, int):
                id = int(id)
            expense = request.env['hr.expense'].sudo().browse(id)
            if not expense:
                return self._prepare_response(False, 404, None, None, "Expense Not Found")
            if expense.state in ['approved', 'done']:
                return self._prepare_response(False, 400, None, None, "Expense is already approved")
            product_id = data.get('category_id', None)
            update_values = {}
            if product_id:
                product = request.env['product.product'].sudo().search([('id', '=', product_id), ('can_be_expensed', '=', True)])
                if not product:
                    return self._prepare_response(False, 400, None, None, "Category ID is not valid")
                update_values['product_id'] = product_id
            name = data.get('description', None)
            if name:
                update_values['name'] = name
            amount = data.get('amount', None)
            if amount:
                update_values['total_amount_currency'] = amount
            expense.sudo().write(update_values)
            for attachment in data.get('attachment_ids', []):
                if attachment.get('id'):
                    attachment_id = attachment.get('id')
                    attachment = request.env['ir.attachment'].sudo().browse(attachment_id)
                    attachment.unlink()
                else:
                    decoded_attachment = base64.b64decode(attachment.get('data'))
                    file_name = attachment.get('file_name')
                    file_type = magic.from_buffer(decoded_attachment, mime=True)
                    encoded_data = base64.b64encode(decoded_attachment).decode('utf-8')
                    request.env['ir.attachment'].sudo().create({
                        'name': file_name,
                        'type': 'binary',
                        'datas': encoded_data,
                        'res_model': 'hr.expense',
                        'res_id': expense.id, 
                        'mimetype': file_type
                    })
            return self._prepare_response(True, 200, "Expense Updated", None, None)
        except AccessError:
            return self._prepare_response(False, 403, None, None, "Access denied")
        except Exception as e:
            return self._prepare_response(False, 500, None, None, str(e))

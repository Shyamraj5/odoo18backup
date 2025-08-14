from datetime import date, datetime, timedelta, time
import json
import base64
import logging
import random
import string
import requests
import calendar
from TaqnyatSms import client
import re
from odoo import http, exceptions, _, fields
from odoo.http import request
from odoo.addons.odoo_auth2.controllers.auth2_authentication import validate_token
from pytz import timezone

_logger = logging.getLogger(__name__)

class DietMobileApi(http.Controller):

    def make_response(self, statusOk, statusCode, message, payload, error):
        return request.make_response(json.dumps({
            "statusOk": statusOk,
            "statusCode": statusCode,
            "message": message,
            "payload": payload,
            "error": error
        }), headers=[('Content-Type', 'application/json')])

    def create_profile(self, data):
        _logger.info(f"CREATE PROFILE DATA PASSED >>>>>> {data}")
        if not data:
            return self.make_response(False, 400, [], None, [
                "No data given.", # english error message
                "No data given." # arabic error message
            ])
        for field in ['mobile', 'password']:
            if field not in data:
                return self.make_response(False, 400, [], None, [
                    f"{field.capitalize()} not given.", # english error message
                    f"{field.capitalize()} not given." # arabic error message
                ])
        mobile = data['mobile']
        password = data['password']
        customer_id = request.env['res.partner'].sudo().search([
            ('phone', '=', mobile)
        ])
        if customer_id:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} exists.", # english error message
                f"هذا الرقم مسجل من قبل." # arabic error message
            ])
        mandatory_fields = ['nickname', 'street_id', 'house_number']
        mandatory_fields_not_given = [field.capitalize() for field in mandatory_fields if data.get(field) and not data[field]]
        if mandatory_fields_not_given:
            return self.make_response(False, 400, [], None, [
                f"{','.join(mandatory_fields_not_given)} not given.", # english error message
                f"{','.join(mandatory_fields_not_given)} not given." # arabic error message
            ])
        goals_id = False
        if 'customer_goals_id' in data:
            goals_id = request.env['customer.goals'].sudo().search([('id', '=', data['customer_goals_id'])], limit=1)
            if not goals_id:
                return self.make_response(False, 400, [], None, [
                    f"Goal with ID {data['customer_goals_id']} doesn't exist.",
                    f"Goal with ID {data['customer_goals_id']} doesn't exist."
                ])
        refferal_code_condition = True
        while refferal_code_condition:
            code_length = 8
            characters = string.digits + string.ascii_letters + string.digits
            code = ''.join(random.choice(characters) for i in range(code_length))
            partner_exists = request.env["res.partner"].search([("referral_code", "=", code)])
            if not partner_exists:
                refferal_code = code
                refferal_code_condition = False
        district_id = request.env['customer.district'].sudo().search([('id', '=', data.get('district_id', False))], limit=1)
        if district_id:
            city_id = district_id.city_id.id
        else:
            city_id = False
        
        try:
            customer_id = request.env['res.partner'].sudo().create({
                'referral_code': refferal_code,
                'company_type': 'person',
                'type': 'contact',
                'phone': mobile,
                'diet_app_password': password,
                'is_customer': True,
                'customer_sequence_no': request.env['ir.sequence'].next_by_code('customer.code') or _('New'),
                'name': data.get('first_name', False) or mobile,
                'last_name': data.get('last_name', False),
                'arabic_name': data.get('first_name_arabic', False),
                'last_name_arabic': data.get('last_name_arabic', False),
                'gender': data.get('gender', False),
                'date_of_birth': datetime.strptime(data.get('date_of_birth', '1900-1-1'), '%Y-%m-%d').date() if data.get('date_of_birth', False) else date(1900,1,1),
                'email': data.get('email', False),
                'height': data.get('height', False),
                'weight': data.get('weight', False),
                'source': data.get('source', False),
                'customer_goals_id': goals_id.id if goals_id else False,
                'other_source': data.get('other_source', False),
                'image_1920': data.get('profile_picture', False),
                'is_pregnent': data.get('is_pregnent', False),
                'child_ids': [(0,0, {
                    'name': data.get('nickname', False),
                    'district_id': data.get('district_id', False),
                    'state_id': city_id,
                    'street_id': data.get('street_id', False),
                    'house_number': data.get('house_number', False),
                    'floor_number': data.get('floor_number', False),
                    'apartment_no': data.get('apartment_no', False),
                    'zip': data.get('zip', False),
                    'jedha': data.get('jedha', False),
                    'comments': data.get('comments', False),
                    'partner_latitude': float(data.get('partner_latitude', 0.0)),
                    'partner_longitude': float(data.get('partner_longitude', 0.0)),
                })] if data.get('nickname', False) else [],
                'inviter_referral_code': data.get('invitation_code', False)
            })
            if customer_id:
                customer_id.customer_address_id = customer_id.child_ids[0] if customer_id.child_ids else False
                customer_id.message_post(body=f"Customer created from customer app.")
                return self.make_response(True, 200, [
                    "Profile created successfully.", # english success message
                    "تم إنشاء الملف الشخصي بنجاح." # arabic success message
                ], None, [])
                print(city_id)
            else:
                return self.make_response(False, 400, [], None, [
                    "Profile creation failed.", # english error message
                    "فشل في عملية إنشاء الملف الشخصي." # arabic error message
                ])
        except Exception as e:
            return self.make_response(False, 400, [], None, [
                "Profile creation failed.", # english error message
                "فشل في عملية إنشاء الملف الشخصي." # arabic error message
            ])
        
    def get_profile(self, data):
        if not data or 'mobile' not in data:
            return self.make_response(False, 400, [], None, [
                "No data given or Mobile number not given. Can't identify customer.", # english error message
                "لم يتم تقديم بيانات كافية لتحديد العميل." #arabic error message
            ])
        mobile = data['mobile']
        customer = request.env['res.partner'].sudo().search([('phone', '=', mobile)], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} doesn't exist.", # english error message
                f"لا يوجد عميل مرتبط بهذا الرقم." # arabic error message
            ])
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        customer_subscription = customer.customer_sale_order_line_ids.filtered(lambda subs: subs.state=='in_progress')
        subscription_end_date = customer_subscription[0].end_date.strftime('%d-%m-%Y') if customer_subscription and customer_subscription[0].end_date else 'No active subscription.'
        subscription_end_in = sum(customer_subscription.mapped('sub_end_in')) if customer_subscription else 'No active subscription.'
        subscription_name = customer_subscription[0].plan_id.name if customer_subscription else 'No active subscription.'
        subscription_arabic_name = customer_subscription[0].plan_id.arabic_name if customer_subscription else 'No active subscription.'
        delivery_time = ""
        if (
            customer_subscription
            and customer_subscription[0].meal_calendar_ids
            and customer_subscription[0].meal_calendar_ids.filtered(lambda cal: cal.date == fields.Date.today())
            and customer_subscription[0].meal_calendar_ids.filtered(lambda cal: cal.date == fields.Date.today())[0].shift_id
        ):
            shift = f"{customer_subscription[0].meal_calendar_ids.filtered(lambda cal: cal.date == fields.Date.today())[0].shift_id.shift} delivery"
            delivery_time = customer_subscription[0].meal_calendar_ids.filtered(lambda cal: cal.date == fields.Date.today())[0].address_id.delivery_time
        elif (
            customer_subscription
            and customer_subscription[0].meal_calendar_ids
            and customer_subscription[0].meal_calendar_ids[0].shift_id
        ):
            shift =f"{customer_subscription[0].meal_calendar_ids[0].shift_id.shift} delivery"
            delivery_time = customer_subscription[0].meal_calendar_ids[0].address_id.delivery_time
        else:
            shift = "Evening shift"
            delivery_time = customer.customer_address_delivery_time
        if not delivery_time:
            delivery_time = customer.customer_address_district_id.delivery_time
        customer_tags = ', '.join(customer.category_id.mapped('name'))
        cvals = {
            "id": customer.id,
            "customer_code": customer.customer_sequence_no or '',
            "first_name": customer.name or '',
            "last_name": customer.last_name or '',
            "first_name_arabic": customer.arabic_name or '',
            "last_name_arabic": customer.last_name_arabic or '',
            "tags": customer_tags or '',
            "gender": customer.gender or '',
            "height": customer.height or 0.0,
            "weight": customer.weight or 0.0,
            "date_of_birth": customer.date_of_birth.strftime('%Y-%m-%d') if customer.date_of_birth else '1900-1-1',
            "mobile": customer.phone or '',
            "email": customer.email or '',
            "profile_picture": f'{base_url}/web/image/ir.attachment/{customer.profile_picture_attachment_id.id}/datas' if customer.profile_picture_attachment_id else '',
            "subscription_end_date": subscription_end_date,
            "subscription_end_in": subscription_end_in,
            "subscription_name": subscription_name,
            "subscription_arabic_name": subscription_arabic_name,
            "shift": shift,
            "delivery_time": delivery_time if delivery_time else "",
            "is_pregnent": customer.is_pregnent,
            "customer_goal":customer.customer_goals_id.name,
            "latitude": float(customer.partner_latitude),
            "longitude": float(customer.partner_longitude)

        }
        _logger.info(f"{json.dumps(cvals)}")
        return self.make_response(True, 200, [], [cvals], [])

    def update_profile(self, data):
        if not data:
            return self.make_response(False, 400, [], None, [
                "No data received for updating profile.", # english error message
                "لم تصل أي بيانات لتحديث الملف الشخصي." # arabic error message
            ])
        try:
            mobile = data['mobile']
            customer = request.env['res.partner'].sudo().search([('phone', '=', mobile)], limit=1)
            if not customer:
                return self.make_response(False, 400, [], None, [
                    f"Customer with mobile {mobile} doesn't exist.", # english error message
                    f"لا يوجد عميل مرتبط بهذا الرقم." # arabic error message
                ])
            fields_to_update = {
                'profile_picture': 'image_1920',
                'gender': 'gender',
                'height': 'height',
                'weight': 'weight',
                'first_name': 'name',
                'last_name': 'last_name',
                'first_name_arabic': 'arabic_name',
                'last_name_arabic': 'last_name_arabic',
                'date_of_birth': 'date_of_birth',
                'mobile': 'phone',
                'email': 'email',
            }
            update_vals = {odoo_field: data.get(field) for field, odoo_field in fields_to_update.items() if field in data and data[field] != 'False'}
            if 'date_of_birth' in update_vals:
                birthday_list = update_vals['date_of_birth'].split('-')
                update_vals['date_of_birth'] = date(year=int(birthday_list[0]), month=int(birthday_list[1]), day=int(birthday_list[2]))
            params_updated = [field.capitalize() for field in data if field in fields_to_update and data[field] != 'False']
            customer.write(update_vals)
            customer.message_post(body=f"Customer profile updated from customer app.")
            return self.make_response(True, 200, [
                f"Updated {(', '.join(params_updated))}", # english error message
                f"تم تعديل بيانات العميل بنجاح عبر التطبيق. {(', '.join(params_updated))}" # arabic error messages
            ], None, [])
        except KeyError:
            return self.make_response(False, 400, [], None, [
                'Mobile number not given. Can\'t identify customer.', # english error message
                'لم يتم إدخال رقم الجوال، يرجى المحاولة مجددًا.' # arabic error message
            ])

    def delete_profile(self, data):
        if not data or 'mobile' not in data:
            return self.make_response(False, 400, [], None, [
                "No data given or Mobile number not given. Can't identify customer.", # english error message
                "لم يتم تقديم بيانات كافية لتحديد العميل." # arabic error message
            ])
        mobile = data['mobile']
        customer = request.env['res.partner'].sudo().search([('phone', '=', mobile)], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} doesn't exist.", # english error message
                f"لا يوجد عميل مرتبط بهذا الرقم." # arabic error message
            ])
        del_request_id = request.env['customer.account.deletion.request'].sudo().create({'customer_id': customer.id})
        if del_request_id:
            return self.make_response(True, 200, [
                "Customer profile deletion request created successfully.", # english success message
                "تم إرسال طلب حذف بيانات العميل بنجاح." # arabic success message
            ], None, [])
        else:
            return self.make_response(True, 400, [], None, [
                "Deletion request failed.", # english error message
                "فشل في إرسال طلب الحذف." # arabic error message
            ])
    
    @validate_token
    @http.route('/profile', type="http", auth="none", methods=['GET','POST','PATCH','DELETE'], csrf=False)
    def profile(self, **data_passed):
        _logger.info(f"PROFILE DATA PASSED >>>>>> {data_passed}")
        method_to_function = {
            'POST': self.create_profile,
            'GET': self.get_profile,
            'PATCH': self.update_profile,
            'DELETE': self.delete_profile
        }
        function_to_execute = method_to_function.get(request.httprequest.method)
        if request.httprequest.method in ['POST', 'PATCH']:
            data_passed = request.get_json_data()
        if function_to_execute:
            return function_to_execute(data_passed)
        else:
            return self.make_response(False, 400, [], None, [
                "Invalid Method.", # english error message
                "Invalid Method." # arabic error message
            ])

    @validate_token
    @http.route('/profile/exist/<mobile>', type='http', auth='none', methods=['GET'], csrf=False)
    def profile_exist(self, mobile):
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.", # english error message
                "رقم الهاتف المحمول غير مذكور" # arabic error message
            ])
        customer = request.env['res.partner'].search([
            ('phone', '=', mobile)
        ])
        if customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} exists.", # english error message
                f"هذا الرقم مسجل من قبل." # arabic error message
            ])
        else:
            return self.make_response(False, 200, [], None, [])

    @validate_token
    @http.route('/login', type='http', auth="none", methods=['GET'], csrf=False)
    def login(self, **data_passed):
        if not data_passed or not data_passed.get('mobile') or not data_passed.get('password'):
            error_message = "No data given."
            arabic_message = "No data given."
            if not data_passed.get('mobile'):
                error_message = "Mobile not given."
                arabic_message = "يرجى إدخال رقم الجوال."
                if not data_passed.get('password'):
                    error_message = "Mobile and password not given."
                    arabic_message = "يجب تقديم رقم الجوال وكلمة المرور."
            elif not data_passed.get('password'):
                error_message = "Password not given."
                arabic_message = "يرجى إدخال كلمة المرور."
            return self.make_response(False, 400, [], None, [
                error_message, # english error message
                error_message # arabic error message
            ])

        mobile = data_passed['mobile']
        password = data_passed['password']

        if mobile[0:4] == '+966' or mobile[0:4] == ' 965':
            mobile = mobile[4:]
        
        customer_id = request.env['res.partner'].sudo().search(['|', ('phone', '=', mobile), ('phone', '=', f"+966{mobile}"), ('active', '=', True)])
        if not customer_id:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} doesn't exist.", # english error message
                f"لا يوجد عميل مرتبط بهذا الرقم." # arabic error message
            ])
        
        if customer_id.diet_app_password == password:
            return self.make_response(True, 200, [], None, [])
        else:
            return self.make_response(False, 400, [], None, [
                "Invalid credentials.", # english error message
                "بيانات الدخول غير صحيحة." # arabic error message
            ])
    
    @validate_token
    @http.route('/districts', type='http', auth="public", methods=['GET'], csrf=False)
    def get_districts(self, **data_passed):
        try:
            available_district = request.env['customer.district'].sudo().search([('active','=',True)], order='name')
            district_data = [{
                "id": district.id,
                "name": district.name if district.name else '',
                "arabic_name": district.arabic_name if district.arabic_name else ''
            } for district in available_district]
            if district_data:
                return self.make_response(True, 200, [], district_data, [])
            else:
                return self.make_response(False, 400, [
                    "Success.",
                    "Success."
                ], None, [
                    "No states found.",
                    "No states found."
                ])
        except Exception as e:
            return self.make_response(False, 500, [], None, [
                "An error occurred while fetching states.",
                "An error occurred while fetching states."
            ])

    @validate_token
    @http.route('/districts/search/<keyword>', type='http', auth='public', methods=['GET'], csrf=False)
    def search_district(self, keyword):
        districts = request.env['customer.district'].sudo().search([
            ('name','ilike',keyword)
        ])
        district_result = [{
            'id': district.id,
            'name': district.name or "",
            'arabic_name': district.arabic_name or ""
        } for district in districts]
        return self.make_response(True, 200, [], district_result, [])

    @validate_token 
    @http.route('/districts/<city_id>', type='http', auth="public", methods=['GET'], csrf=False)
    def get_districts_by_city(self, city_id, **data_passed):
        try:
            if not city_id:
                return self.make_response(True, 400, [], None, [
                    "City ID not passed.",
                    "City ID not passed."
                ])
            if not isinstance(city_id, int):
                city_id = int(city_id)
            city = request.env['res.country.state'].sudo().search([('id','=',city_id), ('active','=',True)])
            if not city:
                return self.make_response(True, 400, [], None, [
                    "Invalid city ID passed.",
                    "Invalid city ID passed."
                ])
            available_district = request.env['customer.district'].sudo().search([('active','=',True),('city_id','=',city_id)], order='name')
            district_data = [{
                "id": district.id,
                "name": district.name if district.name else '',
                "arabic_name": district.arabic_name if district.arabic_name else ''
            } for district in available_district]
            if district_data:
                return self.make_response(True, 200, [], district_data, [])
            else:
                return self.make_response(False, 400, [
                    "Success.",
                    "Success."
                ], None, [
                    "No states found.",
                    "No states found."
                ])
        except Exception as e:
            return self.make_response(False, 500, [], None, [
                "An error occurred while fetching states.",
                "An error occurred while fetching states."
            ])
        
    @validate_token
    @http.route('/street', type='http', auth="public", methods=['GET'], csrf=False)
    def get_street(self, **data_passed):
        try:
            available_streets = request.env['customer.street'].sudo().search([('active','=',True)], order='name')
            street_data = [{
                "id": street.id,
                "name": street.name if street.name else '',
                "arabic_name": street.arabic_name if street.arabic_name else ''
            } for street in available_streets]
            if street_data:
                return self.make_response(True, 200, [], street_data, [])
            else:
                return self.make_response(False, 400, [], None, [
                    "No streets found.",
                    "No streets found."
                ])
        except Exception as e:
            return self.make_response(False, 500, [], None, [
                "An error occurred while fetching streets.",
                "An error occurred while fetching streets."
            ])
        
    @validate_token
    @http.route('/street/search/<keyword>', type='http', auth='public', methods=['GET'], csrf=False)
    def search_street(self, keyword):
        streets = request.env['customer.street'].sudo().search([
            ('name','ilike',keyword)
        ])
        street_result = [{
            'id': street.id,
            'name': street.name or "",
            'arabic_name': street.arabic_name or ""
        } for street in streets]
        return self.make_response(True, 200, [], street_result, [])
    
    @validate_token
    @http.route('/street/<district_id>', type='http', auth="public", methods=['GET'], csrf=False)
    def get_street_by_district(self, district_id, **data_passed):
        try:
            if not district_id:
                return self.make_response(True, 400, [], None, [
                    "District ID not passed.",
                    "District ID not passed."
                ])
            if not isinstance(district_id, int):
                district_id = int(district_id)
            district = request.env['customer.district'].sudo().search([('id','=',district_id), ('active','=',True)])
            if not district:
                return self.make_response(True, 400, [], None, [
                    "Invalid district ID passed.",
                    "Invalid district ID passed."
                ])
            available_streets = request.env['customer.street'].sudo().search([('active','=',True),('district_id','=',district_id)], order='sequence')
            street_data = [{
                "id": street.id,
                "name": street.name if street.name else '',
                "arabic_name": street.arabic_name if street.arabic_name else ''
            } for street in available_streets]
            if street_data:
                return self.make_response(True, 200, [], street_data, [])
            else:
                return self.make_response(False, 400, [], None, [
                    "No streets found.",
                    "No streets found."
                ])
        except Exception as e:
            return self.make_response(False, 500, [], None, [
                "An error occurred while fetching streets.",
                "An error occurred while fetching streets."
            ])
    
    @validate_token
    @http.route('/cities', type='http', auth="public", methods=['GET'], csrf=False)
    def get_cities(self, **data_passed):
        try:
            available_cities = request.env['res.country.state'].sudo().search([('active','=',True)], order='name')
            city_data = [{
                "id": city.id,
                "name": city.name if city.name else '',
                "arabic_name": city.arabic_name if city.arabic_name else ''
            } for city in available_cities]
            if city_data:
                return self.make_response(True, 200, [
                    "Success",
                    "Success"
                ], city_data, [])
            else:
                return self.make_response(False, 400, [], None, [
                    "No cities found.",
                    "No cities found."
                ])
        except Exception as e:
            return self.make_response(False, 500, [], None, [
                "An error occurred while fetching cities.",
                "An error occurred while fetching cities."
            ])

    
    @validate_token
    @http.route('/delivery_time', type='http', auth="public", methods=['GET'], csrf=False)
    def delivery_time(self, **data_passed):
        available_delivery_times = request.env['customer.shift'].sudo().search([])
        delivery_time_data = [{
            "id": delivery_time.id,
            "name": delivery_time.shift if delivery_time.shift else '',
            "arabic_name": delivery_time.arabic_name if delivery_time.arabic_name else ''
        } for delivery_time in available_delivery_times]
        if available_delivery_times:
            return self.make_response(True, 200, [], delivery_time_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No delivery times found.", # english error message
                "لا توجد أوقات توصيل متاحة حاليًا." # arabic error message
            ])
    @validate_token
    @http.route('/allergy', type='http', auth="public", methods=['PATCH'], csrf=False)
    def update_allergy(self, **data_passed):
        data_passed = request.get_json_data()
        if 'mobile' not in data_passed or not data_passed['mobile']:
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.", # english error message
                "يرجى إدخال رقم الجوال." # arabic error message
            ])
        
        customer_id = request.env['res.partner'].sudo().search([('phone','=',data_passed['mobile'])],limit=1)
        if not customer_id:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile number {data_passed['mobile']} does not exist.", # english error message
                f"لا يوجد عميل مرتبط بهذا الرقم. {data_passed['mobile']}" # arabic error message
            ])
        
        customer_id.allergy_category_ids = False
        customer_id.allergies = False
        
        all_allergy_categories = request.env['meal.ingredient.category'].search([]).mapped('id')
        allergy_dict = {allergy_cat: request.env['product.template'].search([
            ('is_ingredient','=',True),
            ('ingredient_category_id','=',allergy_cat)
        ]).mapped('id') for allergy_cat in all_allergy_categories}
        
        update_data = {}
        if 'allergies' in data_passed and data_passed['allergies']:
            update_data['allergies'] = [(4, allergy) for allergy in data_passed['allergies']]
            update_data['allergy_category_ids'] = [allergy_cat for allergy_cat in all_allergy_categories\
                 if data_passed['allergies'] and allergy_dict[allergy_cat] and set(allergy_dict[allergy_cat]) <= set(data_passed['allergies'])]
        
        if update_data:
            allergies_to_update = request.env['product.template'].sudo().search([('id', 'in', data_passed['allergies'])])
            allergies_string = ', '.join(allergies_to_update.mapped('name'))
            customer_id.write(update_data)
            customer_id.message_post(body=f"Customer allergies updated from customer app.\n({allergies_string})")
            return self.make_response(True, 200, [], None, [])
        else:
            return self.make_response(False, 200, [], None, [])

    @validate_token
    @http.route('/allergy', type='http', auth="public", methods=['GET'], csrf=False)
    def get_allergy(self, **data_passed):
        if not data_passed or not data_passed.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.", # english error message
                "يرجى إدخال رقم الجوال." # arabic error message
            ])
        
        customer = request.env['res.partner'].sudo().search([('phone', '=', data_passed['mobile'])], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {data_passed['mobile']} doesn't exist.", # english error message
                f"لا يوجد عميل مرتبط بهذا الرقم. {data_passed['mobile']}" # arabic error message
            ])
        
        if not customer.allergies:
            return self.make_response(False, 400, [], None, [
                f"No allergies found for customer {customer.name}.", # english error message
                f"لم يتم العثور على بيانات حساسية للعميل. {customer.name}." # arabic error message
            ])
        
        customer_allergies = [{
            "id": allergy.id,
            "name": allergy.name or '',
            "arabic_name": allergy.arabic_name or ''
        } for allergy in customer.allergies]
        
        return self.make_response(True, 200, [], customer_allergies, [])


    @validate_token
    @http.route('/dislike', type='http', auth="public", methods=['GET'], csrf=False)
    def get_dislikes(self, **data_passed):
        if not data_passed or not data_passed.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.", # english error message
                "يرجى إدخال رقم الجوال.", # arabic error message
            ])
        
        customer = request.env['res.partner'].sudo().search([('phone', '=', data_passed['mobile'])], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {data_passed['mobile']} doesn't exist.", # english error message
                f"لا يوجد عميل مرتبط بهذا الرقم. {data_passed['mobile']}" # arabic error message
            ])
        
        if not customer.dislikes_ids:
            return self.make_response(False, 400, [], None, [
                f"No dislikes found for customer {customer.name}.",
                f"لا توجد مفضلات مسجلة لهذا العميل. {customer.name}."
            ])
        customer_dislikes = [{
            "id": dislike.id,
            "name": dislike.name or '',
            "arabic_name": dislike.arabic_name or ''
        } for dislike in customer.dislikes_ids]
        
        return self.make_response(True, 200, [], customer_dislikes, [])
    

    @validate_token
    @http.route('/dislike', type='http', auth="public", methods=['PATCH'], csrf=False)
    def update_dislike(self, **data_passed):
        data_passed = request.get_json_data()
        if 'mobile' not in data_passed or not data_passed['mobile']:
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.",
                "يرجى إدخال رقم الجوال."
            ])
        customer_id = request.env['res.partner'].sudo().search([('phone','=',data_passed['mobile'])],limit=1)
        if not customer_id:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile number {data_passed['mobile']} does not exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم. {data_passed['mobile']}"
            ])
        
        customer_id.dislike_category_ids = False
        customer_id.dislikes_ids = False
        
        all_dislike_categories = request.env['meal.ingredient.category'].search([]).mapped('id')
        dislike_dict = {dislike_cat: request.env['product.template'].search([
            ('is_ingredient','=',True),
            ('ingredient_category_id','=',dislike_cat)
        ]).mapped('id') for dislike_cat in all_dislike_categories}
        
        update_data = {}
        if 'dislikes' in data_passed and data_passed['dislikes']:
            update_data['dislikes_ids'] = [(4, dislike) for dislike in data_passed['dislikes']]
            update_data['dislike_category_ids'] = [dislike_cat for dislike_cat in all_dislike_categories\
                 if data_passed['dislikes'] and dislike_dict[dislike_cat] and set(dislike_dict[dislike_cat]) <= set(data_passed['dislikes'])]
        
        if update_data:
            dislikes_to_update = request.env['product.template'].sudo().search([('id', 'in', data_passed['dislikes'])])
            dislikes_string = ', '.join(dislikes_to_update.mapped('name'))
            customer_id.write(update_data)
            customer_id.message_post(body=f"Customer dislikes updated from customer app.\n ({dislikes_string})")
            return self.make_response(True, 200, [], None, [])
        else:
            return self.make_response(False, 200, [], None, [])
        
    @validate_token
    @http.route('/dislike_allergy', type='http', auth="public", methods=['PATCH'], csrf=False)
    def update_dislike_allergy(self, **data_passed):
        data_passed = request.get_json_data()
        if 'mobile' not in data_passed or not data_passed['mobile']:
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.",
                "يرجى إدخال رقم الجوال."
            ])
        customer_id = request.env['res.partner'].sudo().search([('phone','=',data_passed['mobile'])],limit=1)
        if not customer_id:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile number {data_passed['mobile']} does not exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم. {data_passed['mobile']}"
            ])
        update_data = {}
        if 'dislikes' in data_passed and data_passed['dislikes']:
            customer_id.dislikes_ids = False
            update_data['dislikes_ids'] = [(4, dislike) for dislike in data_passed['dislikes']]
            dislikes_to_update = request.env['product.template'].sudo().search([('id', 'in', data_passed['dislikes'])])
            dislikes_string = ', '.join(dislikes_to_update.mapped('name'))
            customer_id.message_post(body=f"Customer dislikes updated from customer app.\n ({dislikes_string})")

        if 'allergies' in data_passed and data_passed['allergies']:
            customer_id.allergies = False
            update_data['allergies'] = [(4, allergy) for allergy in data_passed['allergies']]
            allergies_to_update = request.env['product.template'].sudo().search([('id', 'in', data_passed['allergies'])])
            allergies_string = ', '.join(allergies_to_update.mapped('name'))
            customer_id.message_post(body=f"Customer allergies updated from customer app.\n ({allergies_string})")

        if 'is_vegetarian' in data_passed and data_passed['is_vegetarian']:
            update_data['is_vegetarian'] = data_passed['is_vegetarian']
            customer_id.message_post(body=f"Customer's vegetarian status updated")

        if 'comment' in data_passed and data_passed['comment']:
            update_data['comment'] = data_passed['comment']
            customer_id.message_post(body=f"Customer comment updated: {data_passed['comment']}")

        if update_data:
            customer_id.write(update_data)
            return self.make_response(True, 200, [], None, [])
        else:
            return self.make_response(False, 200, [], None, [])
   
    @validate_token
    @http.route('/address', type='http', auth='public', methods=['GET'], csrf=False)
    def get_address(self, **kwargs):
        if not kwargs or not kwargs.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].sudo().search([('phone', '=', kwargs['mobile'])], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {kwargs['mobile']} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم. {kwargs['mobile']}"
            ])
        if not customer.child_ids:
            return self.make_response(False, 400, [], None, [
                f"No address found for customer {customer.name}.",
                f"لم يتم العثور على عنوان مسجل للعميل. {customer.name}."
            ])
        customer_addresses = [{
            "id": address.id,
            "name": address.name or '',
            "arabic_nickname": address.arabic_nickname or '',
            "street_id": address.street_id.id or 0,
            "street_name": address.street_id.name or '',
            "street_name_arabic": address.street_id.arabic_name or '',
            "district_id": address.district_id.id or 0,
            "district_name": address.district_id.name or '',
            "district_name_arabic": address.district_id.arabic_name or '',
            "state_id": address.state_id.id or 0,
            "state_name": address.state_id.name or '',
            "state_name_arabic": address.state_id.arabic_name or '',
            "house_number": address.house_number or '',
            "zip": address.zip or '',
            "floor_number": address.floor_number or '',
            "apartment_no": address.apartment_no or '',
            "comments": address.comments or '',
            "is_default_address": address.is_default_address or False,
        } for address in customer.child_ids]
        
        return self.make_response(True, 200, [], customer_addresses, [])
    
    @validate_token
    @http.route('/address', type='http', auth='public', methods=['POST'], csrf=False)
    def create_address(self, **kwargs):
        kwargs = request.get_json_data()
        if not kwargs or not kwargs.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone', '=', kwargs['mobile'])
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {kwargs['mobile']} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم. {kwargs['mobile']}"
            ])
        if customer.child_ids.filtered(lambda address: address.name==kwargs['nickname']):
            return self.make_response(False, 400, [], None, [
                f"Address {kwargs['nickname']} already exist for customer {customer.name}.",
                f"{kwargs['nickname']} العنوان الذي أدخلته مسجل بالفعل. {customer.name}."
            ])
        keys_to_update = ['name','street_id', 'state_id', 'district_id', 'zip', 'floor_number', 'house_number','shift_id','apartment_no', 'comments','is_default_address', 'partner_latitude', 'partner_longitude']
        address_vals = {key: kwargs[key] for key in keys_to_update if key in kwargs}
        address_vals['type'] = 'other'
        
        if 'city_id' not in kwargs:
            default_city = request.env['res.country.state'].sudo().search([('active', '=', True)], limit=1)
            if default_city:
                address_vals['state_id'] = default_city.id
        if 'district_id' not in kwargs:
            default_district = request.env['customer.district'].sudo().search([('is_default', '=', True)], limit=1)
            if default_district:
                address_vals['district_id'] = default_district.id
        if 'district_id' in kwargs:
            district = request.env['customer.district'].sudo().search([('id', '=', kwargs.get('district_id'))], limit=1)
            address_vals['shift_id'] = district.shift_id.id

        customer.sudo().child_ids = [(0,0, address_vals)]
        customer.sudo().message_post(body=f"Address created for customer from customer app.")
        if not customer.customer_address_id and customer.child_ids:
            customer.customer_address_id = customer.child_ids[-1]
        return self.make_response(True, 200, [], None, [])
   
    
    @validate_token
    @http.route('/address', type='http', auth='public', methods=['PATCH'], csrf=False)
    def update_address(self, **kwargs):
        kwargs = request.get_json_data()
        if not kwargs or not kwargs.get('address_id', False):
            return self.make_response(False, 400, [], None, [
                "Address ID not given.",
                "يرجى ادخال العنوان."
            ])
        address = request.env['res.partner'].sudo().browse(kwargs['address_id'])
        if not address:
            return self.make_response(False, 400, [], None, [
                f"Address with ID {kwargs['address_id']} doesn't exist.",
                f"العنوان المطلوب غير موجود. {kwargs['address_id']}"
            ])
        keys_to_update = ['name', 'street_id', 'state_id', 'district_id', 'zip','floor_number','house_number','apartment_no', 'comments', 'shift_id','is_default_address', 'partner_latitude', 'partner_longitude']
        update_vals = {key: kwargs[key] for key in keys_to_update if key in kwargs}
        update_vals['type'] = 'other'
        
        address.sudo().write(update_vals)
        address.parent_id.sudo().message_post(body=f"Address updated from customer app.")
        return self.make_response(True, 200, [], None, [])
    
    @validate_token
    @http.route('/address', type='http', auth='public', methods=['DELETE'], csrf=False)
    def delete_address(self, **kwargs):
        address = request.env['res.partner'].sudo().browse(int(kwargs.get('address_id')))
        if not address:
            return self.make_response(False, 400, [], None, [
                "Address ID not given or address doesn't exist.",
                "Address ID not given or address doesn't exist."
            ])
        try:
            parent = address.parent_id
            parent.message_post(body=f"Address {address.name} deleted from customer app.")
            address.sudo().unlink()
            if parent.child_ids:
                previous_address_id = parent.child_ids[-1].id
                if previous_address_id:
                    parent.customer_address_id = previous_address_id
            else:
                parent.customer_address_id = False
            return self.make_response(True, 200, [], None, [])
        except Exception as e:
            return self.make_response(False, 500, [], None, [str(e), str(e)])
    
    @validate_token
    @http.route('/meal_category', type='http', auth='public', methods=['GET'], csrf=False)
    def get_meal_categories(self, **data_passed):
        available_meal_categories = request.env['meals.category'].sudo().search([])
        meal_category_data = [{
            "id": categ.id,
            "name": categ.name or '',
            "arabic_name": categ.arabic_name or '',
        } for categ in available_meal_categories]
        if meal_category_data:
            return self.make_response(True, 200, [], meal_category_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No meal categories found.",
                "لم يتم العثور على تصنيفات للوجبات."
            ])
        
    @validate_token
    @http.route('/meal_category/<category>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_meal_category_by_id(self, category):
        if not category:
            return self.make_response(False, 400, [], None, [
                "No category ID passed.",
                "يرجى إدخال التصنيف."
            ])
        available_meal_categories = request.env['meals.category'].sudo().browse(int(category))
        meal_category_data = [{
            "id": categ.id,
            "name": categ.name or '',
            "arabic_name": categ.arabic_name or '',
        } for categ in available_meal_categories]
        if meal_category_data:
            return self.make_response(True, 200, [], meal_category_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                f"No meal categories found with the ID {category}",
                f"No meal categories found with the ID {category}"
            ])
    
    @validate_token
    @http.route('/meal', type='http', auth='public', methods=['GET'], csrf=False)
    def get_meals(self, **data_passed):
        domain =[('is_meal', '=', True)]
        available_meals = request.env['product.template'].sudo().search(domain)
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        meals_data = [{
            "id": meal.id,
            "name": meal.name or "",
            "description": meal.meal_description or '',
            "arabic_name": meal.arabic_name or '',
            "arabic_description": meal.arabic_meal_description or '',
            "meal_category": meal.meal_category_id.ids,
            "image": f'{base_url}/web/image?model=product.template&id={meal.id}&field=image_1920' if meal.image_1920 else '',
            "tags": ', '.join(meal.meal_tag_id.mapped('name')) if meal.meal_tag_id else '',
            "calories": meal.calories or 0.0,
            "protein": meal.protein or 0.0,
            "carbs": meal.carbohydrates or 0.0,
            "fat": meal.fat or 0.0,
            "rating": meal.rating or 0,
            "rating_count": meal.rating_count or 0,
            "price": meal.list_price or 0.0,
            "ingredients": [
                {"image": f'{base_url}/web/image?model=product.template&id={ingre.ingredient_id.id}&field=image_1920' if ingre.ingredient_id.image_1920 else ''} 
                for ingre in meal.ingredients_line_ids
            ] if meal.ingredients_line_ids else []
        } for meal in available_meals]
        if meals_data:
            return self.make_response(True, 200, [], meals_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No meals found.",
                "No meals found."
            ])

    @validate_token
    @http.route('/meal/category/<category>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_meals_by_category(self, category):
        if not category:
            return self.make_response(False, 400, [], None, [
                "No category ID passed.",
                "يرجى إدخال التصنيف."
            ])
        domain =[('is_meal', '=', True), ('meal_category_id', '=', int(category))]
        available_meals = request.env['product.template'].sudo().search(domain)
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        meals_data = [{
            "id": meal.id,
            "name": meal.name or "",
            "description": meal.meal_description or '',
            "arabic_name": meal.arabic_name or '',
            "arabic_description": meal.arabic_meal_description or '',
            "image": f'{base_url}/web/image?model=product.template&id={meal.id}&field=image_1920' if meal.image_1920 else '',
            "tags": ', '.join(meal.meal_tag_id.mapped('name')) if meal.meal_tag_id else '',
            "calories": meal.calories or 0.0,
            "protein": meal.protein or 0.0,
            "carbs": meal.carbohydrates or 0.0,
            "fat": meal.fat or 0.0,
            "rating": meal.rating or 0,
            "rating_count": meal.rating_count or 0,
            "price": meal.list_price or 0.0,
            "ingredients": [
                {
                    "id": ingre.ingredient_id.id,
                    "name": ingre.ingredient_id.name or "",
                    "arabic_name": ingre.ingredient_id.arabic_name or "",
                    "image": f'{base_url}/web/image?model=product.template&id={ingre.ingredient_id.id}&field=image_1920' if ingre.ingredient_id.image_1920 else ''
                } 
                for ingre in meal.ingredients_line_ids
            ] if meal.ingredients_line_ids else []
        } for meal in available_meals]
        if meals_data:
            return self.make_response(True, 200, [], meals_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No meals found.",
                "No meals found."
            ])
    
    @validate_token
    @http.route('/meal/<meal>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_meal_by_id(self, meal):
        if not meal:
            return self.make_response(False, 400, [], None, [
                "No meal ID passed.",
                "No meal ID passed."
            ])
        available_meals = request.env['product.template'].sudo().browse(int(meal))
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        meal_data = [{
            "id": meal.id,
            "name": meal.name or "",
            "description": meal.meal_description or '',
            "arabic_name": meal.arabic_name or '',
            "arabic_description": meal.arabic_meal_description or '',
            "image": f'{base_url}/web/image?model=product.template&id={meal.id}&field=image_1920' if meal.image_1920 else '',
            "tags": ', '.join(meal.meal_tag_id.mapped('name')) if meal.meal_tag_id else '',
            "calories": meal.calories or 0.0,
            "protein": meal.protein or 0.0,
            "carbs": meal.carbohydrates or 0.0,
            "fat": meal.fat or 0.0,
            "rating": meal.rating or 0,
            "rating_count": meal.rating_count or 0,
            "price": meal.list_price or 0.0,
            "ingredients": [
                {"image": f'{base_url}/web/image?model=product.template&id={ingre.ingredient_id.id}&field=image_1920' if ingre.ingredient_id.image_1920 else ''} 
                for ingre in meal.ingredients_line_ids
            ] if meal.ingredients_line_ids else []
        } for meal in available_meals]
        if meal_data:
            return self.make_response(True, 200, [], meal_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                f"No meal found with the ID {meal}",
                f"No meal found with the ID {meal}"
            ])
        
    @validate_token
    @http.route('/ingredient/search/<keyword>', type='http', auth='public', methods=['GET'], csrf=False)
    def search_ingredient(self, keyword):
        result = {'categories':[], 'ingredients':[]}
        category_ids = request.env['meal.ingredient.category'].sudo().search([
            ('name','ilike',keyword)
        ])
        result['categories'] += [{
            'id': categ.id,
            'name': categ.name or "",
            'arabic_name': categ.arabic_name or ""
        } for categ in category_ids]
        ingredient_ids = request.env['product.template'].sudo().search([
            ('is_ingredient','=',True),('name','ilike',keyword)
        ])
        result['ingredients'] += [{
            'id': ingre.id,
            'name': ingre.name or "",
            'arabic_name': ingre.arabic_name or ""
        } for ingre in ingredient_ids]
        return self.make_response(True, 200, [], [result], [])
    
    @validate_token
    @http.route('/ingredient_category', type='http', auth='public', methods=['GET'], csrf=False)
    def get_ingredient_category(self, **data_passed):
        available_ingredient_categories = request.env['product.template'].sudo().search([('is_ingredient', '=',True)]).mapped('ingredient_category_id')
        ingredient_category_data = [{
            "id": categ.id,
            "name": categ.name if categ.name else "",
            "arabic_name": categ.arabic_name if categ.arabic_name else "",
        } for categ in available_ingredient_categories]
        if available_ingredient_categories:
            return self.make_response(True, 200, [], ingredient_category_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No ingredient categories found.",
                "لم يتم العثور على تصنيفات للمكونات."
            ])
    
    @validate_token
    @http.route('/ingredient_category/<category>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_ingredient_category_by_id(self, category):
        if not category:
            return self.make_response(False, 400, [], None, [
                "No category ID passed.",
                "يرجى إدخال التصنيف."
            ])
        available_ingredient_categories = request.env['meal.ingredient.category'].sudo().browse(int(category))
        ingredient_category_data = [{
            "id": categ.id,
            "name": categ.name or "",
            "arabic_name": categ.arabic_name or "",
        } for categ in available_ingredient_categories]
        if available_ingredient_categories:
            return self.make_response(True, 200, [], ingredient_category_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                f"No ingredient categories found with the ID {category}",
                f"No ingredient categories found with the ID {category}"
            ])
        
    @validate_token
    @http.route('/ingredient', type='http', auth='public', csrf=False)
    def get_ingredients(self, **data_passed):
        domain = [('is_ingredient', '=', True)]
        available_ingredients = request.env['product.template'].sudo().search(domain)
        ingredients_data = [{
            "id": ingredient.id,
            "name": ingredient.name or "",
            "arabic_name": ingredient.arabic_name or "",
        } for ingredient in available_ingredients]
        if available_ingredients:
            return self.make_response(True, 200, [], ingredients_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No ingredients found",
                "لا توجد مكونات مطابقة."
            ])

    @validate_token
    @http.route('/ingredient/category/<category>', type='http', auth='public', csrf=False)
    def get_ingredientsby_category(self, category):
        domain = [('is_ingredient', '=', True)]
        if category:
            domain.append(('ingredient_category_id','=', int(category)))
        else:
            return self.make_response(False, 400, "", None, "No category ID passed.")
        available_ingredients = request.env['product.template'].sudo().search(domain)
        ingredients_data = [{
            "id": ingredient.id,
            "name": ingredient.name or "",
            "arabic_name": ingredient.arabic_name or "",
        } for ingredient in available_ingredients]
        if available_ingredients:
            return self.make_response(True, 200, [], ingredients_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No ingredients found",
                "لا توجد مكونات مطابقة."
            ])
    
    @validate_token
    @http.route('/ingredient/<ingredient>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_ingredient_by_id(self, ingredient):
        if not ingredient:
            return self.make_response(False, 400, [], None, [
                "Ingredient ID not passed.",
                "يرجى إدخال ID المكون."
            ])
        available_ingredients = request.env['product.template'].sudo().browse(int(ingredient))
        ingredient_data = [{
            "id": ingre.id,
            "name": ingre.name or "",
            "arabic_name": ingre.arabic_name or "",
        } for ingre in available_ingredients]
        if available_ingredients:
            return self.make_response(True, 200, [], ingredient_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No ingredient found with the ID {ingredient}",
                "المكون المطلوب غير موجود. {ingredient}"
            ])
    
    @validate_token
    @http.route('/plan_categories', type='http', auth='public', methods=['GET'], csrf=False)
    def get_plan_categories(self, **data_passed):
        available_plan_categories = request.env['plan.category'].sudo().search([])
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        plan_category_data = [{
            "id": categ.id,
            "name": categ.name if categ.name else "",
            "arabic_name": categ.arabic_name if categ.arabic_name else "",
            "image": f'{base_url}/web/image?model=plan.category&id={categ.id}&field=image' if categ.image else '',
        } for categ in available_plan_categories]
        if available_plan_categories:
            return self.make_response(True, 200, [], plan_category_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No plan categories found.",
                "لا توجد تصنيفات للخطط الغذائية."
            ])
    
    @validate_token
    @http.route('/plan_category/<category>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_plan_category_by_id(self, category):
        if not category:
            return self.make_response(False, 400, [], None, [
                "Plan category ID not passed.",
                "يرجى إدخال ID النظام الغذائية."
            ])
        available_plan_categories = request.env['plan.category'].sudo().browse(int(category))
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        plan_category_data = [{
            "id": categ.id,
            "name": categ.name or "",
            "arabic_name": categ.arabic_name or "",
            "image": f'{base_url}/web/image?model=plan.category&id={categ.id}&field=image' if categ.image else '',
        } for categ in available_plan_categories]
        if available_plan_categories:
            return self.make_response(True, 200, [], plan_category_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                f"No plan categories found with the ID {category}",
                f"No plan categories found with the ID {category}"
            ])
        
    @validate_token
    @http.route('/plan', type='http', auth='public', methods=['GET'], csrf=False)
    def get_subscription_plans(self, **data_passed):
        available_plans = request.env['subscription.package.plan'].sudo().search([('active', '=', True)], order='sequence')
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        plans_data = []
        for plan in available_plans:
            meal_configuration = []
            meal_configuration_arabic = []
            for meal in plan.meal_config_ids:
                if meal.meal_count > 0:
                    meal_configuration.append(f"{meal.meal_count} - {meal.meal_category_id.name}")
                    meal_configuration_arabic.append(f"{meal.meal_count} - {meal.meal_category_id.arabic_name}")
            plan_details = {
                "id": plan.id,
                "name": plan.name or "",
                "arabic_name": plan.arabic_name or "",
                "description": plan.description or "",
                "arabic_description": plan.arabic_description or "",
                "protein": plan.protein or 0.0,
                "carbs": plan.carbohydrates or 0.0,
                "calories": plan.calories or 0.0,
                "image": f'{base_url}/web/image?model=subscription.package.plan&id={plan.id}&field=image' if plan.image else '',
                "meal_configuration": meal_configuration,
                "meal_configuration_arabic": meal_configuration_arabic
            }
            plans_data.append(plan_details)
        if available_plans:
            return self.make_response(True, 200, [], plans_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No plans found",
                "لم يتم العثور على الخطط الغذائية متاحة."
            ])
    
    @validate_token
    @http.route('/plan_choice/<plan>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_subscription_plan_choices(self, plan, **data_passed):
        if not plan or not plan.isdigit():
            return self.make_response(False, 400, [], None, [
                "Plan ID not passed.",
                "يرجى إدخال ID  النظام المطلوبة."
            ])
        available_plan = request.env['subscription.package.plan'].sudo().browse(int(plan))
        if not available_plan:
            return self.make_response(False, 400, [], None, [
                f"No plan found with the ID {plan}",
                f"No plan found with the ID {plan}"
            ])
        for plan in available_plan:
            meal_configuration = []
            meal_configuration_arabic = []
            for meal in plan.meal_config_ids:
                if meal.meal_count > 0:
                    meal_configuration.append(f"{meal.meal_count} - {meal.meal_category_id.name}")
                    meal_configuration_arabic.append(f"{meal.meal_count} - {meal.meal_category_id.arabic_name}")
        choice_data = [{
            "id": choice.id,
            "name": choice.name or "",
            "arabic_name": choice.arabic_name or "",
            "duration_type": dict(choice._fields['duration_type'].selection).get(choice.duration_type) or "",
            "duration_type_arabic" : dict(choice._fields['duration_type_arabic'].selection).get(choice.duration_type_arabic) or "",
            "days_count": choice.no_of_day,
            "strike_price": choice.strike_through_price if choice.is_strike_through else "",
            "price": choice.plan_tax_amount or 0.0,
            "protein": choice.plan_config_day_id.protein or 0.0,
            "carbohydrates": choice.plan_config_day_id.carbohydrates or 0.0,
            "fat": choice.plan_config_day_id.fat or 0.0,
            "meal_configuration": meal_configuration,
            "meal_configuration_arabic": meal_configuration_arabic,
            "available_days": {
                "sunday": choice.sunday,
                "monday": choice.monday,
                "tuesday": choice.tuesday,
                "wednesday": choice.wednesday,
                "thursday": choice.thursday,
                "friday": choice.friday,
                "saturday": choice.saturday
            }
        } for choice in available_plan.day_choice_ids]
        order = {"Day": 0, "Week": 1, "Month": 2}
        choice_data = sorted(choice_data, key=lambda x: order[x["duration_type"]])
        if choice_data:
            return self.make_response(True, 200, [], choice_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No plans found",
                "لم يتم العثور على الخطط الغذائية متاحة."
            ])

    @validate_token
    @http.route('/plan/category/<category>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_subscription_plan_by_category(self, category, **data_passed):
        if not category:
            return self.make_response(False, 400, [], None, [
                "Category ID not passed.",
                "Category ID not passed."
            ])
        domain = [('active', '=', True), ('plan_category_id', '=', int(category))]
        duration = data_passed.get('duration', False)
        if duration:
            domain.append(('duration_days','=',duration))
        available_plans = request.env['subscription.package.plan'].sudo().search(domain, order='sequence')
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        plans_data = []
        for plan in available_plans:
            meal_configuration = []
            meal_configuration_arabic = []
            for meal in plan.meal_config_ids:
                if meal.meal_count > 0:
                    meal_configuration.append(f"{meal.meal_count} - {meal.meal_category_id.name}")
                    meal_configuration_arabic.append(f"{meal.meal_count} - {meal.meal_category_id.arabic_name}")
            plan_details = {
                "id": plan.id,
                "name": plan.name or "",
                "arabic_name": plan.arabic_name or "",
                "description": plan.description or "",
                "arabic_description": plan.arabic_description or "",
                "protein": plan.protein or 0.0,
                "carbs": plan.carbohydrates or 0.0,
                "calories": plan.calories or 0.0,
                "image": f'{base_url}/web/image?model=subscription.package.plan&id={plan.id}&field=image' if plan.image else '',
                "meal_configuration": meal_configuration,
                "meal_configuration_arabic": meal_configuration_arabic
            }
            plans_data.append(plan_details)
        if available_plans:
            return self.make_response(True, 200, [], plans_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No plans found",
                "لم يتم العثور على الخطط الغذائية متاحة."
            ])

    @validate_token
    @http.route('/plan/<plan>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_subscription_plan_by_id(self, plan, **data_passed):
        if not plan:
            return self.make_response(False, 400, [], None, [
                "Plan ID not passed.",
                "يرجى إدخال ID  النظام المطلوبة."
            ])
        available_plans = request.env['subscription.package.plan'].sudo().search([('id','=',plan)])
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        plans_data = []
        for plan in available_plans:
            meal_configuration = []
            meal_configuration_arabic = []
            for meal in plan.meal_config_ids:
                if meal.meal_count > 0:
                    meal_configuration.append(f"{meal.meal_count} - {meal.meal_category_id.name}")
                    meal_configuration_arabic.append(f"{meal.meal_count} - {meal.meal_category_id.arabic_name}")
            plan_details = {
                "id": plan.id,
                "name": plan.name or "",
                "arabic_name": plan.arabic_name or "",
                "description": plan.description or "",
                "arabic_description": plan.arabic_description or "",
                "protein": plan.protein or 0.0,
                "carbs": plan.carbohydrates or 0.0,
                "calories": plan.calories or 0.0,
                "image": f'{base_url}/web/image?model=subscription.package.plan&id={plan.id}&field=image' if plan.image else '',
                "meal_configuration": meal_configuration,
                "meal_configuration_arabic": meal_configuration_arabic
            }
            plans_data.append(plan_details)
        if available_plans:
            return self.make_response(True, 200, [], plans_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No plans found",
                "لم يتم العثور على الخطط الغذائية متاحة."
            ])
                    
    @validate_token
    @http.route('/reset_password', type='http', auth='public', methods=['PATCH'], csrf=False)
    def reset_password(self, **data_passed):
        data_passed = request.get_json_data()
        if 'mobile' not in data_passed or not data_passed['mobile']:
            return self.make_response(False, 400, [], None, [
                "No mobile number passed.",
                "No mobile number passed."
            ])
        if 'new_password' not in data_passed or not data_passed['new_password']:
            return self.make_response(False, 400, [], None, [
                "New password not passed.",
                "يرجى إدخال كلمة مرور جديدة."
            ])
        customer_id = request.env['res.partner'].search([
            ('phone', '=', data_passed['mobile'])
        ], limit=1)
        
        if customer_id:
            customer_id.write({
                "diet_app_password": data_passed['new_password'],
                'gender': data_passed.get('gender', False),
                'date_of_birth': datetime.strptime(data_passed.get('date_of_birth', '1900-1-1'), '%Y-%m-%d').date() if data_passed.get('date_of_birth', False) else date(1900,1,1),
                'email': data_passed.get('email', False),
            })
            customer_id.message_post(body=f"Password reset from customer app")
            return self.make_response(True, 200, [
                "Password changed successfully.",
                "تم تحديث كلمة المرور بنجاح."
            ], None, [])
        else:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile number {data_passed['mobile']} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم. {data_passed['mobile']}"
            ])
    
    @validate_token
    @http.route('/get_duration', type='http',auth='public', methods=['GET'],csrf=False)
    def get_duration_by_plan_category(self, **data_passed):
        try:
            category = data_passed['category']
        except KeyError:
            return self.make_response(False, 400, [], None, [
                "Category is not given",
                "لم يتم تحديد التصنيف."
            ])
        available_durations =request.env['subscription.package.plan'].sudo().search([('plan_category_id', '=', int(category))]).mapped('duration_days')
        unique_durations =[]
        for x in available_durations:
            if x not in unique_durations:
                unique_durations.append(x)
        unique_durations.sort()
        duration_data = unique_durations
        if available_durations:
            return self.make_response(True, 200, [
                f"Found {len(unique_durations)} durations.",
                f"Found {len(unique_durations)} durations."
            ], duration_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No durations found",
                "لم يتم العثور على مدد زمنية متاحة."
            ])
        
    @http.route('/get_plan_end_date', type='http', auth='public', methods=['GET'], csrf=False)
    def get_plan_end_date(self, **kwargs):
        kwargs = request.get_json_data()
        if 'plan_id' not in kwargs:
            return self.make_response(False, 400, [], None, [
                'Plan ID not passed.',
                'يرجى إدخال ID  النظام المطلوبة.'
            ])
        plan_id = kwargs['plan_id']
        plan = request.env['subscription.package.plan'].sudo().browse(int(plan_id))
        if 'start_date' not in kwargs:
            return self.make_response(False, 400, [], None, [
                'Start date not passed.',
                'يرجى إدخال تاريخ البدء.'
            ])
        try:
            start_date = datetime.strptime(kwargs['start_date'], '%Y-%m-%d').date()
        except Exception as e:
            return self.make_response(False, 400, [], None, [
                'Invalid date format. Send date in YYYY-MM-DD format.',
                'صيغة التاريخ غير صحيحة. يرجى استخدام صيغة YYYY-MM-DD.'
            ])
        end_date = start_date + timedelta(days=plan.duration_days)
        return self.make_response(True, 200, [
            'End date calculated successfully.',
            'تم احتساب تاريخ الانتهاء بنجاح.'
        ], [{'end_date': end_date.strftime('%Y-%m-%d') if end_date else '1900-01-01'}], [])
    
    
    @validate_token
    @http.route('/subscription', type='http', auth='public', methods=['POST'], csrf=False)
    def create_subscription_order(self, **kwargs):
        kwargs = request.get_json_data()
        required_data = [
            'mobile',
            'plan_id',
            'plan_choice_id',
            'start_date',
            'promo_code',
            'apply_reward_points'
        ]
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if any(key not in kwargs for key in required_data):
            return self.make_response(False, 400, [], None, [
                "Required data not passed.",
                "البيانات المطلوبة غير مكتملة."
            ])
        mobile = kwargs['mobile']
        customer = request.env['res.partner'].sudo().search([
            ('phone','=',mobile)
        ],limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f'Customer with mobile number {mobile} not found.',
                f'Customer with mobile number {mobile} not found.'
            ])
        promo_code = kwargs.get('promo_code', False)
        subscription_lines = request.env['diet.subscription.order'].sudo()
        plan_id = kwargs['plan_id']
        plan = request.env['subscription.package.plan'].sudo().browse(int(plan_id))
        if not plan:
            return self.make_response(False, 400, [], None, [
                f'Plan with ID {plan_id} not found.',
                f'النظام الغذائية التي تبحث عنها غير موجودة. {plan_id}'
            ])
        choice_id = kwargs['plan_choice_id']
        choice = request.env['plan.choice'].sudo().browse(int(choice_id))
        if not choice:
            return self.make_response(False, 400, [], None, [
                f'Plan choice with ID {choice_id} not found.',
                f'الخيار المحدد للخطة الغذائية غير متاح. {choice_id}'
            ])
        start_date = datetime.strptime(kwargs['start_date'], '%Y-%m-%d').date()
        week = 7
        excluded_weekdays = []
        if not choice.monday:
            excluded_weekdays.append(0)
        if not choice.tuesday:
            excluded_weekdays.append(1)
        if not choice.wednesday:
            excluded_weekdays.append(2)
        if not choice.thursday:
            excluded_weekdays.append(3)
        if not choice.friday:
            excluded_weekdays.append(4)
        if not choice.saturday:
            excluded_weekdays.append(5)
        if not choice.sunday:
            excluded_weekdays.append(6)
        end_date = request.env['diet.subscription.order']._get_end_date(excluded_weekdays, choice.no_of_day, start_date)
        overlapping_subscriptions_query = """SELECT id FROM customer_sale_order_line WHERE partner_id = %s AND state IN ('in_progress') 
                                                AND ('%s' BETWEEN actual_start_date AND end_date
                                                OR '%s' BETWEEN actual_start_date AND end_date)""" % (
                customer.id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
            )
        request.env.cr.execute(overlapping_subscriptions_query)
        overlapping_subscriptions = request.env.cr.fetchall()
        if overlapping_subscriptions:
            return self.make_response(False, 400, [], None, [
                f'The subscription period for customer overlaps with another subscription.',
                f'هناك تداخل بين فترة الاشتراك والاشتراك الحالي.'
            ])
        subscription_vals = {
            'partner_id': customer.id,
            'plan_id': plan.id,
            'actual_start_date': start_date,
            'end_date': end_date,
            'plan_choice_id':choice.id,
            'created_by': customer.id,
            'promo_code': promo_code,
            'payment_type': 'on_line'
        }
        apply_reward_points = kwargs['apply_reward_points']
        new_subscription = request.env['diet.subscription.order'].sudo().create(subscription_vals).with_context(skip_base_price_calculation=True)
        customer.message_post(body=f"Subscription created from customer app.")
        new_subscription.message_post(body=f"Subscription created from customer app.")
        subscription_lines |= new_subscription
        if subscription_lines:
            response_subs_data = []
            for subs in subscription_lines:
                subs._onchange_plan_id()
                subs._onchange_end_date()
                subs.onchange_meal_count_generation()
                subs._onchange_ramdan_meal_count_generation()
                subs.available_days()
                if promo_code and subs:
                    try:
                        subs.verify_promo_code()
                        subs.message_post(body=f"Subscription activated from customer app.")
                    except Exception as e:
                        return self.make_response(False, 400, [], None, [str(e), str(e)])
                if apply_reward_points:
                    subs.apply_reward_points()
                subs.with_context(from_mobile=True).confirm()
                subs.generate_meal_calendar()
                invoice_ref = False
                invoice = False
                if subs.invoice_ids:
                    invoice = subs.invoice_ids[0]
                    invoice_ref = invoice.name
                    if invoice.amount_total > 0.0:
                        invoice.process_tap_payment()
                subscription_details = {
                    'subscription_id': subs.id,
                    'subscription_number': subs.order_number,
                    'plan_id': subs.plan_id.id,
                    'plan_name': subs.plan_id.name,
                    'plan_arabic_name': subs.plan_id.arabic_name,
                    'start_date': subs.actual_start_date.strftime('%Y-%m-%d') if subs.actual_start_date else '1900-01-01',
                    'end_date': subs.end_date.strftime('%Y-%m-%d') if subs.end_date else '1900-01-01',
                    'total': subs.total if subs.total else 0.0,
                    'plan_base_price':subs.grand_total if subs.grand_total else 0.0,
                    'tax': subs.amount_tax if subs.amount_tax else 0.0,
                    'coupon_discount': subs.coupon_discount if subs.coupon_discount else 0.0,
                    'promo_code_discount': subs.promo_code_discount if subs.promo_code_discount else 0.0,
                    'grand_total': subs.grand_total if subs.grand_total else 0.0,
                }
                response_subs_data.append({'order_reference':subs.order_number if subs.order_number else '',
                                           'payment_reference':invoice_ref if invoice_ref else '',
                                            "transaction_url": invoice.tap_payment_transaction_url if invoice else '',
                                            "redirect_url": invoice.tap_payment_redirect_url if invoice else '',
                                            "post_url": f"{base_url}/payment/tap/webhook",
                                            "payment_status_url": f"{base_url}/payment/status",
                                           'plan_id':subs.plan_id.id if subs.plan_id else 0,
                                           'plan_name':subs.plan_id.name if subs.plan_id else '',
                                           'duration':subs.plan_id.duration_days if subs.plan_id else 0,
                                           'start_date':subs.actual_start_date.strftime('%Y-%m-%d') if subs.actual_start_date else '1900-01-01',
                                           'end_date':subs.end_date.strftime('%Y-%m-%d') if subs.end_date else '1900-01-01',
                                           'amount':subs.total if subs.total else 0.0,
                                           'subscription_details': subscription_details})
            return self.make_response(True, 200, [], response_subs_data, []) 
        else:
            return self.make_response(False, 400, [], None, [
                f'Subscription creation for {customer.name} failed.',
                f'فشل في إتمام عملية الاشتراك. {customer.name}'
            ])
    
    @validate_token
    @http.route('/subscription/<mobile>', type='http', auth='public',methods=['GET'], csrf=False)
    def get_customer_subscriptions(self, mobile, **kwargs):
        if not mobile:
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone','=',mobile)
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} not found.",
                f"Customer with mobile {mobile} not found."
            ])
        subscriptions = []
        for subscription in customer.customer_sale_order_line_ids.filtered(
            lambda subs: subs.state in ['in_progress','paid']
        ):
            meal_configuration = []
            for count in subscription.meal_count_ids:
                meal_configuration.append(f"{count.additional_count} - {count.meal_category_id.name}")

            subscription_val = {
                'subscription_id': subscription.id,
                'subscription_number': subscription.order_number if subscription.order_number else '',
                'subscription_status': subscription.state if subscription.state else '',
                'plan_id': subscription.plan_id.id if subscription.plan_id else 0,
                'plan_name': subscription.plan_id.name if subscription.plan_id.name else '',
                'plan_arabic_name': subscription.plan_id.arabic_name if subscription.plan_id.arabic_name else '',
                'plan_duration': subscription.plan_id.duration_days if subscription.plan_id.duration_days else 0,
                'start_date': subscription.actual_start_date.strftime('%Y-%m-%d') if subscription.actual_start_date else '1900-01-01',
                'end_date': subscription.end_date.strftime('%Y-%m-%d') if subscription.end_date else '1900-01-01',
                'total': subscription.total if subscription.total else 0.0,
                'coupon_discount': subscription.coupon_discount if subscription.coupon_discount else 0.0,
                'grand_total': subscription.grand_total if subscription.grand_total else 0.0,
                'meals_count': len(subscription.meal_line_ids) if subscription.meal_line_ids else 0,
                "meal_configuration": meal_configuration
            }
            freezed_calendar_vals = request.env['customer.meal.calendar'].sudo().search([
                ('so_id','=',subscription.id),
                ('state','=','freezed')
            ])
            if freezed_calendar_vals:
                freezed_days = [fday.date.strftime('%Y-%m-%d') if fday.date else '1900-01-01' for fday in freezed_calendar_vals]
                subscription_val.update({'freeze_days': list(set(freezed_days))})
            subscriptions.append(subscription_val)
        if subscriptions:
            return self.make_response(True, 200, [], subscriptions, [])
        else:
            return self.make_response(False, 400, [], None, [
                f'No subscriptions found for {customer.customer_sequence_no} - {customer.name} - {customer.phone}',
                f'لا توجد اشتراكات مسجلة. {customer.customer_sequence_no} - {customer.name} - {customer.phone}'
            ])
        
    # @validate_token
    # @http.route('/get_weekday_meals', type='http', auth='public', methods=['GET'], csrf=False)
    # def get_weekday_meals(self, **kwargs):
    #     if not kwargs.get('subscription_id', False):
    #         return self.make_response(False, 400, "", None, 'Subscription ID not passed.')
    #     if not kwargs.get('day', False):
    #         return self.make_response(False, 400, "", None,'Day of week not passed.')
    #     if not kwargs.get('meal_category_id', False):
    #         return self.make_response(False, 400, "", None,'Meal type not passed.')
    #     subscription = request.env['diet.subscription.order'].sudo().browse(int(kwargs['subscription_id']))
    #     if not subscription:
    #         return self.make_response(False, 400, "", None,f"Suscription with ID {kwargs['mobile']} not found.")
    #     meal_category = request.env['meals.category'].sudo().browse(int(kwargs['meal_category_id']))
    #     if not meal_category:
    #         return self.make_response(False, 400, "", None,f'Meal category with ID {kwargs["meal_category_id"]} not found.')
    #     category_meal_line = subscription.meal_line_ids.filtered(
    #         lambda meal_line: meal_line.meal_category_id == meal_category
    #     )
    #     if category_meal_line:
    #         category_meal_line = category_meal_line[0]
    #     day = kwargs['day']
    #     if day not in ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']:
    #         return self.make_response(False, 400, "", None,'Invalid day passed. Day can any of sunday,monday,tuesday,wednesday,thursday,friday,saturday')
    #     available_meal_options = []
    #     if day == 'sunday':
    #         day_meal_ids = category_meal_line.domain_for_sunday_meal_ids
    #     elif day == 'monday':
    #         day_meal_ids = category_meal_line.domain_for_monday_meal_ids
    #     elif day == 'tuesday':
    #         day_meal_ids = category_meal_line.domain_for_tuesday_meal_ids
    #     elif day == 'wednesday':
    #         day_meal_ids = category_meal_line.domain_for_wednesday_meal_ids
    #     elif day == 'thursday':
    #         day_meal_ids = category_meal_line.domain_for_thursday_meal_ids
    #     elif day == 'friday':
    #         day_meal_ids = category_meal_line.domain_for_friday_meal_ids
    #     elif day == 'saturday':
    #         day_meal_ids = category_meal_line.domain_for_saturday_meal_ids
    #     else:
    #         day_meal_ids = False
    #     base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     for meal in day_meal_ids:
    #         available_meal_options.append({
    #             'id': meal.id,
    #             'name': meal.name if meal.name else '',
    #             'name_arabic': meal.arabic_name if meal.arabic_name else '',
    #             'description': meal.meal_description if meal.meal_description else '',
    #             'description_arabic': meal.arabic_meal_description if meal.arabic_meal_description else '',
    #             'image': f'{base_url}/web/image?model=product.template&id={meal.id}&field=image_1920' if meal.image_1920 else '',
    #             'protein': meal.protein if meal.protein else 0.0,
    #             'carbohydrates': meal.carbohydrates if meal.carbohydrates else 0.0,
    #             'fat': meal.fat if meal.fat else 0.0,
    #             'calories': meal.calories if meal.calories else 0.0,
    #             "rating": meal.rating if meal.rating else 0,
    #             "rating_count": meal.rating_count if meal.rating_count else 0
    #         })
    #     if available_meal_options:
    #         return self.make_response(True, 200, f'Received meals data for {day} {meal_category.name}',available_meal_options, "")
    #     else:
    #         return self.make_response(False, 400, "", None,f'No meals found for {subscription.partner_id.name} on subscription {subscription.order_number} for {meal_category.name} on {day}.')

    @validate_token
    @http.route('/set_weekday_meals', type='http', auth='public', methods=['PATCH'], csrf=False)
    def set_weekday_meals(self, **kwargs):
        kwargs = request.get_json_data()
        _logger.info(f"{kwargs}")
        if not kwargs.get('subscription_id', False):
            return self.make_response(False, 400, [], None, [
                'Subscription ID not passed.',
                'يرجى إدخال ID الاشتراك.'
            ])
        if not kwargs.get('date', False):
            return self.make_response(False, 400, [], None,[
                'Day of week not passed.',
                'يرجى تحديد اليوم المطلوب.'
            ])
        if not kwargs.get('meal_config', False):
            return self.make_response(False, 400, [], None,[
                'Meals not passed.',     
                'لم يتم إدخال بيانات الوجبات.'
            ])
        subscription = request.env['diet.subscription.order'].sudo().browse(int(kwargs['subscription_id']))
        if not subscription:
            return self.make_response(False, 400, [], None,[
                f"Suscription with ID {kwargs['mobile']} not found.",
                f"Suscription with ID {kwargs['mobile']} not found."
            ])
        meal_category_ids = kwargs['meal_config'][0]
        meal_category_ids = [int(x) for x in meal_category_ids]
        meal_category = request.env['meals.category'].sudo().search([('id','in',meal_category_ids)])
        if not meal_category:
            return self.make_response(False, 400, [], None,[
                f'Meal category with ID {kwargs["meal_category_id"]} not found.',
                f'Meal category with ID {kwargs["meal_category_id"]} not found.'
            ])
        try:
            calendar_date = datetime.strptime(kwargs['date'], '%Y-%m-%d').date()
        except:
            return self.make_response(False, 400, [], None,[
                'Invalid date format. Send date in YYYY-MM-DD format.',
                'صيغة التاريخ غير صحيحة. يرجى استخدام صيغة YYYY-MM-DD.'
            ])                
        try:
            for category in meal_category:
                calendar_id = request.env['customer.meal.calendar'].sudo().search([
                    ('so_id','=',subscription.id),
                    ('date','=',calendar_date),
                    ('meal_category_id','=',category.id),
                    ('state', 'in', ['active','active_with_meal']) 
                ])
                if not calendar_id:
                    return self.make_response(False, 400, [], None, [
                        f'No subscription found for {subscription.partner_id.name} on subscription {subscription.order_number} for {category.name} on {calendar_date}.',
                        f'No subscription found for {subscription.partner_id.name} on subscription {subscription.order_number} for {category.name} on {calendar_date}.'
                    ])
                recieved_meal_ids = kwargs['meal_config'][0][str(category.id)]
                calendar_with_new_meals_to_set = calendar_id[0:len(recieved_meal_ids)]
                calendar_without_new_meals_to_set = calendar_id - calendar_with_new_meals_to_set
                for i in range(len(recieved_meal_ids)):
                    calendar_with_new_meals_to_set[i].meal_id = recieved_meal_ids[i]
                    calendar_with_new_meals_to_set[i].meal_selection_by = 'customer'
                    calendar_with_new_meals_to_set[i]._onchange_state()
                for calendar in calendar_without_new_meals_to_set:
                    calendar.so_id.apply_default_meals_by_date_range(calendar.date, calendar.date)
                    calendar.meal_selection_by = 'system'
                    calendar._onchange_state()
            return self.make_response(True, 200, [
                f'Meals set successfully for {subscription.partner_id.name} on subscription {subscription.order_number} for {category.name} on {calendar_date}.',
                f'Meals set successfully for {subscription.partner_id.name} on subscription {subscription.order_number} for {category.name} on {calendar_date}.'
            ], None, [])
        except:
            return self.make_response(False, 400, [], None,[
                f'Error setting meals on {calendar_date.strftime("%d-%m-%Y")}. Please contact customer care.',            
                f'Error setting meals on {calendar_date.strftime("%d-%m-%Y")}. Please contact customer care.'
            ])
        
            

    @validate_token
    @http.route('/freeze_subscription', type='http', auth='public', methods=['PATCH'], csrf=False)
    def freeze_subscription(self, **kwargs):
        kwargs = request.get_json_data()
        _logger.info(f"{kwargs}")
        errors = []
        if not kwargs.get('subscription_id', False):
            return self.make_response(False, 400, [], None,[
                'Subscription ID not passed.',        
                'يرجى إدخال ID الاشتراك.'
            ])
        if not kwargs.get('freeze_dates', False):
            return self.make_response(False, 400, [], None, [
                'Dates to freeze not sent not passed.',
                'يرجى إدخال تواريخ التجميد.'
            ])
        try:
            freeze_dates = []
            for date in kwargs['freeze_dates']:
                freeze_dates.append(datetime.strptime(date, '%Y-%m-%d').date())
        except:
            return self.make_response(False, 400, [], None, [
                'Invalid start date format. Start date should be in YYYY-MM-DD',
                'صيغة تاريخ البداية غير صحيحة.  يرجى استخدام صيغة YYYY-MM-DD.'
            ])
        try:
            subscription = request.env['diet.subscription.order'].sudo().browse(int(kwargs['subscription_id']))
        except:
            return self.make_response(False, 400, [], None, [
                "Invalid subscription Id.", 
                "Invalid subscription Id."
            ])
        try:
            for freeze_date in freeze_dates:
                try:
                    subscription.with_context(skip_base_price_calculation=True).freeze_subscription_day(freeze_date)
                    subscription.sudo().message_post(body=f"Subscription freezed for {freeze_date.strftime('%d-%m-%Y')} from customer app.")
                except Exception as e:
                    errors.append((freeze_date, str(e)))  # Capture the error and continue
            if errors:
                error_messages = "; ".join([f"{date}: {msg}" for date, msg in errors])
                return self.make_response(True, 200, [
                    "Some dates could not be frozen.",
                    "فشل في عملية تجميد بعض الأيام، يرجى التواصل مع خدمة العملاء."
                ], error_messages, [
                    "please contact customer care.",
                    "please contact customer care."
                ])
            else:
                return self.make_response(True, 200, [
                    'Subscription freezed successfully.',
                    'تم تجميد الاشتراك بنجاح.'
                ], kwargs.get('freeze_dates', []), [])
        except Exception as e:
            return self.make_response(False, 400, [], None, [
                'Subscription freezing failed.',
                'فشل في تجميد الاشتراك.'
            ])
            
    @validate_token
    @http.route('/unfreeze_subscription', type='http', auth='public', methods=['PATCH'], csrf=False)
    def unfreeze_subscription(self, **kwargs):
        kwargs = request.get_json_data()
        _logger.info(f"{kwargs}")
        errors = []
        if not kwargs.get('subscription_id', False):
            return self.make_response(False, 400, [], None, [
                'Subscription ID not passed.',        
                'يرجى إدخال ID الاشتراك.'
            ])
        if not kwargs.get('freeze_dates', False):
            return self.make_response(False, 400, [], None, [
                'Dates to freeze not sent not passed.',
                'يرجى إدخال تواريخ التجميد.'
            ])
        try:
            freeze_dates = []
            for date in kwargs['freeze_dates']:
                freeze_dates.append(datetime.strptime(date, '%Y-%m-%d').date())
        except:
            return self.make_response(False, 400, "", None, [
                'Invalid start date format. Start date should be in YYYY-MM-DD',
                'صيغة تاريخ البداية غير صحيحة.  يرجى استخدام صيغة YYYY-MM-DD.'
            ])
        try:
            subscription = request.env['diet.subscription.order'].sudo().browse(int(kwargs['subscription_id']))
        except:
            return self.make_response(False, 400, "", None, [
                "Invalid subscription Id.", 
                "Invalid subscription Id."
            ])
        try:
            for freeze_date in freeze_dates:
                try:
                    subscription.with_context(skip_base_price_calculation=True).unfreeze_subscription_day(freeze_date)
                    subscription.sudo().message_post(body=f"Subscription unfreezed for {freeze_date.strftime('%Y-%m-%d')} from customer app.")
                except Exception as e:
                    errors.append((freeze_date, str(e)))  # Capture the error and continue
            if errors:
                error_messages = "; ".join([f"{date}: {msg}" for date, msg in errors])
                return self.make_response(True, 200, [
                    "Some dates could not be unfrozen.",
                    "Some dates could not be unfrozen."
                ], error_messages, [])
            else:
                return self.make_response(True, 200, [
                    'Subscription unfreezed successfully.',
                    'تم فك التجميد بنجاح.'
                ], kwargs.get('freeze_dates', []), [])
        except Exception as e:
            return self.make_response(False, 400, [], None, [
                'Subscription unfreezing failed.',   
                'فشل في عملية فك التجميد.'
            ])   
        
    @validate_token
    @http.route('/get_subscription_meal_by_date', type='http', auth='public', methods=['GET'], csrf=False)
    def get_subscription_meal_by_date(self, **kwargs):
        if not kwargs.get('subscription_id', False):
            return self.make_response(False, 400, [], None, [
                'Subscription ID not passed.',    
                'يرجى إدخال ID الاشتراك.'
            ])
        if not kwargs.get('meal_date', False):
            return self.make_response(False, 400, [], None, [
                'Date not passed.',
                'يرجى إدخال التاريخ المطلوب.'
            ])
        try:
            meal_date = datetime.strptime(kwargs['meal_date'], '%Y-%m-%d').date()
        except:
            return self.make_response(False, 400, [], None, [
                'Invalid meal date format. Meal date should be in YYYY-MM-DD',
                'صيغة تاريخ الوجبات غير صحيحة. يرجى استخدام صيغة YYYY-MM-DD.'
            ])
        try:
            subscription = request.env['diet.subscription.order'].sudo().browse(int(kwargs['subscription_id']))
            if subscription.state != 'in_progress':
                return self.make_response(False, 400, [], None,'Subscription not active.')
            calendar_day = request.env['customer.meal.calendar'].sudo().search([
                ('so_id','=',subscription.id),
                ('date','=',meal_date)
            ])
            meal_categories = subscription.meal_count_ids.mapped('meal_category_id')
            meal_data = []
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            for meal_category in meal_categories:
                meal = calendar_day.filtered(lambda mline: mline.meal_category_id == meal_category)
                meal_data.append({
                    'meal_category_id': meal_category.id,
                    'meal_category_name': meal_category.name if meal_category.name else '',
                    'meal_category_arabic_name': meal_category.arabic_name if meal_category.arabic_name else '',
                    'meal_id': meal.meal_id.id if meal.meal_id else 0,
                    'tags': ', '.join(meal.meal_tag_id.mapped('name')) if meal.meal_tag_id else '',
                    'meal_name': meal.meal_id.name if meal.meal_id.name else '',
                    'meal_arabic_name': meal.meal_id.arabic_name if meal.meal_id.arabic_name else '',
                    'description': meal.meal_id.meal_description if meal.meal_id.meal_description else '',
                    'description_arabic': meal.meal_id.arabic_meal_description if meal.meal_id.arabic_meal_description else '',
                    'image': f'{base_url}/web/image?model=product.template&id={meal.meal_id.id}&field=image_1920' if meal.meal_id.image_1920 else '',
                    'protein': meal.meal_id.protein if meal.meal_id.protein else 0.0,
                    'carbohydrates': meal.meal_id.carbohydrates if meal.meal_id.carbohydrates else 0.0,
                    'fat': meal.meal_id.fat if meal.meal_id.fat else 0.0,
                    'calories': meal.meal_id.calories if meal.meal_id.calories else 0.0,
                    "rating": meal.meal_id.rating if meal.meal_id.rating else 0,
                    "rating_count": meal.meal_id.rating_count if meal.meal_id.rating_count else 0
                })
            return self.make_response(True, 200, [],meal_data, [])
        except:
            return self.make_response(False, 400, [], None, [
                f'No subscription found with ID {kwargs["subscription_id"]}.',
                f'No subscription found with ID {kwargs["subscription_id"]}.'
            ])
        
    @validate_token
    @http.route('/verify_coupon', type='http', auth='public', methods=['GET'], csrf=False)
    def verify_coupon(self, **kwargs):
        if not kwargs.get('plan_choice_id', False):
            return self.make_response(False, 400, [], None, [
                'Plan ID not passed.',    
                'يرجى إدخال ID  النظام المطلوبة.' 
            ])   
        if not kwargs.get('coupon_code', False):
            return self.make_response(False, 400, [], None, [
                'Coupon code not passed.',
                'يرجى إدخال رمز الخصم.'
            ])
        try:
            plan = request.env['plan.choice'].sudo().browse(int(kwargs['plan_choice_id']))
        except:
            return self.make_response(False, 400, [], None, [
                f'No plan choice found with ID {kwargs["plan_choice_id"]}.',
                f'No plan choice found with ID {kwargs["plan_choice_id"]}.'
            ])
        try:
            total = plan.plan_price
            company = request.env.company
            default_tax = company.sudo().account_sale_tax_id
            discount = 0
            if default_tax:
                tax_obj = default_tax.compute_all(total)
                total = tax_obj['total_excluded']
                tax_amount = sum([tax['amount'] for tax in tax_obj['taxes']])
                grand_total = tax_obj['total_included']
            else:
                total = total
                tax_amount = 0.0
                grand_total = total
            is_applied = False
            coupon_code = kwargs['coupon_code']
            if ' ' in coupon_code:
                coupon_code = coupon_code.replace(' ', '')
            promo_id = request.env['coupon.program'].search([('program_name','=',coupon_code),('state', '=', 'active')])
            if not promo_id:
                coupon_code = coupon_code.upper()
                promo_id = request.env['coupon.program'].search([('program_name','=',coupon_code),('state', '=', 'active')])
            if not promo_id:
                coupon_code = coupon_code.lower()
                promo_id = request.env['coupon.program'].search([('program_name','=',coupon_code),('state', '=', 'active')])
            if not promo_id:
                expired_promo_id = request.env['coupon.program'].search([('program_name','=',coupon_code),('state', '=', 'expired')])
                if not expired_promo_id:
                    coupon_code = coupon_code.upper()
                    expired_promo_id = request.env['coupon.program'].search([('program_name','=',coupon_code),('state', '=', 'expired')])
                if not expired_promo_id:
                    coupon_code = coupon_code.lower()
                    expired_promo_id = request.env['coupon.program'].search([('program_name','=',coupon_code),('state', '=', 'expired')])
                if expired_promo_id:
                    return self.make_response(False, 400, [], [{
                        'total': round(total if total else 0.0, 2),
                        'tax': round(tax_amount if tax_amount else 0.0, 2),
                        'discount': round(discount if discount else 0.0, 2),
                        'grand_total': round(grand_total if grand_total else 0.0, 2)
                    }], [
                        'Coupon expired.',
                        'انتهت صلاحية القسيمة'
                    ])
            if not promo_id:
                return self.make_response(False, 400, [], [{
                        'total': round(total if total else 0.0, 2),
                        'tax': round(tax_amount if tax_amount else 0.0, 2),
                        'discount': round(discount if discount else 0.0, 2),
                        'grand_total': round(grand_total if grand_total else 0.0, 2)
                    }], [
                    'Invalid coupon code.',
                    'رمز الخصم غير صالح.'
                ])
            if promo_id and not promo_id.no_partner_limit and kwargs.get('mobile', False):
                partner_id = request.env['res.partner'].sudo().search([('phone','=',kwargs['mobile'])])
                if partner_id:
                    is_applied = promo_id.participation_ids.filtered(lambda x: x.customer_id == partner_id)
                if is_applied:
                    return self.make_response(False, 400, [], [{
                        'total': round(total if total else 0.0, 2),
                        'tax': round(tax_amount if tax_amount else 0.0, 2),
                        'discount': round(discount if discount else 0.0, 2),
                        'grand_total': round(grand_total if grand_total else 0.0, 2)
                    }], [
                        'Coupon usage exceeded.',
                        'تم تجاوز الحد الأقصى لاستخدام القسيمة.'
                    ])
            if promo_id and promo_id.promocode_used >= promo_id.coupon_count:
                return self.make_response(False, 400, [], [{
                        'total': round(total if total else 0.0, 2),
                        'tax': round(tax_amount if tax_amount else 0.0, 2),
                        'discount': round(discount if discount else 0.0, 2),
                        'grand_total': round(grand_total if grand_total else 0.0, 2)
                }], [
                    'Coupon usage exceeded.',
                    'تم تجاوز الحد الأقصى لاستخدام القسيمة.'
                ])
            if promo_id and not promo_id.is_universal_code:
                applicable_plan_line = promo_id.plan_applicable_ids.filtered(lambda app_line: plan in app_line.appl_choice_ids)
                if not applicable_plan_line:
                    return self.make_response(False, 400, [], [{
                        'total': round(total if total else 0.0, 2),
                        'tax': round(tax_amount if tax_amount else 0.0, 2),
                        'discount': round(discount if discount else 0.0, 2),
                        'grand_total': round(grand_total if grand_total else 0.0, 2)
                    }], [
                        'Promocode not applicable for the selected plan and choice.',
                        'لا ينطبق الرمز الترويجي على الخطة والاختيار المحددين'
                    ])
            current_day = datetime.today().strftime('%A')
            count = 0
            if promo_id.program_availability == 'custom':
                if promo_id.sunday and current_day == 'Sunday':
                    count += 1
                elif promo_id.monday and current_day == 'Monday':
                    count += 1
                elif promo_id.tuesday and current_day == 'Tuesday':
                    count += 1
                elif promo_id.wednesday and current_day == 'Wednesday':
                    count += 1
                elif promo_id.thursday and current_day == 'Thursday':
                    count += 1
                elif promo_id.friday and current_day == 'Friday':
                    count += 1
                elif promo_id.saturday and current_day == 'Saturday':
                    count += 1
                else:
                    return self.make_response(False, 400, [], [{
                        'total': round(total if total else 0.0, 2),
                        'tax': round(tax_amount if tax_amount else 0.0, 2),
                        'discount': round(discount if discount else 0.0, 2),
                        'grand_total': round(grand_total if grand_total else 0.0, 2)
                    }], [
                        'This Promo Code is not available today',
                        'رمز العرض غير متاح اليوم.'
                    ])
            total = plan.plan_price
            company = request.env.company
            default_tax = company.sudo().account_sale_tax_id
            if default_tax:
                tax_obj = default_tax.compute_all(total)
                total = tax_obj['total_excluded']
                tax_amount = sum([tax['amount'] for tax in tax_obj['taxes']])
                grand_total = tax_obj['total_included']
            else:
                total = total
                tax_amount = 0.0
                grand_total = total
            if not promo_id.is_universal_code:
                applicable_plan_line = promo_id.plan_applicable_ids.filtered(lambda app_line: plan in app_line.appl_choice_ids)
                if applicable_plan_line.discount_type == 'percentage':
                    discount_percentage = applicable_plan_line.program_discount
                    discount = grand_total * discount_percentage / 100
                else:
                    discount = applicable_plan_line.program_discount
            else:
                if promo_id.discount_type == 'percentage':
                    discount = grand_total * promo_id.program_discount / 100
                else:
                    discount = promo_id.program_discount
                
            if grand_total < discount:
                return self.make_response(False, 400, [], [{
                        'total': round(total if total else 0.0, 2),
                        'tax': round(tax_amount if tax_amount else 0.0, 2),
                        'discount': round(discount if discount else 0.0, 2),
                        'grand_total': round(grand_total if grand_total else 0.0, 2)
                    }], [
                    'Not Applicable on this subscription',
                    'لا يمكن استخدام رمز العرض مع هذا الاشتراك.'
                ])
            grand_total -= discount

            return self.make_response(True, 200, [], [{
                'total': round(total if total else 0.0, 2),
                'tax': round(tax_amount if tax_amount else 0.0, 2),
                'discount': round(discount if discount else 0.0, 2),
                'grand_total': round(grand_total if grand_total else 0.0, 2)
            }], [])
        
        except:
            return self.make_response(False, 400, [], None, [
                'Invalid coupon code.',
                'رمز الخصم غير صالح.'
            ])
        
    @validate_token
    @http.route('/activate_subscription', type='http', auth='public', methods=['POST'], csrf=False)
    def activate_subscription(self, **kwargs):
        kwargs = request.get_json_data()
        if not kwargs.get('subscription_id', False):
            return self.make_response(False, 400, [], None,[
                'Subscription ID not passed.',        
                'يرجى إدخال ID الاشتراك.'
            ])
        try:
            subscription = request.env['diet.subscription.order'].sudo().browse(int(kwargs['subscription_id']))
            if subscription.state == 'paid':
                subscription.activate_subscription()
                subscription.message_post(body=f"Subscription activated from customer app.")
            elif subscription.state == 'in_progress':
                return self.make_response(False, 400, [], None, [
                    'Subscription already active.',
                    'Subscription already active.'
                ])
            return self.make_response(True, 200, [
                'Subscription activated.',
                'Subscription activated.'
            ] ,None, [])
        except:
            return self.make_response(False, 400, [], None, [
                f'No subscription found with ID {kwargs["subscription_id"]}.',
                f'No subscription found with ID {kwargs["subscription_id"]}.'
            ])

    @validate_token
    @http.route('/submit_meal_rating', type='http', auth='public', methods=['POST'], csrf=False)
    def submit_meal_rating(self, **kwargs):
        kwargs = request.get_json_data()
        if not kwargs.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone','=',kwargs['mobile'])
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {kwargs['mobile']} not found.",
                f"Customer with mobile {kwargs['mobile']} not found."
            ])
        if not kwargs.get('meal_id', False):
            return self.make_response(False, 400, [], None, [
                'Meal not passed.',
                'يرجى إدخال بيانات الوجبة'
            ])
        meal = request.env['product.template'].sudo().browse(int(kwargs['meal_id']))
        if not meal:
            return self.make_response(False, 400, [], None, [
                f"Meal with ID {kwargs['meal_id']} not found.",        
                f"الوجبة المطلوبة غير متوفرة. {kwargs['meal_id']}"
            ])
        if not kwargs.get('rating', False):
            return self.make_response(False, 400, [], None, [
                'Rating not passed.',
                'يرجى إدخال تقييم.'
            ])
        rating = int(kwargs['rating'])
        if rating not in [0,1,2,3,4,5]:
            return self.make_response(False, 400, [], None, [
                f'Rating should be between 0 and 5 stars. Passed value is {rating}.',
                f'يجب أن يكون التقييم بين 0 و5 نجوم. {rating}.'
            ])
        try:
            customer_rating_exists = request.env['meal.customer.rating'].sudo().search([
                ('partner_id','=',customer.id),
                ('meal_id','=',meal.id)
            ])
            if customer_rating_exists:
                customer_rating_exists.rating = str(rating)
                meal.message_post(body=f"Rating updated by {customer.name} from customer app. Rating: {rating}")
                customer.message_post(body=f"Rating updated for {meal.name} from customer app. Rating: {rating}")
            else:
                request.env['meal.customer.rating'].sudo().create({
                    "partner_id": customer.id,
                    "meal_id": meal.id,
                    "rating": str(rating)
                })
                meal.message_post(body=f"Rating submitted by {customer.name} from customer app. Rating: {rating}")
                customer.message_post(body=f"Rating submitted for {meal.name} from customer app. Rating: {rating}")
            return self.make_response(True, 200, [
                'Rating submitted successfully.',
                'Rating submitted successfully.'
            ], None, [])
        except Exception as e:
            return self.make_response(False, 500, [], None, [
                'Internal Error',
                'حدث خطأ داخلي.'
            ])

    @validate_token
    @http.route('/set_date_meal', type='http', auth='public', methods=['POST'], csrf=False)
    def set_date_meal(self, **kwargs):
        kwargs = request.get_json_data()
        try:
            required_vals = ['subscription_id', 'date', 'meal_category_id', 'meal_id']
            vals_not_passed = [input_key for input_key in required_vals if (input_key not in kwargs.keys()) or (not kwargs.get(input_key, False)) ]
            if vals_not_passed:
                return self.make_response(False, 400, [], None, [
                    f'Required values not given ({", ".join(vals_not_passed)}).',
                    f'البيانات المطلوبة غير مكتملة. ({", ".join(vals_not_passed)}).'
                ])
            subscription = request.env['diet.subscription.order'].sudo().browse(kwargs.get('subscription_id'))
            meal_category = request.env['meals.category'].sudo().search([('id', '=', kwargs.get('meal_category_id'))])
            meal = request.env['product.template'].sudo().search([('id', '=', kwargs.get('meal_id'))], limit=1)
            subs_date = datetime.strptime(kwargs.get('date'), '%Y-%m-%d').date()
            today_date = fields.Date.today()
            if subs_date < today_date:
                return self.make_response(False, 400, [], None, [
                    'Already delivered meals cannot be edited.',
                    'لا يمكن تعديل الوجبات التي تم توصيلها.'
                ])
            date_difference = subs_date - today_date
            if date_difference.days <= 2:
                return self.make_response(False, 400, [], None, [
                    'You cannot change the meals for the selected date as meal preparation started.',
                    'لا يمكن تغيير الوجبات بعد بدء التحضير.'
                ])
            meal_calendar_entry = request.env['customer.meal.calendar'].sudo().search([
                ('so_id', '=', subscription.id),
                ('meal_category_id', '=', meal_category.id),
                ('date', '=', subs_date)
            ], limit=1)
            if not meal_calendar_entry:
                return self.make_response(False, 400, [], None, [
                    'No entry with the given combination of subscription, date, meal category, meal found.',
                    'No entry with the given combination of subscription, date, meal category, meal found.'
                ])
            previous_meal = meal_calendar_entry.meal_id.name if meal_calendar_entry.meal_id else 'No meal applied'
            meal_calendar_entry.sudo().update({'meal_id': meal.id,'state': 'active_with_meal'})
            subscription.message_post(body=f"Meal updated for {meal_category.name} on {subs_date.strftime('%Y-%m-%d')} from customer app. Previous meal: {previous_meal}. New meal: {meal.name}")
            consumed_calories = meal_calendar_entry.total_calories
            calorie_status = meal_calendar_entry.calorie_status

            payload = {
                "consumed_calories": consumed_calories,
                "status": calorie_status
            }
            return self.make_response(True, 200, [
                'Meal updated successfully',
                'تم تحديث الوجبة بنجاح.'
            ], payload, [])
        except Exception as e:
            return self.make_response(False, 500, [], None, [
                'Internal Error',
                'حدث خطأ داخلي.'
            ])

    @validate_token
    @http.route('/dietitian_appointment', type='http', auth='public', methods=['POST'], csrf=False)
    def create_dietitian_history(self, **kwargs):
        kwargs = request.get_json_data()
        if not kwargs or not kwargs.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone', '=',kwargs['mobile'])
        ],limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {kwargs['mobile']} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم. {kwargs['mobile']}"
            ])
        appointment_id = request.env['dietitian.appointment.history'].sudo().create({
            'customer_id': customer.id, 
            'note': 'Dietition Appoinment Requested.',
            'date': fields.Date.today()
        })
        if appointment_id:
            appointment_id.message_post(body=f"Dietitian appoinment requested from customer app.")
            customer.message_post(body=f"Dietitian appoinment requested from customer app.")
        return self.make_response(True, 200, [
            "Dietitian appoinment requested.",
            "تم طلب موعد مع أخصائي التغذية."
        ], None, [])

    @validate_token
    @http.route('/notification/<mobile>', type='http', auth='public', methods=['GET'], csrf=False)
    def notification(self, mobile):
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Customer ID not passed.",
                "يرجى إدخال ID العميل."
            ])
        find_customer_query = f"SELECT id FROM res_partner WHERE phone = '{mobile}'"
        request.env.cr.execute(find_customer_query)
        customer = request.env.cr.dictfetchall()
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} not found.",
                f"Customer with mobile {mobile} not found."
            ])
        customer = customer[0]['id']
        date_today = fields.Date.today().strftime('%Y-%m-%d')
        date_today_start = f"{date_today} 00:00:00"
        date_today_end = f"{date_today} 23:59:59"
        find_customer_notifications_query = f"""
            SELECT notification_id, title, message, message_send_datetime
            FROM customer_notification_line
            WHERE customer_id = {customer} AND message_send_datetime BETWEEN '{date_today_start}' AND '{date_today_end}'
        """
        request.env.cr.execute(find_customer_notifications_query)
        customer_notification = request.env.cr.dictfetchall()
        customer_notifications = []
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for result in customer_notification:
            customer_notifications.append({
                'datetime': result['message_send_datetime'].strftime('%Y-%m-%d %H:%M:%S'), 
                'title': result['title'],
                'message': result['message'],
                'image': f'{base_url}/web/image?model=customer.notification&id={result["notification_id"]}&field=image' if result['notification_id'] else '',
            })
        return request.make_response(json.dumps({
            "statusOk": True,
            "statusCode": 200,
            "message": [],
            "payload": customer_notifications,
            "error": []
        }), headers=[('Content-Type', 'application/json')])
    
    @validate_token
    @http.route('/support', type='http', auth="public", methods=['GET'], csrf=False)
    def get_customer_support(self, **data_passed):
        support_number = request.env['ir.config_parameter'].sudo().get_param('diet.customer_support_number')
        if support_number:
            return self.make_response(True, 200, [], support_number, [])
        else:
            return self.make_response(False, 400, [], None, [
                "Customer care number not found.",
                "رقم خدمة العملاء غير متوفر."
            ])
        
        
    @validate_token
    @http.route('/device_token', type='http', auth='public', methods=['POST'], csrf=False)
    def device_token(self):
        data = request.get_json_data()
        mobile = data.get('mobile', False)
        device_token = data.get('device_token', False)
        error = ""
        data_not_passed = []
        if not mobile:
            data_not_passed.append("Mobile")
        if not device_token:
            data_not_passed.append("Device Token")
        if data_not_passed:
            return self.make_response(False, 400, [], [], [
                f"{', '.join(data_not_passed)} not given.",
                f"{', '.join(data_not_passed)} not given."
            ])
        get_customer_query = f"""SELECT id FROM res_partner WHERE phone='{mobile}'"""
        request.env.cr.execute(get_customer_query)
        customer = request.env.cr.dictfetchone()
        if not customer:
            return self.make_response(False, 400, [], [], [
                f"Customer with mobile {mobile} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم."
            ])
        else:
            existing_token = request.env['customer.device.token'].search([
                ('partner_id', '=', customer['id']),
                ('device_token', '=', device_token)
            ])
            if not existing_token:
                request.env['customer.device.token'].create({
                    "partner_id": customer['id'],
                    "device_token": device_token
                })
            return self.make_response(True, 200, [], [], [])

    @validate_token
    @http.route('/remove_device_token', type='http', auth='public', methods=['POST'], csrf=False)
    def remove_device_token(self):
        data = request.get_json_data()
        device_token = data.get('device_token', False)
        if not device_token:
            return self.make_response(False, 400, [], [], [
                "Device Token not given.",
                "يرجى إدخال رمز الجهاز."
            ])
        check_token_exists_query = f"""SELECT id FROM customer_device_token WHERE device_token='{device_token}'"""
        request.env.cr.execute(check_token_exists_query)
        token_exists = request.env.cr.dictfetchone()
        if not token_exists:
            return self.make_response(False, 400, [], [], [
                "Device Token doesn't exist.",
                "رمز الجهاز المدخل غير موجود."
            ])
        else:
            request.env['customer.device.token'].browse(token_exists['id']).unlink()
            return self.make_response(True, 200, [], [], [])


    @validate_token
    @http.route('/referral_code', type='http', auth='public', methods=['GET'], csrf=False)
    def referral_code(self, mobile):
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile not passed.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone', '=', mobile)
        ], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم."
            ])
        cvals = {
            "referral_code": customer.referral_code,
            "referral_earnings": 0
        }
        return self.make_response(True, 200, [], [cvals], [])
    
    @validate_token
    @http.route('/share_referral_code', type='http', auth='public', methods=['GET'], csrf=False)
    def share_referral_code(self, mobile):
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile not passed.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone', '=', mobile)
        ], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم."
            ])
        cvals = {
            "message": f"Share Your health journey with friends! Invite them to join FEED family using your referral code {customer.referral_code}  and earn rewards. Let's spread wellness"
        }
        return self.make_response(True, 200,[], [cvals], [])
    
    @validate_token
    @http.route('/special_offer', type='http', auth='public', methods=['GET'], csrf=False)
    def get_special_offers_confirm(self, **kwargs):
        special_offers = request.env['special.offer'].sudo().search([('state', '=', 'confirm')])
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        special_offers_data = [{
            "title": offer.title or "",
            "description": offer.description or "",
            "image": f'{base_url}/web/image?model=special.offer&id={offer.id}&field=image' if offer.image else "",
        } for offer in special_offers]

        if special_offers_data:
            return self.make_response(True, 200, [
                "Special offers  fetched successfully",
                "تم تحميل العروض الخاصة بنجاح."
            ], special_offers_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No special offers found",
                "لا توجد عروض حاليًا."
            ])

    @validate_token
    @http.route('/driver/login', type='http', auth='public', methods=['GET'], csrf=False)
    def driver_login(self, **kwargs):
        mobile = kwargs.get('mobile', False)
        password = kwargs.get('password', False)
        if not mobile or not password:
            return self.make_response(False, 400, [], None, [
                "Invalid Credentials",
                "بيانات الدخول غير صحيحة."
            ])
        if mobile[0:4] == '+966' or mobile[0:4] == ' 965':
            mobile = mobile[4:]
        driver_query = f"""SELECT driver_app_password as password FROM area_driver WHERE active=True and phone='{mobile}' or phone='+966{mobile}'"""
        request.env.cr.execute(driver_query)
        driver = request.env.cr.dictfetchone()
        if not driver:
            return self.make_response(False, 400, [], None, [
                f"Driver with mobile {mobile} doesn't exist.",
                f"السائق المطلوب غير موجود. {mobile}"
            ])
        if password == driver.get('password'):
            return self.make_response(True, 200, [
                "Login Successful",
                "تم تسجيل الدخول بنجاح."
            ], None, [])
        else:
            return self.make_response(False, 400, [], None, [
                "Incorrect Password",
                "كلمة المرور المدخلة غير صحيحة."
            ])
        
    @validate_token
    @http.route('/driver/reset_password', type='http', auth='public', methods=['PATCH'], csrf=False)
    def driver_reset_password(self, **kwargs):
        json_body = request.get_json_data()
        mobile = json_body.get('mobile', False)
        new_password = json_body.get('new_password', False)        
        if not mobile or not new_password:
            return self.make_response(False, 400, [], None, [
                "Mobile/Password not supplied.",
                "يرجى إدخال رقم الجوال وكلمة المرور."
            ])
        driver_query = f"""SELECT id FROM area_driver WHERE phone='{mobile}' or phone='+966{mobile}'"""
        request.env.cr.execute(driver_query)
        driver = request.env.cr.dictfetchone()
        if not driver:
            return self.make_response(False, 400, [], None, [
                f"Driver with mobile {mobile} doesn't exist.",
                f"السائق المطلوب غير موجود. {mobile}"
            ])
        driver_id = driver.get('id')
        if isinstance(driver_id, str):
            driver_id = int(driver_id)
        try:
            update_password_query = f"""UPDATE area_driver SET driver_app_password='{new_password}' WHERE id={driver_id}"""
            driver = request.env['area.driver'].sudo().browse(driver_id)
            driver.message_post(body=f"Password reset from driver app.")
            request.env.cr.execute(update_password_query)
            return self.make_response(True, 200, [], None, [])
        except Exception as e:
            return self.make_response(False, 400, [], None, [
                "Password reset failed.",
                "فشل في إعادة تعيين كلمة المرور."
            ])
        
    @validate_token
    @http.route('/driver/homescreen', type='http', auth='public', methods=['GET'], csrf=False)
    def driver_homescreen(self, **kwargs):
        mobile = kwargs.get('mobile')
        if not mobile:
            return self.make_response(False, 400, [], [], [
                "Driver mobile not given.",
                "Driver mobile not given."
            ])
        driver_query = f"""SELECT id, name, code FROM area_driver WHERE phone='{mobile}' or phone='+966{mobile}'"""
        request.env.cr.execute(driver_query)
        driver = request.env.cr.dictfetchone()
        if not driver:
            return self.make_response(False, 400, [], [], [
                f"Driver with mobile {mobile} doesn't exist.",
                f"السائق المطلوب غير موجود. {mobile}"
            ])
        payload = []
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        driver_orders = request.env['driver.order'].sudo().search([('date','=',fields.Date.today()), ('driver_id','=',driver.get('id'))])
        delivered = driver_orders.filtered(lambda order: order.status=='delivered')
        pending = driver_orders.filtered(lambda order: order.status=='pending')
        shift_data = []
        shift_ids = request.env['customer.shift'].sudo().search([])
        for shift in shift_ids:
            shift_data.append({
                'id': shift.id,
                "name": shift.shift,
                "arabic_name": shift.arabic_name
            })
        driver_record = request.env['area.driver'].sudo().browse(driver.get('id'))
        driver_profile_picture = f"{base_url}/web/image?model=area.driver&id={driver.get('id')}&field=image" if driver_record.image else ""
        homescreen_data = {
            'name': driver.get('name', ''),
            'code': driver.get('code', ''),
            'image': driver_profile_picture,
            'total_orders': len(driver_orders),
            'delivered_orders': len(delivered),
            'pending_orders': len(pending),
            'shifts': shift_data
        }
        payload.append(homescreen_data)
        if payload:
            return self.make_response(True, 200, [], payload, [])
        else:
            return self.make_response(False, 400, [], [], [
                "No data found",
                "No data found"
            ])
        
    @validate_token
    @http.route('/driver/orders', type='http', auth='public', methods=['GET'], csrf=False)
    def driver_orders(self, **kwargs):
        mobile = kwargs.get('mobile')
        order_date = kwargs.get('date', False)
        shift_id = kwargs.get('shift_id')
        if not mobile:
            return self.make_response(False, 400, [], [], [
                "Driver mobile not given.",
                "Driver mobile not given."
            ])
        driver_query = f"""SELECT id, name, code FROM area_driver WHERE phone='{mobile}' or phone='+966{mobile}'"""
        request.env.cr.execute(driver_query)
        driver = request.env.cr.dictfetchone()
        if not driver:
            return self.make_response(False, 400, [], [], [
                f"Driver with mobile {mobile} doesn't exist.",
                f"السائق المطلوب غير موجود. {mobile}"
            ])
        payload = []
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        domain = [
            ('driver_id','=',driver.get('id'))
        ]
        if order_date:
            order_date = datetime.strptime(order_date, '%Y-%m-%d').date()
            order_date_day = order_date.strftime('%A').lower()
            if order_date_day == 'thursday':
                domain += [('date', '>=', order_date),('date', '<=', order_date + timedelta(days=1))]
            else:
                domain.append(('date', '=', order_date))
        if shift_id:
            domain.append(('shift_id', '=', int(shift_id)))
        driver_orders = request.env['driver.order'].sudo().search(domain, order='delivery_queue_number')
        for order in driver_orders:
            customer_phone = order.customer_id.phone if order.customer_id.phone else False
            if customer_phone and len(customer_phone) == 8:
                customer_phone = f"+966{customer_phone}"
            customer_image = f"{base_url}/web/image?model=res.partner&id={order.customer_id.id}&field=image_1920" if order.customer_id.image_1920 else ""
            map_link = ""
            if order.address_id.partner_latitude and order.address_id.partner_longitude:
                map_link = f"https://www.google.com/maps?q={order.address_id.partner_latitude},{order.address_id.partner_longitude}"
            order_list_data = {
                'queue_no': order.delivery_queue_number,
                'id': order.id,
                'image': customer_image,
                'name': f'{order.customer_id.name} {order.customer_id.last_name}',
                'customer_id': order.customer_id.customer_sequence_no,
                'arabic_name': f'{order.customer_id.arabic_name} {order.customer_id.last_name_arabic}',
                'street': order.street_id.name if order.street_id else '',
                'area': order.district_id.name if order.district_id else '',
                'area_arabic': order.district_id.arabic_name if order.district_id else '',
                'zone_id':order.zone_id.name if order.zone_id else '',
                'jedha': order.jedha if order.jedha else '',
                'house_number': order.house_number if order.house_number else '',
                'floor_number': order.floor_number if order.floor_number else '',
                'customer_comments': order.comments if order.comments else '',
                'phone': customer_phone,
                'status': order.status,
                'map_link': map_link
            }
            payload.append(order_list_data)
        if payload:
            return self.make_response(True, 200, [], payload, [])
        else:
            return self.make_response(False, 400, [], [], [
                "No orders found",
                "لا توجد طلبات مسجلة."
            ])
        
    @validate_token
    @http.route('/driver/order', type='http', auth='public', methods=['GET'], csrf=False)
    def driver_order(self, **kwargs):
        order_id = kwargs.get('order_id')
        payload = []
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        driver_orders = request.env['driver.order'].sudo().search([
            ('id','=',int(order_id))
        ])
        for order in driver_orders:
            customer_phone = order.customer_id.phone if order.customer_id.phone else False
            if customer_phone and len(customer_phone) == 8:
                customer_phone = f"+966{customer_phone}"
            customer_image = f"{base_url}/web/image?model=res.partner&id={order.customer_id.id}&field=image_1920" if order.customer_id.image_1920 else ""
            map_link = None
            if order.customer_id.partner_latitude and order.customer_id.partner_longitude:
                map_link = f"https://www.google.com/maps?q={order.customer_id.partner_latitude},{order.customer_id.partner_longitude}"
            order_list_data = {
                'queue_no': order.delivery_queue_number,
                'id': order.id,
                'image': customer_image,
                'name': f'{order.customer_id.name} {order.customer_id.last_name}',
                'customer_id': order.customer_id.customer_sequence_no,
                'arabic_name': f'{order.customer_id.arabic_name} {order.customer_id.last_name_arabic}',
                'street': order.street_id.name if order.street_id else '',
                'zone_id':order.zone_id.name if order.zone_id else '',
                'area': order.district_id.name if order.district_id else '',
                'area_arabic': order.district_id.arabic_name if order.district_id else '',
                'jedha': order.jedha if order.jedha else '',
                'house_number': order.house_number if order.house_number else '',
                'floor_number': order.floor_number if order.floor_number else '',
                'customer_comments': order.comments if order.comments else '',
                'phone': customer_phone,
                'status': order.status,
                'map_link': map_link
            }
            payload.append(order_list_data)
        if payload:
            return self.make_response(True, 200, [], payload, [])
        else:
            return self.make_response(False, 400, [], [], [
                "Order not found",
                "لم يتم العثور على الطلب المطلوب."
            ])
        
    @validate_token
    @http.route('/driver/delivered', type='http', auth='public', methods=['PATCH'], csrf=False)
    def driver_delivered(self, **kwargs):
        order_id = kwargs.get('order_id')
        comments = kwargs.get('comments')
        driver_order = request.env['driver.order'].sudo().search([
            ('id','=',int(order_id))
        ])
    
        if driver_order:
            driver_order.status = 'delivered'
            for calendar in driver_order.meal_calendar_ids:
                calendar.delivery_status = 'delivered'
            driver_order.driver_comments = comments
            driver_order.message_post(body=f"Order delivered by driver")
            return self.make_response(True, 200, [], [], [])
        else:
            return self.make_response(False, 400, [], [], [
                "Order not found",
                "لم يتم العثور على الطلب المطلوب."
            ])
        
    @validate_token
    @http.route('/driver/not_delivered', type='http', auth='public', methods=['PATCH'], csrf=False)
    def driver_not_delivered(self, **kwargs):
        order_id = kwargs.get('order_id')
        comments = kwargs.get('comments')
        driver_order = request.env['driver.order'].sudo().search([
            ('id','=',int(order_id))
        ])
    
        if driver_order:
            driver_order.status = 'not_delivered'
            for calendar in driver_order.meal_calendar_ids:
                calendar.delivery_status = 'not_delivered'
            driver_order.driver_comments = comments
            driver_order.message_post(body=f"Order not delivered by driver")
            return self.make_response(True, 200, [], [], [])
        else:
            return self.make_response(False, 400, [], [], [
                "Order not found",
                "لم يتم العثور على الطلب المطلوب."
            ])
        
    @validate_token
    @http.route('/driver/comments', type='http', auth='public', methods=['PATCH'], csrf=False)
    def driver_comments(self, **kwargs):
        order_id = kwargs.get('order_id')
        comments = kwargs.get('comments')
        driver_order = request.env['driver.order'].sudo().search([
            ('id','=',int(order_id))
        ])
    
        if driver_order:
            driver_order.driver_comments = comments
            return self.make_response(True, 200, [], [], [])
        else:
            return self.make_response(False, 400, [], [], [
                "Order not found",
                "لم يتم العثور على الطلب المطلوب."
            ])

    @validate_token
    @http.route('/driver', type='http', auth='public', methods=['GET'], csrf=False)
    def driver_profile(self, **kwargs):
        mobile = kwargs.get('mobile')
        if not mobile:
            return self.make_response(False, 400, [], [], [
                "Driver mobile not given.",
                "Driver mobile not given."
            ])
        driver_query = f"""SELECT id, name, code, phone, email FROM area_driver WHERE phone='{mobile}' or phone='+966{mobile}'"""
        request.env.cr.execute(driver_query)
        driver = request.env.cr.dictfetchone()
        if not driver:
            return self.make_response(False, 400, [], [], [
                f"Driver with mobile {mobile} doesn't exist.",
                f"السائق المطلوب غير موجود. {mobile}"
            ])
        payload = []
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        profile_data = {
            'name': driver.get('name', '') if driver.get('name') else '',
            'code': driver.get('code', '') if driver.get('code') else '',
            'image': f"{base_url}/web/image?model=area.driver&id={driver.get('id')}&field=image",
            'mobile': driver.get('phone', '') if driver.get('phone') else '',
            'email': driver.get('email', '') if driver.get('email') else ''
        }
        payload.append(profile_data)
        if payload:
            return self.make_response(True, 200, [], payload, [])
        else:
            return self.make_response(False, 400, [], [], [
                "No data found",
                "No data found"
            ])
        
    @validate_token
    @http.route('/driver/device_token', type='http', auth='public', methods=['POST'], csrf=False)
    def driver_device_token(self):
        data = request.get_json_data()
        mobile = data.get('mobile', False)
        device_token = data.get('device_token', False)
        error = ""
        data_not_passed = []
        if not mobile:
            data_not_passed.append("Mobile")
        if not device_token:
            data_not_passed.append("Device Token")
        if data_not_passed:
            return self.make_response(False, 400, [], [], [
                f"{', '.join(data_not_passed)} not given.",
                f"{', '.join(data_not_passed)} not given."
            ])
        get_driver_query = f"""SELECT id FROM area_driver WHERE phone='{mobile}' or phone='+966{mobile}'"""
        request.env.cr.execute(get_driver_query)
        driver = request.env.cr.dictfetchone()
        if not driver:
            return self.make_response(False, 400, [], [], [
                f"Driver with mobile {mobile} doesn't exist.",
                f"السائق المطلوب غير موجود. {mobile}"
            ])
        else:
            existing_token = request.env['driver.device.token'].search([
                ('driver_id', '=', driver['id']),
                ('device_token', '=', device_token)
            ])
            if not existing_token:
                request.env['driver.device.token'].create({
                    "driver_id": driver['id'],
                    "device_token": device_token
                })
            return self.make_response(True, 200, [], [], [])

    @validate_token
    @http.route('/driver/notifications/<mobile>', type='http', auth='public', methods=['GET'], csrf=False)
    def notification_driver(self, mobile):
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Driver mobile not passed.",
                "Driver mobile not passed."
            ])
        find_driver_query = f"SELECT id FROM area_driver WHERE phone='{mobile}' or phone='+966{mobile}'"
        request.env.cr.execute(find_driver_query)
        driver = request.env.cr.dictfetchall()
        if not driver:
            return self.make_response(False, 400, [], None, [
                f"Driver with mobile {mobile} not found.",
                f"السائق المطلوب غير موجود. {mobile}"
            ])
        driver = driver[0]['id']
        date_today = fields.Date.today().strftime('%Y-%m-%d')
        find_driver_notifications_query = f"""
            SELECT id, title, message, message_send_datetime
            FROM driver_notification_line
            WHERE driver_id = {driver} AND DATE(message_send_datetime) = '{date_today}'
        """
        request.env.cr.execute(find_driver_notifications_query)
        driver_notifications = []
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for result in request.env.cr.dictfetchall():
            driver_notifications.append({
                'datetime': result['message_send_datetime'].strftime('%Y-%m-%d %H:%M:%S'), 
                'title': result['title'],
                'message': result['message'],
                'image': f'{base_url}/web/image/ir.attachment/{result["id"]}/datas' if result['id'] else '',
            })
        return request.make_response(json.dumps({
            "statusOk": True,
            "statusCode": 200,
            "message": [],
            "payload": driver_notifications,
            "error": []
        }), headers=[('Content-Type', 'application/json')])

    @validate_token
    @http.route('/show_shop', type='http', auth='public', methods=['GET'], csrf=False)
    def driver_comments(self, **kwargs):
        show_shop = request.env['ir.config_parameter'].sudo().get_param('diet.show_shop_in_app')
        return self.make_response(True, 200, [], [{'show_shop': show_shop}], [])

    @validate_token
    @http.route('/get/calendar', type='http', auth='public', methods=['GET'], csrf=False)
    def get_calendar(self, **kwargs):
        if not kwargs.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        mobile = kwargs.get('mobile')
        customer = request.env['res.partner'].sudo().search([
            ('phone','=',mobile)
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} not found.",
                f"Customer with mobile {mobile} not found."
            ])
        subscriptions = customer.customer_sale_order_line_ids.filtered(
            lambda subs: subs.state in ['in_progress']
        )
        if not subscriptions:
            return self.make_response(False, 400, [], None, [
                f'No active subscriptions found for {customer.name} - {customer.phone}',
                f'لا توجد اشتراكات نشطة للعميل. {customer.name} - {customer.phone}'
            ])
        response_data = []
        today_date = fields.Date.today()
        tommorow_date = today_date + timedelta(days=1)
        for subscription in subscriptions:
            meal_calendar = request.env['customer.meal.calendar'].sudo().search([('so_id', '=', subscription.id)])
            for meal in meal_calendar:
                if meal.state in ['active_with_meal','active'] and meal.delivery_status == 'delivered':
                    vals = {
                        'date': meal.date.strftime('%Y-%m-%d'),
                        'status': 'delivered',
                        'subscription_id': subscription.id
                    }
                    response_data.append(vals)
                elif meal.date == today_date and meal.state in ['active_with_meal','active']:
                    vals = {
                        'date': meal.date.strftime('%Y-%m-%d'),
                        'status': 'meal-selected',
                        'subscription_id': subscription.id
                    }
                    response_data.append(vals)
                elif meal.date == tommorow_date and meal.state in ['active_with_meal','active']:
                    vals = {
                        'date': meal.date.strftime('%Y-%m-%d'),
                        'status': 'meal-selected',
                        'subscription_id': subscription.id
                    }
                    response_data.append(vals)
                elif meal.state == 'active_with_meal' and all(map(lambda x: x == 'customer', meal_calendar.filtered(lambda cal: cal.date == meal.date).mapped('meal_selection_by'))):
                    vals = {
                        'date': meal.date.strftime('%Y-%m-%d'),
                        'status': 'meal-selected',
                        'subscription_id': subscription.id
                    }
                    response_data.append(vals)
                elif meal.state == 'active_with_meal' and not all(map(lambda x: x == 'customer', meal_calendar.filtered(lambda cal: cal.date == meal.date).mapped('meal_selection_by'))):
                    vals = {
                        'date': meal.date.strftime('%Y-%m-%d'),
                        'status': 'meal-not-selected',
                        'subscription_id': subscription.id
                    }
                    response_data.append(vals)
                elif meal.state == 'active':
                    vals = {
                        'date': meal.date.strftime('%Y-%m-%d'),
                        'status': 'meal-not-selected',
                        'subscription_id': subscription.id
                    }
                    response_data.append(vals)
                elif meal.state == 'freezed':
                    vals = {
                        'date': meal.date.strftime('%Y-%m-%d'),
                        'status': 'freezed',
                        'subscription_id': subscription.id
                    }
                    response_data.append(vals)
                elif meal.state == 'off_day':
                    vals = {
                        'date': meal.date.strftime('%Y-%m-%d'),
                        'status': 'off-day',
                        'subscription_id': subscription.id
                    }
                    response_data.append(vals)
        if response_data:
            return self.make_response(True, 200, [], response_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No data found.",
                "No data found."
            ])

    @validate_token
    @http.route('/calendar', type='http', auth='public', methods=['GET'], csrf=False)
    def calendar(self, **kwargs):
        if not kwargs.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        mobile = kwargs.get('mobile')
        customer = request.env['res.partner'].sudo().search([
            ('phone','=',mobile)
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} not found.",
                f"Customer with mobile {mobile} not found."
            ])
        subscriptions = customer.customer_sale_order_line_ids.filtered(
            lambda subs: subs.state in ['in_progress']
        )
        if not subscriptions:
            return self.make_response(False, 400, [], None, [
                f'No active subscriptions found for {customer.name} - {customer.phone}',
                f'لا توجد اشتراكات نشطة للعميل. {customer.name} - {customer.phone}'
            ])
        response_data = {}
        today_date = fields.Date.today()
        for subscription in subscriptions:
            meal_calendar = request.env['customer.meal.calendar'].sudo().search([('so_id', '=', subscription.id)])
            for meal in meal_calendar:
                if meal.date < today_date and meal.state in ['active_with_meal','active']:
                    response_data[meal.date.strftime('%Y-%m-%d')] = "delivered"
                elif meal.state == 'active_with_meal' and all(map(lambda x: x == 'customer', meal_calendar.filtered(lambda cal: cal.date == meal.date).mapped('meal_selection_by'))):
                    response_data[meal.date.strftime('%Y-%m-%d')] = "meal-selected"
                elif meal.state == 'active_with_meal' and not all(map(lambda x: x == 'customer', meal_calendar.filtered(lambda cal: cal.date == meal.date).mapped('meal_selection_by'))):
                    response_data[meal.date.strftime('%Y-%m-%d')] = "meal-not-selected"
                elif meal.state == 'active':
                    response_data[meal.date.strftime('%Y-%m-%d')] = "meal-not-selected"
                elif meal.state == 'freezed':
                    response_data[meal.date.strftime('%Y-%m-%d')] = "freezed"
                elif meal.state == 'off_day':
                    response_data[meal.date.strftime('%Y-%m-%d')] = "off-day"
        if response_data:
            return self.make_response(True, 200, [], response_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No data found.",
                "No data found."
            ])
                
    @validate_token
    @http.route('/calendar/meals/<mobile>', type='http', auth='public', methods=['GET'], csrf=False)
    def meals_available_to_customer(self, mobile, **kwargs):
        if not kwargs.get('date', False):
            return self.make_response(False, 400, [], None, [
                'Date not passed.',
                'يرجى إدخال التاريخ المطلوب.'
            ])
        meal_date = kwargs.get('date')
        meal_date = datetime.strptime(meal_date, '%Y-%m-%d').date()
        ramdan_start_date = request.env.company.ramdan_start_date
        ramdan_end_date = request.env.company.ramdan_end_date
        if (
            ramdan_start_date
            and ramdan_end_date
            and meal_date
            and ramdan_start_date <= meal_date <= ramdan_end_date
        ):
            is_ramdan_day = True
        else:
            is_ramdan_day = False
        meal_day = meal_date.strftime('%A').lower()
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile not passed.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone', '=', mobile)
        ], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم."
            ])
        subscriptions = customer.customer_sale_order_line_ids.filtered(
            lambda subs: subs.state in ['in_progress']
        )
        if subscriptions:
            valid_sub = subscriptions.filtered(lambda subs: subs.actual_start_date <= meal_date and subs.end_date >= meal_date)
            if valid_sub:
                subscriptions = valid_sub
        if not subscriptions:
            subscriptions = customer.customer_sale_order_line_ids.filtered(lambda subs:
                subs.actual_start_date >= fields.Date.today()
                and subs.state in ['paid']
            )
            subscriptions = subscriptions[0] if subscriptions else False
        if not subscriptions:
            return self.make_response(False, 400, [], None, [
                f'No active subscriptions found for {customer.name} - {customer.phone}',
                f'لا توجد اشتراكات نشطة للعميل. {customer.name} - {customer.phone}'
            ])
        calendar_entries_date = subscriptions.meal_calendar_ids.filtered(lambda cal: cal.date == meal_date)
        response_data = {'subscription_recommended_calories': subscriptions[0].plan_id.calories, 'meals': []}
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if meal_day == 'sunday':
            meal_day_domain = [('sunday','=',True)]
        elif meal_day == 'monday':
            meal_day_domain = [('monday','=',True)]
        elif meal_day == 'tuesday':
            meal_day_domain = [('tuesday','=',True)]
        elif meal_day == 'wednesday':
            meal_day_domain = [('wednesday','=',True)]
        elif meal_day == 'thursday':
            meal_day_domain = [('thursday','=',True)]
        elif meal_day == 'friday':
            meal_day_domain = [('friday','=',True)]
        elif meal_day == 'saturday':
            meal_day_domain = [('saturday','=',True)]
        else:
            meal_day_domain = []
        ramdan_plan_applied = subscriptions[0].ramdan_plan_applied
        normal_plan = subscriptions[0].ramdan_plan_id if subscriptions[0].ramdan_plan_id.is_ramdan_plan else subscriptions[0].plan_id
        normal_meal_config = subscriptions[0].ramdan_meal_count_ids.filtered(lambda meal: meal.additional_count > 0) if subscriptions[0].ramdan_plan_id.is_ramdan_plan else subscriptions[0].meal_count_ids.filtered(lambda meal: meal.additional_count > 0)
        if is_ramdan_day:
            if subscriptions[0].ramdan_plan_id.is_ramdan_plan:
                ramdan_plan = subscriptions[0].ramdan_plan_id
                ramdan_meal_config = subscriptions[0].ramdan_meal_count_ids.filtered(lambda meal: meal.additional_count > 0)
            elif subscriptions[0].plan_id.is_ramdan_plan:
                ramdan_plan = subscriptions[0].plan_id
                ramdan_meal_config = subscriptions[0].meal_count_ids.filtered(lambda meal: meal.additional_count > 0)
            else:
                ramdan_plan = subscriptions[0].plan_id
                ramdan_meal_config = subscriptions[0].meal_count_ids.filtered(lambda meal: meal.additional_count > 0)
        else:
            ramdan_plan = subscriptions[0].plan_id if not subscriptions[0].plan_id.is_ramdan_plan else subscriptions[0].ramdan_plan_id
            ramdan_meal_config = subscriptions[0].meal_count_ids.filtered(lambda meal: meal.additional_count > 0) if not subscriptions[0].plan_id.is_ramdan_plan else subscriptions[0].ramdan_meal_count_ids.filtered(lambda meal: meal.additional_count > 0)
        if ramdan_plan_applied and is_ramdan_day:
            plan = normal_plan
            meal_config = normal_meal_config
        else:
            plan = ramdan_plan
            meal_config = ramdan_meal_config
        for meal_line in meal_config:
            domain = [('meal_category_id', '=', meal_line.meal_category_id.id),('plan_ids', 'in', plan.ids)]
            if len(meal_day_domain) > 0:
                domain += meal_day_domain
            meals = request.env['product.template'].search(domain)
            items = []
            customer_allergies = customer.allergies
            customer_dislikes = customer.dislikes_ids
            category_entries = calendar_entries_date.filtered(lambda cal: cal.meal_category_id == meal_line.meal_category_id)
            selected_meals = category_entries.filtered(lambda cal: cal.meal_selection_by == 'customer' or cal.delivery_status == 'delivered').mapped('meal_id') if category_entries else False
            for meal in meals:
                if not meal.ingredients_line_ids.filtered(lambda allergy: allergy.ingredient_id in customer_allergies):
                    meal_dislikes = meal.ingredients_line_ids.filtered(lambda dislike: dislike.dislikable and dislike.ingredient_id in customer_dislikes)
                    is_selected = False
                    if selected_meals and meal in selected_meals:
                        is_selected = True
                    selected_count = 0
                    user_tz = request.env.context.get('tz') or request.env.company.partner_id.tz or 'UTC'
                    user_timezone = timezone(user_tz)                
                    current_datetime = datetime.now(user_timezone)
                    current_time = current_datetime.time()
                    today = current_datetime.date()
                    tomorrow = today + timedelta(days=1)
                    tomorrow_1 = today + timedelta(days=2)
                    now = current_time
                    time_430_am = time(4, 30)
                    if now > time_430_am:
                        if meal_date == today or meal_date == tomorrow or meal_date == tomorrow_1:
                            calendar_entries_meal = calendar_entries_date.filtered(
                                lambda cal: cal.meal_id == meal        
                            )
                        else:
                            calendar_entries_meal = calendar_entries_date.filtered(
                                lambda cal: cal.meal_id == meal
                                and (
                                    cal.meal_selection_by == 'customer'
                                    or cal.delivery_status == 'delivered'
                                )
                            )
                            if not calendar_entries_meal:
                                calendar_entries_meal = calendar_entries_date.filtered(
                                    lambda cal: cal.meal_id == meal
                                    and (
                                        cal.meal_selection_by != 'customer'
                                        and cal.delivery_status == 'delivered'
                                    )
                                )
                                is_selected = bool(calendar_entries_meal)
                    else:
                        if meal_date == today or meal_date == tomorrow:
                            calendar_entries_meal = calendar_entries_date.filtered(
                                lambda cal: cal.meal_id == meal        
                            )
                        else:
                            calendar_entries_meal = calendar_entries_date.filtered(
                                lambda cal: cal.meal_id == meal
                                and (
                                    cal.meal_selection_by == 'customer'
                                    or cal.delivery_status == 'delivered'
                                )
                            )
                            if not calendar_entries_meal:
                                calendar_entries_meal = calendar_entries_date.filtered(
                                    lambda cal: cal.meal_id == meal
                                    and (
                                        cal.meal_selection_by != 'customer'
                                        and cal.delivery_status == 'delivered'
                                    )
                                )
                                is_selected = bool(calendar_entries_meal)
                    meal_tags = ', '.join(meal.meal_tag_id.mapped('name')) if meal.meal_tag_id else ''
                    ingredients = []
                    for ingredient in meal.ingredients_line_ids.mapped('ingredient_id'):
                        ingredients.append({
                            'id': ingredient.id,
                            'name': ingredient.name,
                            'arabic_name': ingredient.arabic_name,
                            'image': f"{base_url}/web/image?model=product.template&id={ingredient.id}&field=image_1920" if not ingredient.image_1920 else ""
                        })
                    disliked_ingredients = []
                    for dislike_ingredient in meal_dislikes.mapped('ingredient_id'):
                        disliked_ingredients.append({
                            'id': dislike_ingredient.id,
                            'name': dislike_ingredient.name,
                            'arabic_name': dislike_ingredient.arabic_name,
                            'image': f"{base_url}/web/image?model=product.template&id={dislike_ingredient.id}&field=image_1920" if not dislike_ingredient.image_1920 else ""
                        })
                    if meal in customer.favourite_meals_ids:
                        is_favourite = True
                    else:
                        is_favourite = False
                    items.append({
                        'id': meal.id,
                        'tags': ', '.join(meal.meal_tag_id.mapped('name')) if meal.meal_tag_id else '',
                        'name': meal.name,
                        'arabic_name': meal.arabic_name,
                        'description': meal.meal_description,
                        'arabic_description': meal.arabic_meal_description,
                        'image': f"{base_url}/web/image?model=product.template&id={meal.id}&field=image_1920" if meal.image_1920 else "",
                        'tags': meal_tags,
                        'calories': (meal.calories * meal_line.calorie_multiply_factor) or 0.0,
                        'protein': (meal.protein * meal_line.calorie_multiply_factor) or 0.0,
                        'carbs': (meal.carbohydrates * meal_line.calorie_multiply_factor) or 0.0,
                        'fat': (meal.fat * meal_line.calorie_multiply_factor) or 0.0,
                        'rating': float(meal.rating) or 0.0,
                        'rating_count': meal.rating_count or 0,
                        'is_selected': is_selected,
                        'selected_count': len(calendar_entries_meal) if calendar_entries_meal else 0,
                        'is_dislike': True if meal_dislikes else False,
                        'restrict_double_selection' : meal.restrict_double_selection,
                        'ingredients': ingredients,
                        'dislikes' : disliked_ingredients,
                        'is_favourite': is_favourite
                    })
            response_data['meals'].append({
                'id': meal_line.meal_category_id.id,
                'name': meal_line.meal_category_id.name,
                'arabic_name': meal_line.meal_category_id.arabic_name,
                'item_count': meal_line.additional_count,
                'items': items
            })
        if response_data:
            return self.make_response(True, 200, [], [response_data], [])
        else:
            return self.make_response(False, 400, [], None, [
                "No data found.",
                "No data found."
            ])

    @validate_token
    @http.route('/today_delivery_meals', type='http', auth='public', methods=['GET'], csrf=False)
    def get_today_meals(self, **kwargs):
        if not kwargs.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        if not kwargs.get('date', False):
            return self.make_response(False, 400, [], None, [
                'Date not passed.',
                'يرجى إدخال التاريخ المطلوب.'
            ])
        mobile = kwargs.get('mobile')
        customer = request.env['res.partner'].sudo().search([
            ('phone','=',mobile)
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} not found.",
                f"Customer with mobile {mobile} not found."
            ])
        try:
            delivery_date = datetime.strptime(kwargs.get('date'), '%Y-%m-%d').date()
        except:
            return self.make_response(False, 400, [], None, [
                'Invalid Date format.',
                'Invalid Date format.'
            ])
        delivery_order = request.env['driver.order'].search([
            ('customer_id', '=', customer.id),
            ('date', '=', delivery_date)
        ], limit=1)
        response_list = []
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if delivery_order:
            categories = delivery_order.meal_calendar_ids.mapped('meal_category_id')
            for category in categories:
                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'arabic_name': category.arabic_name,
                    'items': []
                }
                meals = delivery_order.meal_calendar_ids.filtered(lambda cal: cal.meal_category_id == category).mapped('meal_id')
                for meal in meals:
                    meal_tags = ', '.join(meal.meal_tag_id.mapped('name')) if meal.meal_tag_id else ''
                    if meal in customer.favourite_meals_ids:
                        is_favourite = True
                    else:
                        is_favourite = False
                    category_data['items'].append({
                        'id': meal.id,
                        'tags': ', '.join(meal.meal_tag_id.mapped('name')) if meal.meal_tag_id else '',
                        'name': meal.name,
                        'arabic_name': meal.arabic_name,
                        'description': meal.meal_description,
                        'arabic_description': meal.arabic_meal_description,
                        'image': f"{base_url}/web/image?model=product.template&id={meal.id}&field=image_1920",
                        'tags': meal_tags,
                        'calories': meal.calories,
                        'protein': meal.protein or 0.0,
                        'carbs': meal.carbohydrates or 0.0,
                        'fat': meal.fat or 0.0,
                        'rating': float(meal.rating) or 0.0,
                        'rating_count': meal.rating_count or 0,
                        'is_favourite': is_favourite
                    })
                response_list.append(category_data)
            if response_list:
                return self.make_response(True, 200, [], response_list, [])
            else:
                return self.make_response(False, 400, [], None, [
                    "No Data found.",
                    "No Data found."
                ])

        
    @validate_token
    @http.route('/subscription/history/<mobile>', type='http', auth='public', methods=['GET'], csrf=False)
    def subscription_history(self, mobile):
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile not passed.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone', '=', mobile)
        ], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم."
            ])
        subscriptions = customer.customer_sale_order_line_ids.filtered(
            lambda subs: subs.state in ['paid', 'in_progress', 'cancel']
        )
        if not subscriptions:
            return self.make_response(False, 400, [], None, [
                f'No subscriptions found for {customer.name} - {customer.phone}',
                f'لا توجد اشتراكات مسجلة. {customer.name} - {customer.phone}'
            ])
        response_data = []
        for subscription in subscriptions:
            if subscription.payment_status == 'not_paid':
                subscription_status = 'not paid'
            elif subscription.payment_status == 'partial':
                subscription_status = 'partially paid'
            else:
                subscription_status = subscription.state
            response_data.append({
                'id': subscription.id,
                'plan': subscription.plan_id.name,
                'plan_arabic': subscription.plan_id.arabic_name,
                'start_date': subscription.actual_start_date.strftime('%Y-%m-%d') if subscription.actual_start_date else '',
                'end_date': subscription.end_date.strftime('%Y-%m-%d') if subscription.end_date else '',
                'state': subscription_status,
                'meals_config': [{
                    'name': meal_line.meal_category_id.name,
                    'arabic_name': meal_line.meal_category_id.arabic_name,
                    'item_count': meal_line.additional_count
                } for meal_line in subscription.meal_count_ids]
            })
        if response_data:
            return self.make_response(True, 200, [], response_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No data found.",
                "No data found."
            ])

    @validate_token
    @http.route('/allergy/search/<search_key>', type='http', auth='public', methods=['GET'], csrf=False)
    def search_allergy(self, search_key):
        try:
            if not search_key:
                return self.make_response(False, 400, [], None, [
                    "Search key not passed.",
                    "Search key not passed."
                ])
            allergies_search_query = f"select id, name->>'en_US' as name, arabic_name from product_template where is_ingredient=True and name->>'en_US' ILIKE '%{search_key}%'"
            request.env.cr.execute(allergies_search_query)
            allergies = request.env.cr.dictfetchall()
            if not allergies:
                return self.make_response(False, 400, [], None, [
                    "No allergies found.",
                    "لم يتم العثور على بيانات حساسية للعميل."
                ])
            return self.make_response(True, 200, [], allergies, [])
        except:
            return self.make_response(False, 500, [], None, [
                "Internal Error",
                "حدث خطأ داخلي."
            ])

    def format_saudi_phone_number(self, phone_number):
        """
        Format and validate Saudi Arabian phone numbers.
        
        Args:
            phone_number (str): The phone number to format and validate
        
        Returns:
            str or None: Formatted phone number with 966 prefix if valid, None otherwise
        """
        # Remove any spaces, dashes, or other non-digit characters
        cleaned_number = re.sub(r'\D', '', phone_number)
        
        # Check different valid formats
        saudi_code_patterns = [
            r'^(966)?\d{9}$',  # 9 digits with optional country code
            r'^(966)?\d{10}$'  # 10 digits with optional country code
        ]
        
        # Validate number against patterns
        if not any(re.match(pattern, cleaned_number) for pattern in saudi_code_patterns):
            return None
        
        # If number doesn't start with 966, add it
        if not cleaned_number.startswith('966'):
            # If 10-digit number, remove leading 0
            if len(cleaned_number) == 10 and cleaned_number.startswith('0'):
                cleaned_number = cleaned_number[1:]
            
            # Ensure 9 digits and add 966 prefix
            if len(cleaned_number) == 9:
                return f'966{cleaned_number}'
        
        # If number already starts with 966, return as is
        return cleaned_number

    @validate_token
    @http.route('/send_otp', type='http', auth='public', methods=['POST'], csrf=False)
    def send_otp(self):
        data = request.get_json_data()
        mobile = data.get('mobile', False)
        reset_password = data.get('reset_password', False)
        if len(mobile) == 12 and mobile[0:3] == '966':
            mobile = mobile[3:]
        elif len(mobile) == 13 and mobile[0:4] == '+966':
            mobile = mobile[4:]
        if not mobile:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": ["Mobile not passed.", "يرجى إدخال رقم الجوال."]
            }), headers=[('Content-Type', 'application/json')])
        if not reset_password:
            # check_existing_query = f"""SELECT id FROM res_partner WHERE phone='{mobile}' or phone='+966{mobile}'"""
            # request.env.cr.execute(check_existing_query)
            # existing_customer = request.env.cr.dictfetchone()
            existing_customer = request.env['res.partner'].sudo().search([
                '|',
                ('phone', '=', mobile),
                ('phone', '=', f'+966{mobile}')
            ], limit=1)
            if existing_customer:
                return request.make_response(json.dumps({
                    "statusOk": False,
                    "statusCode": 400,
                    "message": [f"Customer with mobile number {mobile} exists.", f"Customer with mobile number {mobile} exists."],
                    "payload": [],
                    "error": [f"Customer with mobile number {mobile} exists.", f"Customer with mobile number {mobile} exists."]
                }), headers=[('Content-Type', 'application/json')])
        else:
            # check_existing_query = f"""SELECT id FROM res_partner WHERE phone='{mobile}' or phone='+966{mobile}'"""
            # request.env.cr.execute(check_existing_query)
            # existing_customer = request.env.cr.dictfetchone()
            existing_customer = request.env['res.partner'].sudo().search([
                '|',
                ('phone', '=', mobile),
                ('phone', '=', f'+966{mobile}')
            ], limit=1)
            if not existing_customer:
                return request.make_response(json.dumps({
                    "statusOk": False,
                    "statusCode": 400,
                    "message": [f"Customer with mobile number {mobile} doesn't exists.", f"Customer with mobile number {mobile} doesn't exists."],
                    "payload": [],
                    "error": [f"Customer with mobile number {mobile} doesn't exists.", f"Customer with mobile number {mobile} doesn't exists."]
                }), headers=[('Content-Type', 'application/json')])
        # query = f"""DELETE FROM sms_otp_verification WHERE mobile='+966{mobile}' or mobile='{mobile}'"""
        # request.env.cr.execute(query)
        otp_rec = request.env['sms.otp.verification'].sudo().search([
            '|',
            ('mobile', '=', mobile),
            ('mobile', '=', f'+966{mobile}')
        ])
        if otp_rec:
            otp_rec.unlink()
        otp = ''.join([str(random.randint(0, 999)).zfill(3) for _ in range(2)])
        _logger.info(otp)
        try:
            sms_bearer_token = request.env['sms.gateway'].search([], limit=1).bearer_token
            sms_client = client(sms_bearer_token)
        except:
            sms_client = False
        phone_number = self.format_saudi_phone_number(mobile)
        request.env['sms.otp.verification'].create({
            "mobile": phone_number,
            "otp": otp
        })
        my_message = f"Your OTP for Feed is {otp}"
        if phone_number and sms_client:
            sms_response = sms_client.sendMsg(my_message, [phone_number], 'Feedmeal', scheduled=False)
            if isinstance(sms_response, str):
                sms_response = json.loads(sms_response)
            if sms_response.get("statusCode") == 201:
                _logger.info(f"OTP {otp} sent successfully to {phone_number}")
                return request.make_response(json.dumps({
                    "statusOk": True,
                    "statusCode": 200,
                    "message": [],
                    "payload": [],
                    "error": []
                }), headers=[('Content-Type', 'application/json')])
            elif sms_response.get("statusCode") == 400:
                return request.make_response(json.dumps({
                    "statusOk": False,
                    "statusCode": 400,
                    "message": [],
                    "payload": [],
                    "error": ["Mobile(s) number(s) is not specified or incorrect", "Mobile(s) number(s) is not specified or incorrect"]
                }), headers=[('Content-Type', 'application/json')])
            else:
                return request.make_response(json.dumps({
                    "statusOk": False,
                    "statusCode": 400,
                    "message": [],
                    "payload": [],
                    "error": ["Contact customer care", "Contact customer care"]
                }), headers=[('Content-Type', 'application/json')])
        else:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": "",
                "payload": [],
                "error": ["Contact customer care", "Contact customer care"]
            }), headers=[('Content-Type', 'application/json')])
    

    @validate_token
    @http.route('/verify_otp', type='http', auth='public', methods=['GET'], csrf=False)
    def verify_otp(self, **kwargs):
        _logger.info(kwargs)
        mobile = kwargs.get('mobile')
        otp = kwargs.get('otp')
        error = ""
        data_not_passed = []
        if not mobile:
            data_not_passed.append("Mobile")
        if not otp:
            data_not_passed.append("OTP")
        if data_not_passed:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": [f"{', '.join(data_not_passed)} not given.", f"{', '.join(data_not_passed)} not given."]
            }), headers=[('Content-Type', 'application/json')])
        if mobile:
            mobile_splace = mobile.split('+')
            no_space_mobile = ''.join(mobile_splace)
            if no_space_mobile[0:3] == '965':
                no_space_mobile = no_space_mobile[3:]
                mobile = f"966{no_space_mobile}"
        phone_number = self.format_saudi_phone_number(mobile)
        # query = f"""SELECT otp FROM sms_otp_verification WHERE mobile='{phone_number}'"""
        # request.env.cr.execute(query)
        # result = request.env.cr.dictfetchone()
        otp_rec = request.env['sms.otp.verification'].sudo().search([
            ('mobile', '=', phone_number),('otp','=',otp)
        ], limit=1)
        if not otp_rec:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": ["OTP request not initiated.", "OTP request not initiated."]
            }), headers=[('Content-Type', 'application/json')])

        _logger.info(f"NUMBER : {otp_rec.mobile}, OTP : {otp_rec.otp}")
        send_otp = otp
        otp = otp_rec.otp
        if otp == send_otp:
            return request.make_response(json.dumps({
                "statusOk": True,
                "statusCode": 200,
                "message": [],
                "payload": [],
                "error": []
            }), headers=[('Content-Type', 'application/json')])
        else:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": ["Invalid OTP", "رمز التحقق غير صحيح."]
            }), headers=[('Content-Type', 'application/json')])

    

    @validate_token
    @http.route('/driver/send_otp', type='http', auth='public', methods=['POST'], csrf=False)
    def driver_send_otp(self):
        data = request.get_json_data()
        mobile = data.get('mobile', False)
        if mobile[0:4] == '+966':
            mobile = mobile[4:]
        reset_password = data.get('reset_password', False)
        if not mobile:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": ["Mobile not passed.", "يرجى إدخال رقم الجوال."]
            }), headers=[('Content-Type', 'application/json')])
        if not reset_password:
            check_existing_query = f"""SELECT id FROM area_driver WHERE phone='{mobile}' or phone='+966{mobile}'"""
            request.env.cr.execute(check_existing_query)
            existing_driver = request.env.cr.dictfetchone()
            if existing_driver:
                return request.make_response(json.dumps({
                    "statusOk": False,
                    "statusCode": 400,
                    "message": [],
                    "payload": [],
                    "error": [f"Driver with mobile number {mobile} exists.", f"Driver with mobile number {mobile} exists."]
                }), headers=[('Content-Type', 'application/json')])
        query = f"""DELETE FROM sms_otp_verification WHERE mobile='+966{mobile}' or mobile='{mobile}'"""
        request.env.cr.execute(query)
        otp = ''.join([str(random.randint(0, 999)).zfill(3) for _ in range(2)])
        _logger.info(otp)
        if mobile[0:4] != '+966':
            mobile = f'+966{mobile}'
        request.env['sms.otp.verification'].create({
            "mobile": mobile,
            "otp": otp
        })
        try:
            sms_bearer_token = self.env['sms.gateway'].search([], limit=1).bearer_token
            sms_client = client(sms_bearer_token)
        except:
            sms_client = False
        phone_number = self.format_saudi_phone_number(phone)
        if phone_number and sms_client:
            sms_response = sms_client.sendMsg(my_message, [phone_number], 'DietDone')
            if sms_response.get("statusCode") == 201:
                _logger.info(f"OTP {otp} sent successfully to {phone_number}")
                return request.make_response(json.dumps({
                    "statusOk": True,
                    "statusCode": sms_response.get("statusCode", ''),
                    "message": [],
                    "payload": [],
                    "error": []
                }), headers=[('Content-Type', 'application/json')])
            elif sms_response.get("statusCode") == 400:
                return request.make_response(json.dumps({
                    "statusOk": False,
                    "statusCode": sms_response.get("statusCode", ''),
                    "message": [],
                    "payload": [],
                    "error": ["Mobile(s) number(s) is not specified or incorrect", "Mobile(s) number(s) is not specified or incorrect"]
                }), headers=[('Content-Type', 'application/json')])
            else:
                return request.make_response(json.dumps({
                    "statusOk": False,
                    "statusCode": sms_response.get("statusCode", ''),
                    "message": [],
                    "payload": [],
                    "error": ["Contact customer care", "Contact customer care"]
                }), headers=[('Content-Type', 'application/json')])
        else:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": ["Contact customer care", "Contact customer care"]
            }), headers=[('Content-Type', 'application/json')])
    

    @validate_token
    @http.route('/driver/verify_otp', type='http', auth='public', methods=['GET'], csrf=False)
    def driver_verify_otp(self, **kwargs):
        _logger.info(kwargs)
        mobile = kwargs.get('mobile')
        otp = kwargs.get('otp')
        error = ""
        data_not_passed = []
        if not mobile:
            data_not_passed.append("Mobile")
        if not otp:
            data_not_passed.append("OTP")
        if data_not_passed:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": [f"{', '.join(data_not_passed)} not given.", f"{', '.join(data_not_passed)} not given."]
            }), headers=[('Content-Type', 'application/json')])
        query = f"""SELECT otp FROM sms_otp_verification WHERE mobile='+966{mobile}' or mobile='{mobile}'"""
        request.env.cr.execute(query)
        result = request.env.cr.dictfetchone()
        _logger.info(result)
        if not result:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": ["OTP request not initiated.", "OTP request not initiated."]
            }), headers=[('Content-Type', 'application/json')])
        send_otp = result['otp']
        if otp == send_otp:
            return request.make_response(json.dumps({
                "statusOk": True,
                "statusCode": 200,
                "message": [],
                "payload": [],
                "error": []
            }), headers=[('Content-Type', 'application/json')])
        else:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": ["Invalid OTP", "رمز التحقق غير صحيح."]
            }), headers=[('Content-Type', 'application/json')])

    @validate_token
    @http.route('/subscription_start_date_validity', type='http', auth='public', methods=['GET'], csrf=False)
    def subscription_start_date_validity(self, **kwargs):
        if not kwargs.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        if not kwargs.get('plan_choice', False):
            return self.make_response(False, 400, [], None, [
                'Plan choice not passed.',
                'يرجى إدخال النظام الغذائية المرادة.'
            ])
        mobile = kwargs.get('mobile')
        plan_choice = kwargs.get('plan_choice')
        if not kwargs.get('start_date', False):
            return self.make_response(False, 400, [], None, [
                'Date not passed.',
                'يرجى إدخال التاريخ المطلوب.'
            ])
        try:
            start_date = datetime.strptime(kwargs.get('start_date'), '%Y-%m-%d').date()
        except:
            return self.make_response(False, 400, [], None, [
                'Invalid Date format.',
                'صيغة التاريخ غير صحيحة. يرجى استخدام صيغة YYYY-MM-DD.'
            ])
        try:
            plan_choice = request.env['plan.choice'].sudo().browse(int(plan_choice))
            plan_days = plan_choice.no_of_day
            expected_end_date = start_date + timedelta(days=plan_days)
        except:
            return self.make_response(False, 400, [], None, [
                'Invalid Plan Choice.',
                'خيار النظام الغذائية المدخل غير صالح.'
            ])
        try:
            customer = request.env['res.partner'].sudo().search([
                ('phone','=',mobile)
            ])
        except:
            return self.make_response(False, 400, [], None, [
                'Customer not found.',
                'Customer not found.'
            ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} not found.",
                f"Customer with mobile {mobile} not found."
            ])
        order_capacity = int(request.env['ir.config_parameter'].sudo().get_param('diet.order_capacity', default=0))
        existing_orders_count = request.env['diet.subscription.order'].search_count([
            ('actual_start_date', '=', start_date)
        ])

        if existing_orders_count + 1 > order_capacity:
            return self.make_response(False, 400, [], None, [
                'Order capacity reached for this date.',
                'تم الوصول إلى الحد الأقصى للطلبات في هذا اليوم.'
            ])
        existing_calendar_query = f"""
            SELECT cal.id AS id 
            FROM customer_meal_calendar AS cal
            JOIN customer_sale_order_line AS so ON so.id=cal.so_id
            WHERE cal.partner_id={customer.id} 
            AND cal.date>='{start_date.strftime('%Y-%m-%d')}' 
            AND cal.date<'{expected_end_date.strftime('%Y-%m-%d')}'
            AND so.state in ('in_progress')
        """
        request.env.cr.execute(existing_calendar_query)
        existing_calendar = request.env.cr.dictfetchone()
        excluded_weekdays = []
        if not plan_choice.monday:
            excluded_weekdays.append(0)
        if not plan_choice.tuesday:
            excluded_weekdays.append(1)
        if not plan_choice.wednesday:
            excluded_weekdays.append(2)
        if not plan_choice.thursday:
            excluded_weekdays.append(3)
        if not plan_choice.friday:
            excluded_weekdays.append(4)
        if not plan_choice.saturday:
            excluded_weekdays.append(5)
        if not plan_choice.sunday:
            excluded_weekdays.append(6)
        end_date = request.env['diet.subscription.order']._get_end_date(excluded_weekdays, plan_choice.no_of_day, start_date)
        company = request.env.company
        default_tax = company.sudo().account_sale_tax_id
        if default_tax:
            tax_obj = default_tax.compute_all(plan_choice.plan_price)
            tax_amount = sum([tax['amount'] for tax in tax_obj['taxes']])
            total = tax_obj['total_excluded']
            grand_total = tax_obj['total_included']
        else:
            tax_amount = 0.0
            total = plan_choice.plan_price
            grand_total = plan_choice.plan_price
        points = 0
        if customer:
            reward_master = request.env["customer.referrals"].search([
                ('customer_id', '=', customer.id)
            ], limit=1)
            if reward_master:
                points = reward_master.balance_amount
        vals = {
            "end_date": end_date.strftime('%Y-%m-%d'),
            "total" : total,
            "tax_amount" : tax_amount,
            "grand_total" : grand_total,
            "available_points": float(points)
        }
        if existing_calendar:
            return self.make_response(False, 400, [], None, [
                f"Subscription already exists for {start_date.strftime('%Y-%m-%d')}",
                f"الاشتراك موجود بالفعل.{start_date.strftime('%Y-%m-%d')}"
            ])
        else:
            return self.make_response(True, 200, [], [vals], [])

    @validate_token
    @http.route('/apply_reward_points', type='http', auth='public', methods=['POST'], csrf=False)
    def apply_reward_points(self, **kwargs):
        kwargs = request.get_json_data()
        if not kwargs.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        if not kwargs.get('plan_choice_id', False):
            return self.make_response(False, 400, [], None, [
                'Plan ID not passed.',
                'يرجى إدخال ID  النظام المطلوبة.'
            ])
        try:
            customer = request.env['res.partner'].sudo().search([
                ('phone','=',kwargs.get('mobile', False))
            ])
        except:
            return self.make_response(False, 400, [], None, [
                'Customer not found.',
                'Customer not found.'
            ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {kwargs.get('mobile', False)} not found.",
                f"Customer with mobile {kwargs.get('mobile', False)} not found."
            ])
        try:
            plan = request.env['plan.choice'].sudo().browse(int(kwargs['plan_choice_id']))
        except:
            return self.make_response(False, 400, [], None, [
                f'No plan choice found with ID {kwargs["plan_choice_id"]}.',
                f'No plan choice found with ID {kwargs["plan_choice_id"]}.'
            ])
        cost = plan.plan_price
        company = request.env.company
        default_tax = company.sudo().account_sale_tax_id
        if default_tax:
            tax_obj = default_tax.compute_all(cost)
            tax_amount = sum([tax['amount'] for tax in tax_obj['taxes']])
            total = tax_obj['total_excluded']
            grand_total = tax_obj['total_included']
        else:
            total = cost
            tax_amount = 0.0
            discount = 0
            grand_total = cost
        points = 0
        if customer:
            reward_master = request.env["customer.referrals"].search([
                ('customer_id', '=', customer.id)
            ], limit=1)
            if reward_master:
                points = reward_master.balance_amount
        if points > grand_total:
            return self.make_response(True, 200, [], [{
                'total': total,
                'tax': tax_amount,
                'discount': grand_total,
                'grand_total': 0.0
            }], [])
        else:
            return self.make_response(False, 400, [], [{
                'total': total,
                'tax': tax_amount,
                'discount': 0.0,
                'grand_total': grand_total
            }],
            [
                "Insufficient points.",
                "النقاط المتوفرة غير كافية."
            ])

    @validate_token
    @http.route('/subscription_payment_link/<subscription_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def subscription_payment_link(self, subscription_id):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if isinstance(subscription_id, str):
            subscription_id = int(subscription_id)
        try:
            subscription = request.env['diet.subscription.order'].sudo().browse(subscription_id)
            if not subscription:
                return self.make_response(False, 400, [], None, [
                    'Subscription not found.',
                    'Subscription not found.'
                ])
        except:
            return self.make_response(False, 400, [], None, [
                'Invalid Subscription ID.',
                'Invalid Subscription ID.'
            ])
        if subscription.state in ['paid', 'in_progress'] and subscription.payment_status == 'paid':
            return self.make_response(False, 200, [], None, [
                'Subscription already paid.',
                'Subscription already paid.'
            ])
        elif subscription.state == 'paid' and subscription.payment_status == 'not_paid':
            invoice = subscription.invoice_ids[0]
            data = [{
                'subscription_id': subscription.id,
                'order_reference':subscription.order_number if subscription.order_number else '',
                'payment_reference':invoice.name if invoice.name else '',
                'transaction_url': invoice.tap_payment_transaction_url if invoice else '',
                'redirect_url': invoice.tap_payment_redirect_url if invoice else '',
                'payment_status_url': f'{base_url}/payment/status',
                'plan_id': subscription.plan_id.id,
                'plan_name': subscription.plan_id.name,
                'plan_arabic_name': subscription.plan_id.arabic_name,
                'start_date': subscription.actual_start_date.strftime('%Y-%m-%d') if subscription.actual_start_date else '1900-01-01',
                'end_date': subscription.end_date.strftime('%Y-%m-%d') if subscription.end_date else '1900-01-01',
                'total': subscription.total if subscription.total else 0.0,
                'coupon_discount': subscription.coupon_discount if subscription.coupon_discount else 0.0,
                'grand_total': subscription.grand_total if subscription.grand_total else 0.0,
            }]
            return self.make_response(True, 200, [], data, [])
        else:
            return self.make_response(False, 400, [], None, [
                'Data not found. Contact customer care.',
                'Data not found. Contact customer care.'
            ])

    @validate_token
    @http.route('/meals_menu', type='http', auth='public', methods=['GET'], csrf=False)
    def meals_menu(self, **kwargs):
        if not kwargs.get('day', False):
            return self.make_response(False, 400, [], None, [
                'Day not passed.',
                'Day not passed.'
            ])
        day = kwargs.get('day')
        day = day.lower()
        if day not in ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']:
            return self.make_response(False, 400, [], None, [
                'Invalid Day.',
                'Invalid Day.'
            ])
        domain = [('active','=',True), ('show_in_app_menu','=',True)]
        if day == 'sunday':
            domain.append(('sunday','=',True))
        elif day == 'monday':
            domain.append(('monday','=',True))
        elif day == 'tuesday':
            domain.append(('tuesday','=',True))
        elif day == 'wednesday':
            domain.append(('wednesday','=',True))
        elif day == 'thursday':
            domain.append(('thursday','=',True))
        elif day == 'friday':
            domain.append(('friday','=',True))
        elif day == 'saturday':
            domain.append(('saturday','=',True))
        response_data = []
        categories = request.env['meals.category'].sudo().search([])
        for category in categories:
            category_data = {
                'id': category.id,
                'name': category.name,
                'arabic_name': category.arabic_name,
                'meals': []
            }
            meals = request.env['product.template'].sudo().search(domain + [('meal_category_id','in',category.ids)])
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            for meal in meals:
                meal_tags = ', '.join(meal.meal_tag_id.mapped('name')) if meal.meal_tag_id else ''
                ingredients = []
                for ingredient in meal.ingredients_line_ids.mapped('ingredient_id'):
                    ingredients.append({
                        'id': ingredient.id,
                        'name': ingredient.name,
                        'arabic_name': ingredient.arabic_name,
                        'image': f"{base_url}/web/image?model=product.template&id={ingredient.id}&field=image_1920" if ingredient.image_1920 else ""
                    })
                category_data['meals'].append({
                    'id': meal.id,
                    'tags': ', '.join(meal.meal_tag_id.mapped('name')) if meal.meal_tag_id else '',
                    'name': meal.name,
                    'arabic_name': meal.arabic_name,
                    'description': meal.meal_description,
                    'arabic_description': meal.arabic_meal_description,
                    'image': f"{base_url}/web/image?model=product.template&id={meal.id}&field=image_1920",
                    'tags': meal_tags,
                    'calories': meal.calories,
                    'protein': meal.protein or 0.0,
                    'carbs': meal.carbohydrates or 0.0,
                    'fat': meal.fat or 0.0,
                    'rating': float(meal.rating) or 0.0,
                    'rating_count': meal.rating_count or 0,
                    'ingredients' : ingredients
                })
            response_data.append(category_data)
        return self.make_response(True, 200, [], response_data, [])
    
    @validate_token
    @http.route('/eshop/view_cart/<mobile>', type='http', auth='public', methods=['GET'], csrf=False)
    def view_cart(self, mobile):
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile not passed.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone', '=', mobile)
        ], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم."
            ])
        cart = request.env['diet.eshop.sale'].sudo().search([
            ('customer_id', '=', customer.id),
            ('state', '=', 'draft')
        ], limit=1)
        if not cart:
            return self.make_response(False, 400, [], None, [
                f'No items found',
                f'No items found'
            ])
        else:
            response_data = {
                'order_reference': cart.name,
                'order_date': cart.order_date.strftime('%Y-%m-%d'),
                'state': cart.state,
                'total': cart.total,
                'invoice_reference': cart.invoice_ids[0].name if cart.invoice_ids else '',
                'order_line': [{
                    'meal_id': line.meal_id.id,
                    'meal_name': line.meal_id.name,
                    'quantity': line.quantity
                } for line in cart.meal_line_ids]
            }
            return self.make_response(True, 200, [], response_data, [])
        
    @validate_token
    @http.route('/eshop/add_to_cart', type='http', auth='public', methods=['POST'], csrf=False)
    def add_to_eshop_cart(self):
        data = request.get_json_data()
        if not data.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        if not data.get('meal_id', False):
            return self.make_response(False, 400, [], None, [
                'Meal ID not passed.',
                'Meal ID not passed.'
            ])
        if not data.get('quantity', False):
            return self.make_response(False, 400, [], None, [
                'Quantity not passed.',
                'Quantity not passed.'
            ])
        mobile = data.get('mobile')
        meal_id = data.get('meal_id')
        quantity = data.get('quantity')
        customer = request.env['res.partner'].sudo().search([
            ('phone','=',mobile)
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} not found.",
                f"Customer with mobile {mobile} not found."
            ])
        meal = request.env['product.template'].sudo().browse(int(meal_id))
        if not meal:
            return self.make_response(False, 400, [], None, [
                f"Meal with ID {meal_id} not found.",
                f"Meal with ID {meal_id} not found."
            ])
        cart = request.env['diet.eshop.sale'].sudo().search([
            ('customer_id', '=', customer.id),
            ('state', '=', 'draft')
        ], limit=1)
        if not cart:
            cart = request.env['diet.eshop.sale'].sudo().create({
                'customer_id': customer.id
            })
        cart_line = cart.meal_line_ids.filtered(lambda line: line.meal_id == meal)
        if cart_line:
            cart_line.quantity += quantity
        else:
            cart_line = request.env['diet.eshop.sale.line'].sudo().create({
                'meal_id': meal.id,
                'quantity': quantity,
                'order_id': cart.id
            })
        response_data = {
            'order_reference': cart.name,
            'order_date': cart.order_date.strftime('%Y-%m-%d'),
            'state': cart.state,
            'total': cart.total,
            'invoice_reference': cart.invoice_ids[0].name if cart.invoice_ids else '',
            'order_line': [{
                'meal_id': line.meal_id.id,
                'meal_name': line.meal_id.name,
                'quantity': line.quantity
            } for line in cart.meal_line_ids]
        }
        return self.make_response(True, 200, [
            "Item added to cart successfully.",
            "Item added to cart successfully."
        ], response_data, [])
    
    @validate_token
    @http.route('/eshop/remove_from_cart', type='http', auth='public', methods=['POST'], csrf=False)
    def remove_from_eshop_cart(self):
        data = request.get_json_data()
        if not data.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        if not data.get('meal_id', False):
            return self.make_response(False, 400, [], None, [
                'Meal ID not passed.',
                'Meal ID not passed.'
            ])
        if not data.get('quantity', False):
            return self.make_response(False, 400, [], None, [
                'Quantity not passed.',
                'Quantity not passed.'
            ])
        mobile = data.get('mobile')
        meal_id = data.get('meal_id')
        quantity = data.get('quantity')
        customer = request.env['res.partner'].sudo().search([
            ('phone','=',mobile)
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} not found.",
                f"Customer with mobile {mobile} not found."
            ])
        meal = request.env['product.template'].sudo().browse(int(meal_id))
        if not meal:
            return self.make_response(False, 400, [], None, [
                f"Meal with ID {meal_id} not found.",
                f"Meal with ID {meal_id} not found."
            ])
        cart = request.env['diet.eshop.sale'].sudo().search([
            ('customer_id', '=', customer.id),
            ('state', '=', 'draft')
        ], limit=1)
        if not cart:
            return self.make_response(False, 400, [], None, [
                f"Cart not found.",
                f"لم يتم العثور على العربة."
            ])
        cart_line = cart.meal_line_ids.filtered(lambda line: line.meal_id == meal)
        if not cart_line:
            return self.make_response(False, 400, [], None, [
                f"Item not found in cart.",
                f"Item not found in cart."
            ])
        if cart_line.quantity <= quantity:
            cart_line.unlink()
        else:
            cart_line.quantity -= quantity
        response_data = {
            'order_reference': cart.name,
            'order_date': cart.order_date.strftime('%Y-%m-%d'),
            'state': cart.state,
            'total': cart.total,
            'invoice_reference': cart.invoice_ids[0].name if cart.invoice_ids else '',
            'order_line': [{
                'meal_id': line.meal_id.id,
                'meal_name': line.meal_id.name,
                'quantity': line.quantity
            } for line in cart.meal_line_ids]
        }
        return self.make_response(True, 200, [], response_data, [
            "Item removed from cart successfully.",
            "تمت إزالة العنصر من العربة بنجاح."
        ])

    @validate_token
    @http.route('/eshop/empty_cart', type='http', auth='public', methods=['POST'], csrf=False)
    def empty_eshop_cart(self):
        data = request.get_json_data()
        if not data.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        mobile = data.get('mobile')
        customer = request.env['res.partner'].sudo().search([
            ('phone','=',mobile)
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} not found.",
                f"Customer with mobile {mobile} not found."
            ])
        cart = request.env['diet.eshop.sale'].sudo().search([
            ('customer_id', '=', customer.id),
            ('state', '=', 'draft')
        ], limit=1)
        if not cart:
            return self.make_response(False, 400, [], None, [
                f"Cart not found.",
                f"لم يتم العثور على العربة."
            ])
        cart.unlink()
        return self.make_response(True, 200, [], None, [
            "Cart emptied successfully.",
            "تم إفراغ العربة بنجاح."
        ])
    
    @validate_token
    @http.route('/eshop/checkout', type='http', auth='public', methods=['POST'], csrf=False)
    def eshop_checkout(self):
        data = request.get_json_data()
        if not data.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        mobile = data.get('mobile')
        customer = request.env['res.partner'].sudo().search([
            ('phone','=',mobile)
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} not found.",
                f"Customer with mobile {mobile} not found."
            ])
        cart = request.env['diet.eshop.sale'].sudo().search([
            ('customer_id', '=', customer.id),
            ('state', '=', 'draft')
        ])
        if not cart:
            return self.make_response(False, 400, [], None, [
                f"Cart not found.",
                f"لم يتم العثور على العربة."
            ])
        cart.action_confirm()
        cart.action_invoice()
        invoice = cart.invoice_ids.filtered(lambda post: post.state == 'posted')[0]
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        response_data = {
            'order_reference':cart.name if cart.name else '',
            'payment_reference':invoice.name if invoice else '',
            "transaction_url": invoice.tap_payment_transaction_url if invoice else '',
            "redirect_url": invoice.tap_payment_redirect_url if invoice else '',
            "payment_status_url": f"{base_url}/payment/status",
        }
        return self.make_response(True, 200, [
            'Order placed successfully.',
            'تم تسجيل الطلب بنجاح.'
        ], response_data, [])

    @validate_token
    @http.route('/eshop/history/<mobile>', type='http', auth='public', methods=['GET'], csrf=False)
    def eshop_order_history(self, mobile):
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile not passed.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone', '=', mobile)
        ], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم."
            ])
        orders = request.env['diet.eshop.sale'].sudo().search([
            ('customer_id', '=', customer.id)
        ])
        if not orders:
            return self.make_response(False, 400, [], None, [
                f'No orders found for {customer.name} - {customer.phone}',
                f'لم يتم العثور على الطلب المطلوب. {customer.name} - {customer.phone}'
            ])
        response_data = []
        for order in orders:
            response_data.append({
                'order_reference': order.name,
                'order_date': order.order_date.strftime('%Y-%m-%d'),
                'state': order.state,
                'total': order.total,
                'invoice_reference': order.invoice_ids[0].name if order.invoice_ids else '',
                'order_line': [{
                    'meal_id': line.meal_id.id,
                    'meal_name': line.meal_id.name,
                    'quantity': line.quantity
                } for line in order.meal_line_ids]
            })
        if response_data:
            return self.make_response(True, 200, [], response_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No data found.",
                "No data found."
            ])

    @validate_token
    @http.route('/eshop/payment_link/<mobile>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_eshop_order_payment_link(self, mobile):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile not passed.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone', '=', mobile)
        ], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم."
            ])
        order = request.env['diet.eshop.sale'].sudo().search([
            ('customer_id', '=', customer.id),
            ('state', '=', 'confirm'),
            ('invoice_status', '!=', 'not_invoiced'),
            ('payment_status', '=', 'not_paid')
        ], limit=1)
        if not order:
            return self.make_response(False, 400, [], None, [
                f'No order found for {customer.name} - {customer.phone}',
                f'لا توجد طلبات مسجلة. {customer.name} - {customer.phone}'
            ])
        invoice = order.invoice_ids.filtered(lambda post: post.state == 'posted')[0]
        data = [{
            'order_reference': order.name,
            'payment_reference': invoice.name,
            'transaction_url': invoice.tap_payment_transaction_url if invoice else '',
            'redirect_url': invoice.tap_payment_redirect_url if invoice else '',
            'payment_status_url': f'{base_url}/payment/status',
            'total': order.total,
        }]
        return self.make_response(True, 200, [], data, [])

    @validate_token
    @http.route('/dietitian', type='http', auth='public', methods=['GET'], csrf=False)
    def get_dietitian(self, **kwargs):
        dietitians = request.env['hr.employee'].sudo().search([('employee_type', '=', 'dietitian')])
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        dietitian_data = []
        for dietitian in dietitians:
            dietitian_dict = {
                'id': dietitian.id,
                'name': dietitian.name if dietitian.name else '',
                'arabic_name':dietitian.employee_arabic_name if dietitian.employee_arabic_name else '',
                'qualification': dietitian.study_field if dietitian.study_field else '',
                'qualification_arabic':dietitian.study_field_arabic if dietitian.study_field_arabic else '',
                'job_position': dietitian.job_title if dietitian.job_title else '',
                'job_position_arabic':dietitian.job_title_arabic if dietitian.job_title_arabic else '',
                'area_of_speciality': [speciality.name if speciality.name else '' for speciality in dietitian.area_of_speciality_ids],
                'area_of_speciality_arabic': [speciality.arabic_name if speciality.arabic_name else '' for speciality in dietitian.area_of_speciality_ids],
                'image': f'{base_url}/web/image?model=hr.employee&id={dietitian.id}&field=image_1920' if dietitian.image_1920 else '',
            }
            dietitian_data.append(dietitian_dict)
        return self.make_response(True, 200, [], dietitian_data, [])

    @validate_token
    @http.route('/dietitian/available/month', type='http', auth='public', methods=['GET'], csrf=False)
    def get_dietian_availablity(self, **kwargs):
        if not kwargs.get('dietitian_id', False):
            return self.make_response(False, 400, [], None, [
                'Dietitian ID not passed.',
                'Dietitian ID not passed.'
            ])
        if not kwargs.get('month', False):
            return self.make_response(False, 400, [], None, [
                'Month not passed.',
                'Month not passed.'
            ])
        if not kwargs.get('year', False):
            return self.make_response(False, 400, [], None, [
                'Year not passed.',
                'Year not passed.'
            ])
        dietitian_id = kwargs.get('dietitian_id')
        month = int(kwargs.get('month'))
        year = int(kwargs.get('year'))
        dietitian = request.env['hr.employee'].sudo().browse(int(dietitian_id))
        if not dietitian:
            return self.make_response(False, 400, [], None, [
                'Dietitian not found.',
                'لم يتم العثور على أخصائي التغذية.'
            ])
        availability = []
        start_date = datetime(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        end_date = datetime(year, month, last_day)
        while start_date <= end_date:
            available = False
            dietitian_available_days = dietitian.dietitian_available_days.mapped('name')
            dietitian_time_slots = dietitian.dietitian_time_slots.mapped('id')
            if start_date.strftime("%A") in dietitian_available_days:
                booked_slots = request.env['dietitian.appointment.history'].sudo().search([
                    ('dietitian_id', '=', dietitian.id),
                    ('date', '=', start_date.strftime('%Y-%m-%d')),
                    ('state', 'in', ['confirmed'])
                ])
                if booked_slots:
                    available_slots = list(set(dietitian_time_slots) - set(booked_slots.mapped('time_slot_id.id')))
                    if available_slots:
                        available = True
                else:
                    available = True
            else:
                available = False
            availability.append({
                'date': start_date.strftime('%Y-%m-%d'),
                'available': available
            })
            start_date += timedelta(days=1)
        return self.make_response(True, 200, [], availability, [])

    @validate_token
    @http.route('/dietitian/available/slots', type='http', auth='public', methods=['GET'], csrf=False)
    def get_dietitian_available_slots(self, **kwargs):
        if not kwargs.get('dietitian_id', False):
            return self.make_response(False, 400, [], None, [
                'Dietitian ID not passed.',
                'Dietitian ID not passed.'
            ])
        if not kwargs.get('date', False):
            return self.make_response(False, 400, [], None, [
                'Date not passed.',
                'يرجى إدخال التاريخ المطلوب.'
            ])
        dietitian_id = kwargs.get('dietitian_id')
        date = kwargs.get('date')
        dietitian = request.env['hr.employee'].sudo().browse(int(dietitian_id))
        if not dietitian:
            return self.make_response(False, 400, [], None, [
                'Dietitian not found.',
                'لم يتم العثور على أخصائي التغذية.'
            ])
        available_slots = []
        dietitian_available_days = dietitian.dietitian_available_days.mapped('name')
        dietitian_time_slots = dietitian.dietitian_time_slots.mapped('id')
        booked_slots = []
        if datetime.strptime(date, '%Y-%m-%d').strftime("%A") in dietitian_available_days:
            bookings = request.env['dietitian.appointment.history'].sudo().search([
                ('dietitian_id', '=', dietitian.id),
                ('date', '=', date),
                ('state', 'in', ['confirmed'])
            ])
            if bookings:
                booked_slots = bookings.mapped('time_slot_id').ids
        else:
            return self.make_response(False, 400, [], None, [
                'Dietitian not available on this day.',
                'أخصائي التغذية غير متاح في اليوم المطلوب.'
            ])
        for slot in dietitian_time_slots:
            time_slot = request.env['dietitian.time.slot'].sudo().browse(slot)
            available_slots.append({
                'id': time_slot.id,
                'name': time_slot.name,
                'status': 'available' if time_slot.id not in booked_slots else 'booked'
            })
        return self.make_response(True, 200, [], available_slots, [])

    @validate_token
    @http.route('/dietitian/book_slot', type='http', auth='public', methods=['POST'], csrf=False)
    def book_dietitian_slot(self):
        data = request.get_json_data()
        if not data.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        if not data.get('dietitian_id', False):
            return self.make_response(False, 400, [], None, [
                'Dietitian ID not passed.',
                'Dietitian ID not passed.'
            ])
        if not data.get('date', False):
            return self.make_response(False, 400, [], None, [
                'Date not passed.',
                'يرجى إدخال التاريخ المطلوب.'
            ])
        if not data.get('time_slot_id', False):
            return self.make_response(False, 400, [], None, [
                'Time Slot ID not passed.',
                'Time Slot ID not passed.'
            ])
        mobile = data.get('mobile')
        dietitian_id = data.get('dietitian_id')
        date = data.get('date')
        time_slot_id = data.get('time_slot_id')
        customer = request.env['res.partner'].sudo().search([
            ('phone','=',mobile)
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                "Customer with mobile {mobile} not found.",
                "Customer with mobile {mobile} not found."
            ])
        dietitian = request.env['hr.employee'].sudo().browse(int(dietitian_id))
        if not dietitian:
            return self.make_response(False, 400, [], None, [
                'Dietitian not found.',
                'لم يتم العثور على أخصائي التغذية.'
            ])
        time_slot = request.env['dietitian.time.slot'].sudo().browse(int(time_slot_id))
        if not time_slot:
            return self.make_response(False, 400, [], None, [
                'Time Slot not found.',
                'Time Slot not found.'
            ])
        dietitian_available_days = dietitian.dietitian_available_days.mapped('name')
        if datetime.strptime(date, '%Y-%m-%d').strftime("%A") not in dietitian_available_days:
            return self.make_response(False, 400, [], None, [
                'Dietitian not available on this day.',
                'أخصائي التغذية غير متاح في اليوم المطلوب.'
            ])
        appointment = request.env['dietitian.appointment.history'].sudo().create({
            'patient_id': customer.id,
            'dietitian_id': dietitian.id,
            'date': date,
            'time_slot_id': time_slot.id,
            'state': 'confirmed'
        })
        appointment.action_confirm()
        return self.make_response(True, 200, [
            'Slot booked successfully.',
            'تم حجز الموعد بنجاح.'
        ], None, [])

    @validate_token
    @http.route('/rewards/summary/<mobile>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_customer_rewards_summary(self, mobile):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile not passed.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone', '=', mobile)
        ], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} doesn't exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم."
            ])
        max_spin_count = request.env['ir.config_parameter'].sudo().get_param('diet.max_weekly_spins')
        if max_spin_count:
            max_spin_count = int(max_spin_count)
        else:
            max_spin_count = 0
        today = fields.Date.today()
        today_minus_7 = today - timedelta(days=7)
        this_week_spin_ids = request.env['weekly.spin.log'].sudo().search([
            ('customer_id', '=', customer.id),
            ('date', '>=', today_minus_7),
            ('date', '<=', today)
        ])
        total_spins_this_week = 0
        if this_week_spin_ids and max_spin_count:
            total_spins_this_week = max_spin_count if (len(this_week_spin_ids) >= max_spin_count) else len(this_week_spin_ids)
        remaining_spins = max_spin_count - total_spins_this_week
        if remaining_spins < 0:
            remaining_spins = 0
        rewards = request.env['customer.referrals'].sudo().search([
            ('customer_id', '=', customer.id)
        ], limit=1)
        reward_levels = request.env['referral.reward.levels'].sudo().search([], order='name asc')
        if not rewards:
            rewards_data = {
                'total_collected_points': 0,
                'current_points': 0,
                'level': 0,
                'level_stages': [{"level": "0", "value": "0", "eligible_items": []}] + [{
                    "level": level.name, 
                    "value": str(level.reward_amount),
                    "eligible_items": [
                        {
                            "id": item.id,
                            "name": item.name or "",
                            "arabic_name": item.arabic_name or "",
                            "description": item.description or "",
                            "arabic_description": item.arabic_meal_description or "",
                            "image": f"{base_url}/web/image?model=product.template&id={item.id}&field=image_1920" if item.image_1920 else ''
                        } for item in level.reward_eligible_item_ids
                    ]
                } for level in reward_levels],
                'friends_count': 0,
                'daily_spin_remaining_count': remaining_spins,
                'refferral_income': 0,
            }
            return self.make_response(False, 200, [], rewards_data, [])
        rewards_data = {
            'total_collected_points': rewards.total_received,
            'current_points': rewards.balance_amount,
            'level': rewards.reward_level_id.name,
            'level_stages': [{"level": "0", "value": "0", "eligible_items": []}] + [{
                "level": level.name, 
                "value": str(level.reward_amount),
                "eligible_items": [
                    {
                        "id": item.id,
                        "name": item.name or "",
                        "arabic_name": item.arabic_name or "",
                        "description": item.description or "",
                        "arabic_description": item.arabic_meal_description or "",
                        "image": f"{base_url}/web/image?model=product.template&id={item.id}&field=image_1920" if item.image_1920 else ''
                    } for item in level.reward_eligible_item_ids
                ]
            } for level in reward_levels],
            'friends_count': 0,
            'daily_spin_remaining_count': remaining_spins,
            'refferral_income': 0
        }
        return self.make_response(False, 200, [], rewards_data, [])

    @validate_token
    @http.route('/rewards/transactions/<mobile>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_customer_rewards_transactions(self, mobile):
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile not passed.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].sudo().search([
            ('phone', '=', mobile)
        ], limit=1)
        if not customer:
            return self.make_response(False, 400, [], None, [
                "Customer with mobile {mobile} doesn't exist.",
                "لا يوجد عميل مرتبط بهذا الرقم."
            ])
        rewards = request.env['customer.referrals'].sudo().search([
            ('customer_id', '=', customer.id)
        ], limit=1)
        if not rewards:
            return self.make_response(False, 400, [], None, [
                f"No rewards found for {customer.name} - {customer.phone}",
                f"لم يتم العثور على مكافآت متاحة. {customer.name} - {customer.phone}"
            ])
        transactions = rewards.received_ids
        transaction_data = []
        for transaction in transactions:
            transaction_data.append({
                'date': transaction.create_date.strftime('%Y-%m-%d'),
                'amount': transaction.amount,
                'type': transaction.wallet_type.name,
                'description': transaction.remarks
            })
        return self.make_response(False, 200, [], transaction_data, [])

    @validate_token
    @http.route('/rewards/wheel/items', type='http', auth='public', methods=['GET'], csrf=False)
    def get_rewards_wheel_items(self):
        wheel_items = request.env['offer.wheel'].sudo().search([])
        if not wheel_items:
            return self.make_response(False, 400, [], None, [
                "No items found.",
                "No items found."
            ])
        items_data = []
        for item in wheel_items:
            items_data.append({
                'id': item.id,
                'name': item.name,
                'reward_amount': item.reward_amount,
            })
        return self.make_response(True, 200, [], items_data, [])

    @validate_token
    @http.route('/rewards/wheel/spin', type='http', auth='public', methods=['POST'], csrf=False)
    def spin_rewards_wheel(self):
        data = request.get_json_data()
        if not data.get('mobile', False):
            return self.make_response(False, 400, [], None, [
                'Mobile not passed.',
                'يرجى إدخال رقم الجوال.'
            ])
        if not data.get('wheel_item_id', False):
            return self.make_response(False, 400, [], None, [
                'Wheel Item ID not passed.',
                'Wheel Item ID not passed.'
            ])
        mobile = data.get('mobile')
        wheel_item_id = data.get('wheel_item_id')
        customer = request.env['res.partner'].sudo().search([
            ('phone','=',mobile)
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} not found.",
                f"Customer with mobile {mobile} not found."
            ])
        wheel_item = request.env['offer.wheel'].sudo().browse(int(wheel_item_id))
        if not wheel_item:
            return self.make_response(False, 400, [], None, [
                'Wheel Item not found.',
                'Wheel Item not found.'
            ])
        rewards = request.env['customer.referrals'].sudo().search([
            ('customer_id', '=', customer.id)
        ], limit=1)
        if not rewards:
            rewards = request.env['customer.referrals'].create({'customer_id': customer.id})
        rewards.received_ids.create({
            'referral_id': rewards.id,
            'amount': wheel_item.reward_amount,
            'wallet_type': request.env.ref('diet.offer_wheel_reward_type').id,
            'remarks': f"Reward received for spinning the wheel."
        })
        max_spin_count = request.env['ir.config_parameter'].sudo().get_param('diet.max_weekly_spins')
        if max_spin_count:
            max_spin_count = int(max_spin_count)
        else:
            max_spin_count = 0
        today = fields.Date.today()
        today_minus_7 = today - timedelta(days=7)
        this_week_spin_ids = request.env['weekly.spin.log'].sudo().search([
            ('customer_id', '=', customer.id),
            ('date', '>=', today_minus_7),
            ('date', '<=', today)
        ])
        total_spins_this_week = 0
        if this_week_spin_ids and max_spin_count:
            total_spins_this_week = max_spin_count if (len(this_week_spin_ids) >= max_spin_count) else len(this_week_spin_ids)
        remaining_spins = max_spin_count - total_spins_this_week
        if remaining_spins < 0:
            remaining_spins = 0
        if not remaining_spins:
            return self.make_response(True, 400, [
                "Spins limit exhausted for this week.",
                "Spins limit exhausted for this week."
            ], None, [
                "Spins limit exhausted for this week.",
                "Spins limit exhausted for this week."
            ])
        request.env['weekly.spin.log'].sudo().create({
            'date': fields.Date.today(),
            'customer_id': customer.id,
            'wheel_item_id': wheel_item.id
        })
        return self.make_response(True, 200, [
            "Wheel spun successfully.",
            "تم تدوير العجلة بنجاح."
        ], None, [])

    @validate_token
    @http.route('/delivery_status', type='http', auth='public', methods=['GET'], csrf=False)
    def delivery_status(self, **kwargs):
        mobile = kwargs.get('mobile', False)
        delivery_date_str = kwargs.get('date', False)
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.",
                "يرجى إدخال رقم الجوال."
            ])
        try:
            delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
        except Exception as e:
            return self.make_response(False, 400, [], None, [
                'Invalid date format. Send date in YYYY-MM-DD format.',
                'صيغة التاريخ غير صحيحة. يرجى استخدام صيغة YYYY-MM-DD.'
            ])
        customer = request.env['res.partner'].search([
            ('phone', '=', mobile)
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} does not exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم. {mobile}"
            ])
        driver_order = request.env['driver.order'].sudo().search([
            ('customer_id', '=', customer.id),
            ('date', '=', delivery_date)
        ], limit=1)
        response_message = []
        if not driver_order:
            response_message.append({"status": "cooking"})
        elif driver_order.status == "pending":
            response_message.append({"status": "delivery"})
        elif driver_order.status == "delivered":
            response_message.append({"status": "delivered"})
        if response_message:
            return self.make_response(True, 200, [], response_message, [])
        else:
            return self.make_response(False, 400, [], None, [
                "Contact customer care.",
                "Contact customer care."
            ])

    @validate_token
    @http.route('/customer/invoices/<mobile>', type='http', auth='public', methods=['GET'], csrf=False)
    def customer_invoices(self, mobile, **kwargs):
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.",
                "يرجى إدخال رقم الجوال."
            ])
        customer = request.env['res.partner'].search([
            ('phone', '=', mobile)
        ])
        if not customer:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile {mobile} does not exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم. {mobile}"
            ])
        invoices = request.env['account.move'].sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('partner_id', '=', customer.id),
            ('customer_so_line_id', '!=', False)
        ])
        invoice_data = []
        for inv in invoices:
            subscription_name = ""
            if inv.customer_so_line_id.plan_id and inv.customer_so_line_id.plan_id.name:
                subscription_name = inv.customer_so_line_id.plan_id.name
            inv_data = {
                "name": inv.partner_id.full_name or "",
                "date": inv.invoice_date.strftime('%d %B %Y') or "",
                "subscription_name": subscription_name or "",
                "invoice_id": inv.name or "",
                "invoice_ref": inv.customer_so_line_id.order_number or "",
                "created_date": inv.create_date.strftime("%B %d, %Y %H:%M %p") or "",
                "expiry_date": inv.invoice_date_due.strftime("%B %d, %Y") or "",
                "mobile": inv.partner_id.phone or "",
                "email": inv.partner_id.email or "",
                "customer_ref": inv.partner_id.customer_sequence_no or "",
                "diet_package": f"{inv.amount_total:.2f} {inv.currency_id.symbol}",
                "balance": f"{inv.amount_residual:.2f} {inv.currency_id.symbol}",
                "total": f"{inv.amount_total:.2f} {inv.currency_id.symbol}",
                "service_charge": f"0 {inv.currency_id.symbol}",
                "grand_total": f"{inv.amount_total:.2f} {inv.currency_id.symbol}",
            }
            invoice_data.append(inv_data)
        if invoice_data:
            return self.make_response(True, 200, [], invoice_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No data found.",
                "No data found."
            ])

    @validate_token
    @http.route('/set_favourite_meal', type='http', auth='public', methods=['PATCH'], csrf=False)
    def set_favourite_meal(self, **data_passed):
        data_passed = request.get_json_data()
        if 'mobile' not in data_passed or not data_passed['mobile']:
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.",
                "يرجى إدخال رقم الجوال."
            ])
        if 'meal_id' not in data_passed or not data_passed['meal_id']:
            return self.make_response(False, 400, [], None, [
                "Meal not given.",
                "لم يتم إدخال بيانات الوجبات."
            ])
        meal_id = int(data_passed['meal_id'])
        customer_id = request.env['res.partner'].sudo().search([('phone','=',data_passed['mobile'])],limit=1)
        if not customer_id:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile number {data_passed['mobile']} does not exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم. {data_passed['mobile']}"
            ])
        meal_rec_id = request.env['product.template'].sudo().search([
            ('is_meal','=',True),
            ('id','=',meal_id)    
        ],limit=1)
        if not meal_rec_id:
            return self.make_response(False, 400, [], None, [
                f"Meal does not exist.",
                f"Meal does not exist."
            ])
        if meal_rec_id in customer_id.favourite_meals_ids:
            return self.make_response(False, 400, [], None, [
                f"Meal is already in favourite.",
                f"Meal is already in favourite."
            ])
        else:
            customer_id.favourite_meals_ids = [(4, meal_id)]
            return self.make_response(True, 200, [], None, [])
        
    @validate_token
    @http.route('/remove_favourite_meal', type='http', auth='public', methods=['PATCH'], csrf=False)
    def remove_favourite_meal(self, **data_passed):
        data_passed = request.get_json_data()
        if 'mobile' not in data_passed or not data_passed['mobile']:
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.",
                "يرجى إدخال رقم الجوال."
            ])
        if 'meal_id' not in data_passed or not data_passed['meal_id']:
            return self.make_response(False, 400, [], None, [
                "Meal not given.",
                "لم يتم إدخال بيانات الوجبات."
            ])
        meal_id = int(data_passed['meal_id'])
        customer_id = request.env['res.partner'].sudo().search([('phone','=',data_passed['mobile'])],limit=1)
        if not customer_id:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile number {data_passed['mobile']} does not exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم. {data_passed['mobile']}"
            ])
        meal_rec_id = request.env['product.template'].sudo().search([
            ('is_meal','=',True),
            ('id','=',meal_id)    
        ],limit=1)
        if not meal_rec_id:
            return self.make_response(False, 400, [], None, [
                f"Meal does not exist.",
                f"Meal does not exist."
            ])
        if meal_rec_id in customer_id.favourite_meals_ids:
            customer_id.favourite_meals_ids = [(3, meal_id)]
            return self.make_response(True, 200, [], None, [])
        else:
            return self.make_response(False, 400, [], None, [
                f"Meal is not favourite.",
                f"Meal is not favourite."
            ])
        
    @validate_token
    @http.route('/favourite_meals/<mobile>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_favourite_meal(self, mobile, **data_passed):
        if not mobile:
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.",
                "يرجى إدخال رقم الجوال."
            ])
        customer_id = request.env['res.partner'].sudo().search([('phone','=',mobile)],limit=1)
        if not customer_id:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile number {data_passed['mobile']} does not exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم. {data_passed['mobile']}"
            ])
        meal_data = []
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for meal in customer_id.favourite_meals_ids:
            meal_data.append({
                'id': meal.id,
                'tags': ', '.join(meal.meal_tag_id.mapped('name')) if meal.meal_tag_id else '',
                'name': meal.name,
                'arabic_name': meal.arabic_name,
                'description': meal.meal_description,
                'arabic_description': meal.arabic_meal_description,
                'image': f"{base_url}/web/image?model=product.template&id={meal.id}&field=image_1920",
                'tags': ', '.join(meal.meal_tag_id.mapped('name')) if meal.meal_tag_id else ''
            })
        if meal_data:
            return self.make_response(True, 200, [], meal_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                "No data found",
                "No data found"
            ])
        
    @validate_token
    @http.route('/reward_item_purchase', type='http', auth='public', methods=['POST'], csrf=False)
    def reward_item_purchase(self, **data_passed):
        data_passed = request.get_json_data()
        if 'mobile' not in data_passed or not data_passed['mobile']:
            return self.make_response(False, 400, [], None, [
                "Mobile number not given.",
                "يرجى إدخال رقم الجوال."
            ])
        if 'meal_id' not in data_passed or not data_passed['meal_id']:
            return self.make_response(False, 400, [], None, [
                "Meal not given.",
                "لم يتم إدخال بيانات الوجبات."
            ])
        meal_id = int(data_passed['meal_id'])
        customer_id = request.env['res.partner'].sudo().search([('phone','=',data_passed['mobile'])],limit=1)
        if not customer_id:
            return self.make_response(False, 400, [], None, [
                f"Customer with mobile number {data_passed['mobile']} does not exist.",
                f"لا يوجد عميل مرتبط بهذا الرقم. {data_passed['mobile']}"
            ])
        meal_rec_id = request.env['product.template'].sudo().search([
            ('is_meal','=',True),
            ('id','=',meal_id)    
        ],limit=1)
        if not meal_rec_id:
            return self.make_response(False, 400, [], None, [
                f"Meal does not exist.",
                f"Meal does not exist."
            ])
        cart = request.env['diet.eshop.sale'].sudo().create({
            'customer_id': customer_id.id
        })
        cart._compute_available_points()
        cart_line = request.env['diet.eshop.sale.line'].sudo().create({
            'meal_id': meal_rec_id.id,
            'quantity': 1,
            'order_id': cart.id
        })
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        cart_line._onchange_meal_id()
        if cart.available_points > cart.total:
            cart.apply_reward_points()
            cart.action_confirm()
            response_data = {
                'order_reference':cart.name if cart.name else ''
            }
            return self.make_response(True, 200, [
                "Order placed successfully",
                "تم تسجيل الطلب بنجاح."
            ], response_data, [])
        else:
            return self.make_response(False, 400, [], None, [
                f"Not enough reward points.",
                f"النقاط غير كافية للحصول على مكافآت."
            ])

    @validate_token
    @http.route('/shift', type='http', auth='public', methods=['GET'], csrf=False)
    def get_shift(self):
        shifts = request.env['customer.shift'].sudo().search([])
        data = [{
            'id': shift.id,
            'name': shift.shift,
            'arabic_name': shift.arabic_name
        } for shift in shifts]
        return self.make_response(True, 200, [], data, [])

    @validate_token
    @http.route('/delete_account/<mobile>', type='http', auth='public', method=['GET'], csrf=False)
    def delete_account(self, mobile, **kwargs):
        if not mobile:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": ["Mobile not passed.", "يرجى إدخال رقم الجوال."]
            }), headers=[('Content-Type', 'application/json')])
        check_existing_query = f"""SELECT active FROM res_partner WHERE phone='{mobile}'"""
        request.env.cr.execute(check_existing_query)
        existing_customer = request.env.cr.dictfetchone()
        if not existing_customer:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": [f"Customer with mobile number {mobile} doesn't exist.", f"Customer with mobile number {mobile} doesn't exist."]
            }), headers=[('Content-Type', 'application/json')])
        archive_customer_query = f"""UPDATE res_partner SET active=false WHERE phone='{mobile}'"""
        request.env.cr.execute(archive_customer_query)   
        check_archive_query = f"""SELECT active FROM res_partner WHERE phone='{mobile}'"""
        request.env.cr.execute(check_archive_query)
        check_archive_res = request.env.cr.dictfetchone()
        if not check_archive_res.get('active', False):
            return request.make_response(json.dumps({
                "statusOk": True,
                "statusCode": 200,
                "message": ["Account deleted successfully.", "تم حذف الحساب بنجاح."],
                "payload": [],
                "error": []
            }), headers=[('Content-Type', 'application/json')])
        else:
            return request.make_response(json.dumps({
                "statusOk": True,
                "statusCode": 200,
                "message": ["Account deleted failed. Contact customer care.", "فشل في عملية حذف الحساب، يرجى التواصل مع خدمة العملاء."],
                "payload": [],
                "error": []
            }), headers=[('Content-Type', 'application/json')])

    @validate_token
    @http.route('/delete_driver/<mobile>', type='http', auth='public', method=['GET'], csrf=False)
    def delete_account(self, mobile, **kwargs):
        if not mobile:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": ["Mobile not passed.", "يرجى إدخال رقم الجوال."]
            }), headers=[('Content-Type', 'application/json')])
        check_existing_query = f"""SELECT active FROM area_driver WHERE phone='{mobile}'"""
        request.env.cr.execute(check_existing_query)
        existing_customer = request.env.cr.dictfetchone()
        if not existing_customer:
            return request.make_response(json.dumps({
                "statusOk": False,
                "statusCode": 400,
                "message": [],
                "payload": [],
                "error": [f"Driver with mobile number {mobile} doesn't exist.", f"السائق المطلوب غير موجود. {mobile}"]
            }), headers=[('Content-Type', 'application/json')])
        archive_customer_query = f"""UPDATE area_driver SET active=false WHERE phone='{mobile}'"""
        request.env.cr.execute(archive_customer_query)   
        check_archive_query = f"""SELECT active FROM area_driver WHERE phone='{mobile}'"""
        request.env.cr.execute(check_archive_query)
        check_archive_res = request.env.cr.dictfetchone()
        if not check_archive_res.get('active', False):
            return request.make_response(json.dumps({
                "statusOk": True,
                "statusCode": 200,
                "message": ["Account deleted successfully.", "تم حذف الحساب بنجاح."],
                "payload": [],
                "error": []
            }), headers=[('Content-Type', 'application/json')])
        else:
            return request.make_response(json.dumps({
                "statusOk": True,
                "statusCode": 200,
                "message": ["Account deleted failed. Contact customer care.", "فشل في عملية حذف الحساب، يرجى التواصل مع خدمة العملاء."],
                "payload": [],
                "error": []
            }), headers=[('Content-Type', 'application/json')])
        
    @validate_token
    @http.route('/terms_conditions', auth='public', type='http', method=['GET'])
    def get_terms_conditions(self):
        terms_data = [{
            "english": [],
            "arabic": []
        }]
        for term in request.env.company.terms_and_conditions_ids:
            terms_data[0]['english'].append({
                'heading': term.heading if term.heading else '',
                'description': term.description if term.description else '',
            })
        for term in request.env.company.arabic_terms_and_conditions_ids:
            terms_data[0]['arabic'].append({
                'heading': term.heading if term.heading else '',
                'description': term.description if term.description else '',
            })
        return self.make_response(True, 200, [], terms_data, [])
    
    @validate_token
    @http.route('/street', type='http', auth='public', methods=['POST'], csrf=False)
    def create_street(self, **kwargs):
        kwargs = request.get_json_data()
        district_id = kwargs.get('district_id')
        street_name = kwargs.get('street', '').strip().lower()
        arabic_name = kwargs.get('arabic_street', '').strip()

        if not district_id:
            return self.make_response(False, 400, [], None, ['District ID not passed.'])
        
        if not street_name and not arabic_name:
            return self.make_response(False, 400, [], None, ['Either Street name or Arabic name not passed.'])

        existing_street = request.env['customer.street'].sudo().search([
            '|', 
            ('name', 'ilike', street_name if street_name != '' else 'False'),
            ('arabic_name', 'ilike', arabic_name if arabic_name != '' else 'False'),
            ('district_id', '=', district_id)
        ], limit=1)

        if existing_street:
            return self.make_response(True, 200, ['Street already exists.', 'الشارع موجود بالفعل.'], {'id': existing_street.id}, [])

        try:
            new_street = request.env['customer.street'].sudo().create({
                'name': street_name,
                'arabic_name': arabic_name,
                'district_id': district_id
            })
            return self.make_response(True, 200, ['Street Created.', 'تم إنشاء الشارع.'], {'id': new_street.id}, [])
        except Exception as e:
            return self.make_response(False, 400, [], None, [f'Error: {str(e)}'])
        
    @validate_token
    @http.route('/buffer_time', type='http', auth='public', methods=['GET'], csrf=False)
    def buffer_time(self, **kwargs):
        buffer_before_4_30 = request.env['ir.config_parameter'].sudo().get_param('diet.buffer_before_4_30', 0)
        buffer_after_4_30 = request.env['ir.config_parameter'].sudo().get_param('diet.buffer_after_4_30', 0)
        is_wednesday = request.env['ir.config_parameter'].sudo().get_param('diet.is_wednesday', False)
        wednesday_buffer_before_4_30 = request.env['ir.config_parameter'].sudo().get_param('diet.wednesday_buffer_before_4_30', 0)
        wednesday_buffer_after_4_30 = request.env['ir.config_parameter'].sudo().get_param('diet.wednesday_buffer_after_4_30', 0)
        data = {
            'buffer_before_4_30': int(buffer_before_4_30) if buffer_before_4_30 else 0,
            'buffer_after_4_30': int(buffer_after_4_30) if buffer_after_4_30 else 0,
            'is_wednesday': is_wednesday,
            'wednesday_buffer_before_4_30': int(wednesday_buffer_before_4_30) if wednesday_buffer_before_4_30 else 0,
            'wednesday_buffer_after_4_30': int(wednesday_buffer_after_4_30) if wednesday_buffer_after_4_30 else 0
        }
        return self.make_response(True, 200, [], data, [])

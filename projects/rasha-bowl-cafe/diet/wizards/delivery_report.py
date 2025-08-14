from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, date, datetime
from calendar import monthrange
import calendar
import base64
import logging
from io import BytesIO
import pdfkit
import pytz

_logger = logging.getLogger(__name__)

class DeliveryReport(models.TransientModel):
    _name = "delivery.report.wizard"
    _description = "Wizard for Delivery Report"

    date = fields.Date("Date",default=fields.Date.today())
    status = fields.Selection([
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('not_delivered', 'Not Delivered'),
        ('all','All')
    ], string='Status', default='all')
    shift_id = fields.Many2one('customer.shift', string='Shift')
    customer_tag_ids = fields.Many2many('res.partner.category', string='Customer Tag')
    report_type = fields.Selection([
        ('delivery_sticker', 'Delivery Sticker'),
        ('delivery_report', 'Delivery Report'),
        ('delivery_report_with_dislikes', 'Delivery Report with Dislikes'),
        ('delivery_report_without_dislikes', 'Delivery Report without Dislikes'),
        ('export', 'Export')
    ], string='Report Type', default='delivery_sticker')
    report_attachment_id = fields.Many2one('ir.attachment', string='Report Attachment')
    error_check_detail = fields.Html('Error Check Details')
    is_driver_order_generated = fields.Boolean('Driver Order Generated', compute='_compute_is_driver_order_generated')

    @api.depends('date')
    def _compute_is_driver_order_generated(self):
        driver_order_ids = self.env['driver.order'].search([('date', '=', self.date)])
        if driver_order_ids:
            self.is_driver_order_generated = True
        else:
            self.is_driver_order_generated = False

    # check the validity of the report data going to be added to the report
    # all meal calendar entries should have valid meals selected by the customer
    def check_validity(self):
        domain = [
            ('date', '=', self.date),
            ('state', 'in', ['active', 'active_with_meal']),
            '|',
            '|',
            '|',
            '|',
            '|',
            ('meal_id', '=', False),
            ('address_id', '=', False),
            ('address_id.district_id', '=', False),
            ('address_id.state_id', '=', False),
            ('address_id.street', '=', False),
            ('shift_id', '=', False)
        ]
        
        error_meal_calendar_ids = self.env['customer.meal.calendar'].search(domain)
        if error_meal_calendar_ids:
            # check if there is any available address or shift, then assign that address or shift to the meal calendar entry
            for entry in error_meal_calendar_ids:
                order = entry.so_id
                if not entry.address_id or not entry.shift_id:
                    day_of_date = str(entry.date.weekday())
                    day_shifts = order.partner_id.shift_ids.filtered(lambda shift:
                        shift.period=='day_of_week'
                    )
                    schedule_line = False
                    shift = False
                    address = False
                    if not schedule_line:
                        schedule_line = day_shifts.filtered(lambda shift:
                            shift.day_of_week == 'day_of_date'
                        )
                        shift = schedule_line.shift_type if schedule_line else False
                        address = schedule_line.address_id if schedule_line else False
                    if not schedule_line:
                        range_shifts = order.partner_id.shift_ids.filtered(lambda shift:
                            shift.period=='date_range'
                        )
                        schedule_line = range_shifts.filtered(lambda shift:
                            shift.from_date <= entry.date <= shift.to_date
                        )
                        shift = schedule_line.shift_type if schedule_line else False
                        address = schedule_line.address_id if schedule_line else False
                    if not schedule_line:
                        shift = order.partner_id.customer_address_id.shift_id if order.partner_id.customer_address_id else False
                        address = order.partner_id.customer_address_id
                    update_vals = {}
                    if not entry.address_id:
                        update_vals['address_id'] = address.id if address else False
                    if not entry.shift_id:
                        update_vals['shift_id'] = shift.id if shift else False
                    if update_vals:
                        entry.write(update_vals)

        error_meal_calendar_ids = self.env['customer.meal.calendar'].search(domain)
        error_meal_calendar_ids = error_meal_calendar_ids.filtered(lambda x: x.so_id.state == 'in_progress')
        if error_meal_calendar_ids:
            meal_table_html = f"""
                <p>Hi,<br/>There meal selection is not proper for the following customers. Please check and update the meal selection.</p>
                <br/>
                <p>Meal Generated for Date: <b>{self.date.strftime('%d-%m-%Y')}</b></p>
                <br/>
                <table width="100%" cellpadding="5" style="border: 1px solid black; border-collapse: collapse;">
                    <thead>
                        <tr style="text-align:center">
                            <th style="border: 1px solid black; border-collapse: collapse;">Customer ID</th>
                            <th style="border: 1px solid black; border-collapse: collapse;">Name</th>
                            <th style="border: 1px solid black; border-collapse: collapse;">Meal Category</th>
                            <th style="border: 1px solid black; border-collapse: collapse;">Meal</th>
                            <th style="border: 1px solid black; border-collapse: collapse;">Meal Selection By</th>
                            <th style="border: 1px solid black; border-collapse: collapse;">City</th>
                            <th style="border: 1px solid black; border-collapse: collapse;">District</th>
                            <th style="border: 1px solid black; border-collapse: collapse;">Street</th>
                            <th style="border: 1px solid black; border-collapse: collapse;">Shift</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for entry in error_meal_calendar_ids:
                meal_name = entry.meal_id.name if entry.meal_id else 'Not Selected'
                district = entry.address_id.district_id.name if entry.address_id.district_id and entry.address_id.district_id.name else 'Not Selected'
                city = entry.address_id.state_id.name if entry.address_id.state_id and entry.address_id.state_id.name else 'Not Selected'
                street = entry.address_id.street if entry.address_id.street else 'Not Selected'
                shift = entry.shift_id.shift if entry.shift_id and entry.shift_id.shift else 'Not Selected'
                if meal_name == 'Not Selected':
                    meal_name = f'<span style="color: red; font-weight: bold;">{meal_name}</span>'
                if district == 'Not Selected':
                    district = f'<span style="color: red; font-weight: bold;">{district}</span>'
                if city == 'Not Selected':
                    city = f'<span style="color: red; font-weight: bold;">{city}</span>'
                if street == 'Not Selected':
                    street = f'<span style="color: red; font-weight: bold;">{street}</span>'
                if shift == 'Not Selected':
                    shift = f'<span style="color: red; font-weight: bold;">{shift}</span>'
                meal_table_html += f"""
                    <tr style="text-align:right">
                        <td style="border: 1px solid black; border-collapse: collapse; text-align: center;">{entry.partner_id.customer_sequence_no}</td>
                        <td style="border: 1px solid black; border-collapse: collapse; text-align: left;">{entry.partner_id.name} {entry.partner_id.last_name}</td>
                        <td style="border: 1px solid black; border-collapse: collapse; text-align: left">{entry.meal_category_id.name}</td>
                        <td style="border: 1px solid black; border-collapse: collapse; text-align: left;">
                            {meal_name}
                        </td>
                        <td style="border: 1px solid black; border-collapse: collapse; text-align: center;">{entry.meal_selection_by.capitalize()}</td>
                        <td style="border: 1px solid black; border-collapse: collapse; text-align: center;">
                            {city}
                        </td>
                        <td style="border: 1px solid black; border-collapse: collapse; text-align: center;">
                            {district}
                        </td>
                        <td style="border: 1px solid black; border-collapse: collapse; text-align: center;">
                            {street}
                        </td>
                        <td style="border: 1px solid black; border-collapse: collapse; text-align: center;">
                            {shift}
                        </td>
                    </tr>
                """
            meal_table_html += """
                    </tbody>
                </table>
            """
            return {
                "type": "ir.actions.act_window",
                "res_model": "delivery.report.wizard",
                "view_mode": "form",
                "context": {
                    "default_date": self.date,
                    "default_report_type": self.report_type,
                    "default_shift_id": self.shift_id.id,
                    "default_customer_tag_ids": self.customer_tag_ids.ids,
                    "default_status": self.status,
                    "default_error_check_detail": meal_table_html
                },
                "target": "new"
            }
        else:
            driver_order_ids = self.env['driver.order'].search([('date', '=', self.date)])
            if driver_order_ids:
                driver_order_ids.unlink()

            meal_calendar_ids = self.env['customer.meal.calendar'].search([
                ('date', '=', self.date),
                ('state', 'in', ['active', 'active_with_meal']),
                ('driver_order_id', '=', False)
            ])
            if not meal_calendar_ids:
                raise ValidationError(_("No data found"))
            meal_calendar_ids = meal_calendar_ids.filtered(lambda x: x.so_id.state == 'in_progress')
            meal_calendar_ids = meal_calendar_ids.sorted(key=lambda x: (x.shift_id.shift, x.address_id.district_id.zone_id.name, x.address_id.district_id.name, x.address_id.street, x.partner_id))
            partner_ids = meal_calendar_ids.mapped('partner_id')
            queue_no = 1
            for partner in partner_ids:
                partner_entries = meal_calendar_ids.filtered(lambda x: x.partner_id == partner)
                if partner_entries:
                    day_of_date = str(self.date.weekday())
                    day_shifts = partner.shift_ids.filtered(lambda shift:
                        shift.period=='day_of_week'
                    )
                    schedule_line = False
                    shift = False
                    address_id = False
                    if not schedule_line:
                        schedule_line = day_shifts.filtered(lambda shift:
                            shift.day_of_week == day_of_date
                        )
                        shift = schedule_line.shift_type if schedule_line else False
                        address_id = schedule_line.address_id if schedule_line else False
                    if not schedule_line:
                        range_shifts = partner.shift_ids.filtered(lambda shift:
                            shift.period=='date_range'
                        )
                        schedule_line = range_shifts.filtered(lambda shift:
                            shift.from_date <= self.date <= shift.to_date
                        )
                        shift = schedule_line.shift_type if schedule_line else False
                        address_id = schedule_line.address_id if schedule_line else False
                    if not schedule_line:
                        shift = partner.customer_address_id.shift_id if partner.customer_address_id else False
                        address_id = partner.customer_address_id
                    if partner_entries[0].so_id.customer_address_id:
                        address_id = partner_entries[0].so_id.customer_address_id
                    driver_id = False
                    if address_id:
                        driver_id = address_id.district_id.zone_id.driver_ids[0] if address_id.district_id.zone_id.driver_ids else False
                    default_shift_id = self.env['customer.shift'].search([('is_default', '=', True)])
                    if not default_shift_id:
                        default_shift_id = False
                    else:
                        default_shift_id = default_shift_id[0].id
                    driver_order_id = self.env['driver.order'].create({
                        'driver_id': driver_id.id if driver_id else False,
                        'date': self.date,
                        'status': 'pending',
                        'address_id': address_id.id if address_id else False,
                        'shift_id': shift.id if shift else default_shift_id,
                        'customer_id': partner.id,
                        'subscription_id': partner_entries[0].so_id.id if partner_entries[0].so_id else False,
                        'delivery_queue_number': queue_no
                    })
                    partner_entries.write({'driver_order_id': driver_order_id.id})
                    queue_no += 1            
            
            return {
                "type": "ir.actions.act_window",
                "res_model": "delivery.report.wizard",
                "view_mode": "form",
                "context": {
                    "default_date": self.date,
                    "default_report_type": self.report_type,
                    "default_shift_id": self.shift_id.id,
                    "default_customer_tag_ids": self.customer_tag_ids.ids,
                    "default_status": self.status
                },
                "target": "new"   
            }     
            

    def export(self):
        domain = [
            ('date', '=', self.date),
            ('meal_calendar_ids', '=', False)
        ]
        if self.status:
            if self.status == 'pending':
                domain.append(('status', '=', 'pending'))
            elif self.status == 'delivered':
                domain.append(('status', '=', 'delivered'))
            elif self.status == 'not_delivered':
                domain.append(('status', '=', 'not_delivered'))
            else:
                domain.append(('status', 'in', ['pending', 'delivered', 'not_delivered']))
        if self.shift_id:
            domain.append(('shift_id', '=', self.shift_id.id))
        driver_order_without_meal_calendar_ids = self.env['driver.order'].search(domain)
        final_driver_order_without_meal_calendar = self.env['driver.order']
        for driver_order in driver_order_without_meal_calendar_ids:
            do_meal_calendar_ids = self.env['customer.meal.calendar'].search([
                ('date', '=', self.date),
                ('driver_order_id', '=', False),
                ('partner_id', '=', driver_order.customer_id.id),
                ('so_id', '=', driver_order.subscription_id.id)
            ])
            if do_meal_calendar_ids:
                do_meal_calendar_ids.write({'driver_order_id': driver_order.id})
            else:
                final_driver_order_without_meal_calendar |= driver_order
        if final_driver_order_without_meal_calendar:
            customer_names = [f"[{customer.customer_sequence_no}] {customer.full_name}" for customer in final_driver_order_without_meal_calendar.mapped('customer_id')]
            customer_names_final = [f'{index + 1}. {name}' for index, name in enumerate(customer_names)]
            raise UserError(_("Driver orders do not have meal details (Meal calendar not linked to driver orders) for the following customers:\n\n"+'\n'.join(customer_names_final)+"\n\nPlease link the meal calendar entries to the driver orders and try again or contact support."))

        data = {
            "date": self.date,
            "status": self.status,
            "shift_id": self.shift_id.id,
            "customer_tag_ids": self.customer_tag_ids.ids,
            "report_type": self.report_type
        }

        if self.report_type in ['delivery_report', 'delivery_report_with_dislikes', 'delivery_report_without_dislikes']:
            pdf_content = self.env['ir.actions.report'].with_context(force_report_rendering=True)._render_qweb_pdf('diet.meals_delivery_report_action', data=data)
            attachment_id = self.env['ir.attachment'].create({
                'name': 'Delivery Report',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content[0]).decode('utf-8'),
                'mimetype': 'application/pdf',
                'is_delivery_report_file': True
            })
            if attachment_id:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/content/%s?download=true' % attachment_id.id,
                    'target': 'self',
                }
        elif self.report_type == 'export':
            return self.env.ref("diet.action_delivery_report").report_action(self, data=data, config=False)
        elif self.report_type == 'delivery_sticker':
            report_data = []
            query_params = [self.date.strftime('%Y-%m-%d')]
            query = """
                SELECT
                    partner.id AS partner_id,
                    partner.full_name AS name,
                    partner.customer_sequence_no AS customer_no,
                    partner.phone AS phone,
                    drv_order.delivery_queue_number AS queue_number,
                    drv_order.date AS date,
                    plan.short_code AS plan_code,
                    subscription.order_number AS order_number,
                    subscription.pc_combination AS pc_combination,
                    district.name AS district,
                    zone.name AS zone,
                    city.name AS city,
                    street AS street,
                    address.house_number AS house_no,
                    address.floor_number AS floor_no,
                    address.apartment_no AS apartment_no,
                    shift.shift AS shift,
                    subscription.actual_start_date AS start_date,
                    subscription.end_date AS end_date,
                    subscription.id AS subscription_id,
                    drv_order.id AS order_id
                FROM
                    driver_order AS drv_order
                JOIN res_partner AS partner ON drv_order.customer_id = partner.id
                JOIN diet_subscription_order AS subscription ON drv_order.subscription_id = subscription.id
                JOIN subscription_package_plan AS plan ON subscription.plan_id = plan.id
                JOIN res_partner AS address ON address.id = drv_order.address_id
                JOIN customer_district AS district ON district.id = address.district_id
                JOIN res_country_state AS city ON city.id = address.state_id
                JOIN customer_shift AS shift ON shift.id = drv_order.shift_id
                LEFT JOIN customer_zone AS zone ON zone.id = district.zone_id

                WHERE
                    drv_order.date = %s
            """
            if self.shift_id:
                query += " AND drv_order.shift_id = %s"
                query_params.append(self.shift_id.id)
            if self.status:
                if self.status == 'pending':
                    delivery_status = ['pending']
                elif self.status == 'delivered':
                    delivery_status = ['delivered']
                elif self.status == 'not_delivered':
                    delivery_status = ['not_delivered']
                else:
                    delivery_status = ['pending', 'delivered', 'not_delivered']
                query += " AND drv_order.status in %s"
                query_params.append(tuple(delivery_status))
            query += " ORDER BY drv_order.delivery_queue_number"
            self.env.cr.execute(query, tuple(query_params))
            result = self.env.cr.dictfetchall()

            for basic_data in result:
                pc_combination = ''.join(basic_data['pc_combination'].split('/')) if basic_data['pc_combination'] else ''
                formatted_date = basic_data['date'].strftime('%d-%m-%Y')
                customer = self.env['res.partner'].search([('id', '=', basic_data['partner_id'])])
                tags_string = ', '.join(customer.category_id.filtered(lambda tag: tag.show_in_app).mapped('name'))
                customer_data = {
                    'name': basic_data['name'],
                    'queue_number': basic_data['queue_number'],
                    'order_id': basic_data['order_id'],
                    'phone': basic_data['phone'],
                    'date': formatted_date,
                    'customer_no': basic_data['customer_no'],
                    'category': tags_string or '',
                    'plan_code': basic_data['plan_code'],
                    'pc_combination': pc_combination,
                    'district': basic_data['district'],
                    'zone': basic_data['zone'],
                    'city': basic_data['city'],
                    'street': basic_data['street'],
                    'house_no': basic_data['house_no'] or '',
                    'floor': basic_data['floor_no'] or '',
                    'apartment_no': basic_data['apartment_no'] or '',
                    'order_number': basic_data['order_number'],
                    'start_date': basic_data['start_date'],
                    'end_date': basic_data['end_date'],
                    'subscription_id': basic_data['subscription_id'],
                    'shift': basic_data['shift']
                }
                subscription = self.env['diet.subscription.order'].sudo().browse(int(basic_data['subscription_id']))
                customer_data['remaining_days'] = subscription.sub_end_in
                meals_data = {}
                meals_query = """
                    SELECT
                        meal.id AS meal_id,
                        meal.name->>'en_US' AS meal_name,
                        meal_category.name AS meal_category,
                        calendar.meal_selection_by AS meal_selection_by
                    FROM customer_meal_calendar AS calendar
                    JOIN product_template AS meal ON meal.id = calendar.meal_id
                    JOIN meals_category AS meal_category ON meal_category.id = calendar.meal_category_id
                    WHERE calendar.driver_order_id = %s
                """ % basic_data['order_id']
                self.env.cr.execute(meals_query)
                meals_query_result = self.env.cr.dictfetchall()
                for meal in meals_query_result:
                    if meal['meal_category'] not in meals_data:
                        meals_data[meal['meal_category']] = {'meals': []}
                    dislikes_query = """
                        SELECT
                            dislike.name->>'en_US' AS dislike_name
                        FROM meal_ingredient AS mc
                        JOIN product_template AS dislike ON dislike.id = mc.ingredient_id
                        WHERE mc.meal_id = %s AND mc.dislikable = TRUE AND dislike.id IN (
                            SELECT pd_rel.dislike_id
                            FROM partner_dislike_rel AS pd_rel
                            WHERE pd_rel.partner_id = %s
                        )
                        ORDER BY dislike_name;
                    """
                    self.env.cr.execute(dislikes_query, (meal['meal_id'], basic_data['partner_id']))
                    dislikes = self.env.cr.fetchall()
                    dislikes = [f'No {dislike[0]}' for dislike in dislikes]
                    meal_name = meal['meal_name']
                    if dislikes:
                        meal_name += f" ({', '.join(dislikes)})"
                    meals_data[meal['meal_category']]['meals'].append({
                        'name': meal_name,
                        'meal_selection_by': meal['meal_selection_by']
                    })


                customer_data['meals_data'] = meals_data
                if self.customer_tag_ids:
                    if customer.category_id in self.customer_tag_ids:
                        report_data.append(customer_data)
                else:
                    report_data.append(customer_data)
            
            data = {'report_data': report_data}
            
            options = {
                'page-width': '100mm',
                'page-height': '80mm',
                'margin-top': '1mm',
                'margin-right': '1mm',
                'margin-bottom': '1mm',
                'margin-left': '1mm'
            }

            html_content = """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Sample PDF</title>
                    <link href='https://fonts.googleapis.com/css?family=Libre%20Barcode%2039' rel='stylesheet'>
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
                    <link rel="preconnect" href="https://fonts.googleapis.com">
                    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                    <link href="https://fonts.googleapis.com/css2?family=Archivo:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">

                    <style>
                        body {
                            font-family: "Archivo", sans-serif;
                        }
                        .barcode {
                            font-family: 'Libre Barcode 39', cursive;
                            font-size: 24px;
                        }   
                        table {
                            font-size: 8px;
                            font-family: "Archivo", sans-serif;
                        }
                        .meal-name {
                            font-size: 9px;
                            font-weight: bold;
                        }
                        .page-break { 
                            page-break-after: always;
                        }
                    </style>
                </head>
                <body style="padding: 5px;">
                """
            slno = 1
            for rd in report_data:
                html_content += f"""
                    <table style="width:100%;height:100%;font-size:8.1px;border-collapse: collapse;">
                        <tr style="border-collapse: collapse;">
                            <td style="border-right: 1px solid black; border-collapse: collapse; width:75% !important;">
                                <span style="font-size:14.5px;">
                                    {rd['name']}&#160;&#160;<b>ID#{rd['customer_no']}</b>
                    """
                if rd['category']:
                    html_content += f"""[&#160;{rd['category']}]"""
                html_content += f"""
                                </span>
                                <br/>
                                <span style="font-size:13.5px;">
                                    {rd['phone']}
                                </span>
                            </td>
                            <td style="color: white; background-color: black; font-size:25px; text-align: center; vertical-align: middle;width:25% !important;">
                                <b>Q#{rd['queue_number']}</b>
                            </td>
                        </tr>
                """
                html_content += """
                    <tr style="height:300px;">
                        <td style="border-right: 1px solid black; border-collapse: collapse;vertical-align:top">
                """

                for md in rd['meals_data']:
                    html_content += f"""
                        <span style="font-size:13.5px; font-weight: bold;">{md}</span><br/>
                    """
                    
                    for meal in rd['meals_data'][md]['meals']:
                        # Include each meal and its specific dislikes
                        if meal['meal_selection_by'] == 'customer':
                            html_content += f"""
                                <li style="list-style-type:none;"">
                                    <i class="fas fa-hand-point-up"></i>&#160;&#160;<span style="font-size:12.5px;">{meal['name']}</span>
                                </li>
                            """
                        else:
                            html_content += f"""
                                <li style="font-size:13.5px;">{meal['name']}</li>
                            """
                    html_content += """
                        <br/>
                    """
                html_content += f"""
                        </td>
                        <td style="text-align: center; font-size: 14.5px;width:30%;vertical-align:top;">
                            <div style="border: 1px solid black;">
                                <b>{rd['date']}</b>
                            </div><br/>
                            <span style="font-weight: bold; font-size: 11.5px;">{rd['plan_code']}/{rd['pc_combination']}</span><br/><br/>
                            <div style="font-size: 11.5px;text-align: left;margin-left:9px;font-weight: bold ">
                            {rd['district']}<br/>
                            S: {rd['street']}<br/>
                            H: {rd['house_no']}<br/>
                            F: {rd['floor']}<br/>
                            Apt: {rd['apartment_no']}<br/>
                            {rd['shift']} delivery <br/>
                            </div><br/>
                            <span class="barcode">{rd['order_number']}</span>
                            <div style="height: 2px;"/>
                            <div style="text-align: right; font-size: 11px;font-weight: bold;">
                                START: <b>{rd['start_date'].strftime('%d-%m-%Y')}</b><br/>
                                END: <b>{rd['end_date'].strftime('%d-%m-%Y')}</b><br/>
                                <b>{rd['remaining_days']}</b> Days Left<br/>
                            </div>
                        </td>
                    </tr>
                </table>
                <div style="color: white; background-color: black; font-size:12px; font-weight: bold; height: 15px; line-height: 15px;">
                    <span style="vertical-align: center;">Rasha Bowl</span>
                    <span style="float: right; vertical-align: center;">Zone:{rd['zone']}</span>
                </div>
                <div class="page-break" style="font-size:10px; height: 6px; position: relative;">
                    <span style="position: absolute; left: 0;"><i class='fas fa-globe' style='font-size:8px'></i> www.rashabowl.in</span>
                    <span style="position: absolute; right: 0;"><i class='fas fa-mobile-alt' style='font-size:8px;'></i> </span>
                </div>
                """
                slno += 1
            html_content += """
                </body>
                </html>
                """
            
            pdfkit_val = pdfkit.from_string(html_content, options=options)
            kw_datetime = datetime.now(pytz.utc).astimezone(pytz.timezone('Asia/Kuwait')).strftime('%Y-%m-%d_%H:%M')
            attachment_id = self.env['ir.attachment'].create({
                'name': f'{self.date} - Delivery Sticker Print {kw_datetime}',
                'type': 'binary',
                'datas': base64.b64encode(pdfkit_val).decode('utf-8'),
                'mimetype': 'application/pdf',
                'is_delivery_report_file': True
            })
            if attachment_id:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/content/%s?download=true' % attachment_id.id,
                    'target': 'self',
                }

    def preview(self):
        query_params = [self.date.strftime('%Y-%m-%d')]
        query = """
            SELECT
                partner.id AS partner_id,
                partner.full_name AS name,
                partner.customer_sequence_no AS customer_no,
                partner.phone AS phone,
                drv_order.delivery_queue_number AS queue_number,
                drv_order.date AS date,
                plan.short_code AS plan_code,
                subscription.order_number AS order_number,
                subscription.pc_combination AS pc_combination,
                district.name AS district,
                city.name AS city,
                address.street AS street,
                address.house_number AS house_no,
                address.floor_number AS floor_no,
                address.apartment_no AS apartment_no,
                address.jedha AS jedha,
                shift.shift AS shift,
                subscription.actual_start_date AS start_date,
                subscription.end_date AS end_date,
                subscription.id AS subscription_id,
                drv_order.id AS order_id,
                driver.name AS driver_id,
                zone.name AS zone
            FROM
                driver_order AS drv_order
            JOIN res_partner AS partner ON drv_order.customer_id = partner.id
            JOIN diet_subscription_order AS subscription ON drv_order.subscription_id = subscription.id
            JOIN subscription_package_plan AS plan ON subscription.plan_id = plan.id
            JOIN res_partner AS address ON address.id = drv_order.address_id
            JOIN customer_district AS district ON district.id = address.district_id
            JOIN res_country_state AS city ON city.id = address.state_id
            JOIN customer_shift AS shift ON shift.id = drv_order.shift_id
            LEFT JOIN customer_zone AS zone ON zone.id = district.zone_id
            join area_driver AS driver on driver.id = drv_order.driver_id

            WHERE
                drv_order.date = %s
        """
        if self.shift_id:
            query += " AND drv_order.shift_id = %s"
            query_params.append(self.shift_id.id)
        if self.customer_tag_ids:
            query += " AND customer_tags.id IN %s"
            query_params.append(tuple(self.customer_tag_ids.ids))
        if self.status:
            if self.status == 'pending':
                delivery_status = ['pending']
            elif self.status == 'delivered':
                delivery_status = ['delivered']
            elif self.status == 'not_delivered':
                delivery_status = ['not_delivered']
            else:
                delivery_status = ['pending', 'delivered', 'not_delivered']
            query += " AND drv_order.status in %s"
            query_params.append(tuple(delivery_status))
        query += " ORDER BY drv_order.delivery_queue_number"
        self.env.cr.execute(query, tuple(query_params))
        result = self.env.cr.dictfetchall()
        docs = []
        for data in result:
            customer = self.env['res.partner'].search([('id', '=', data['partner_id'])])
            tags_string = ', '.join(customer.category_id.mapped('name'))
            customer_data = {
                'sl_no': data.get('queue_number', ''),
                'name': data.get('name', ''),
                'id': data.get('customer_no', ''),
                'tag' : tags_string or '',
                'mobile' : data.get('phone', ''),
                'city' : data.get('city', ''),
                'district' : data.get('district', ''),
                'street' : data.get('street', ''),
                'zone' : data.get('zone', ''),
                'house_no' :data.get('house_no', ''),
                'floor' : data.get('floor_no', ''),
                'apartment_no' : data.get('apartment_no', ''),
                'delivery_date': self.date.strftime('%Y-%m-%d'),
                'start_date': data.get('start_date', ''),
                'end_date': data.get('end_date', ''),
                'shift': data.get('shift', ''),
                'driver_id': data.get('driver_id', ''),
            }
            if self.customer_tag_ids:
                if customer.category_id in self.customer_tag_ids:
                    docs.append(customer_data)
            else:
                docs.append(customer_data)
        data = {
            'doc' : docs
        }
        return self.env.ref("diet.action_delivery_report_preview").report_action(self, data=data, config=False)
from odoo import models, fields

class MealsDeliveryReport(models.AbstractModel):
    _name = 'report.diet.meals_delivery_report'
    _description = 'Meals Delivery Report'

    def _get_report_values(self, docids, data=None):

        delivery_date = data.get('date', False)
        status = data.get('status', False)
        shift_id = data.get('shift_id', False)
        customer_tag_ids = data.get('customer_tag_ids', [])
        report_type = data.get('report_type', False)

        report_data = []
        query_params = [delivery_date]
        query = """
            SELECT
                partner.id AS partner_id,
                partner.full_name AS name,
                partner.customer_sequence_no AS customer_no,
                partner.phone AS phone,
                drv_order.delivery_queue_number AS queue_number,
                drv_order.date AS date,
                plan.name AS plan_name,
                subscription.order_number AS order_number,
                subscription.pc_combination AS pc_combination,
                shift.shift AS shift,
                shift.id AS shift_id,
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
            WHERE
                drv_order.date = %s
        """
        if shift_id:
            query += " AND drv_order.shift_id = %s"
            query_params.append(shift_id)
        if customer_tag_ids:
            query += " AND customer_tags.id IN %s"
            query_params.append(tuple(customer_tag_ids))
        if status:
            if status == 'pending':
                delivery_status = ['pending']
            elif status == 'delivered':
                delivery_status = ['delivered']
            elif status == 'not_delivered':
                delivery_status = ['not_delivered']
            else:
                delivery_status = ['pending', 'delivered', 'not_delivered']
            query += " AND drv_order.status in %s"
            query_params.append(tuple(delivery_status))
        query += """
            ORDER BY
                drv_order.delivery_queue_number
        """

        self.env.cr.execute(query, tuple(query_params))
        result = self.env.cr.dictfetchall()
        queue_number = 1
        for basic_data in result:
            pc_combination = ''.join(basic_data['pc_combination'].split('/')) if basic_data['pc_combination'] else ''
            formatted_date = basic_data['date'].strftime('%d-%m-%Y')
            customer = self.env['res.partner'].search([('id', '=', basic_data['partner_id'])])
            tags_string = ', '.join(customer.category_id.mapped('name'))
            customer_data = {
                'queue_number': basic_data['queue_number'],
                'name': basic_data['name'],
                'partner_id': basic_data['partner_id'],
                'order_id': basic_data['order_id'],
                'phone': basic_data['phone'],
                'date': formatted_date,
                'customer_no': basic_data['customer_no'],
                'category': tags_string or '',
                'plan_name': basic_data['plan_name'],
                'pc_combination': pc_combination,
                'order_number': basic_data['order_number'],
                'start_date': basic_data['start_date'],
                'end_date': basic_data['end_date'],
                'subscription_id': basic_data['subscription_id'],
                'shift': basic_data['shift'],
                'shift_id': basic_data['shift_id'],
            }
            subscription = self.env['diet.subscription.order'].sudo().browse(int(basic_data['subscription_id']))
            customer_data['remaining_days'] = subscription.sub_end_in

            meals_data = {}
            meal_category_query = """
                SELECT category.id, category.name 
                FROM meals_count AS so_line
                JOIN meals_category AS category ON category.id = so_line.meal_category_id
                WHERE so_line.meal_subscription_id = %s
            """
            self.env.cr.execute(meal_category_query, (basic_data['subscription_id'],))
            meal_categories = self.env.cr.fetchall()
            all_dislikes = []
            for meal_category_id, meal_category_name in meal_categories:
                category_meal_calendar_entry_query = """
                    SELECT meal.id, meal.name ->> 'en_US' AS meal
                    FROM customer_meal_calendar AS cal
                    JOIN product_template AS meal ON meal.id = cal.meal_id
                    WHERE cal.meal_category_id = %s AND cal.partner_id = %s AND cal.date = %s
                    AND cal.state IN ('active', 'active_with_meal')
                """
                self.env.cr.execute(category_meal_calendar_entry_query, (meal_category_id, basic_data['partner_id'], delivery_date))
                meal_category_meals = self.env.cr.fetchall()
                meal_names = [meal[1] for meal in meal_category_meals]
                meal_ids = [meal[0] for meal in meal_category_meals]

                if meal_ids:
                    meals_data[meal_category_name] = {'meals': ''}
                    meals_list = []
                    for meal_id, meal_name in zip(meal_ids, meal_names):
                        meal_dislikes_query = """
                            SELECT ingredient.name ->> 'en_US' AS dislike
                            FROM meal_ingredient mc
                            JOIN product_template ingredient ON ingredient.id = mc.ingredient_id
                            WHERE mc.meal_id = %s AND mc.dislikable = TRUE AND ingredient.id IN (
                                SELECT pd_rel.dislike_id
                                FROM partner_dislike_rel pd_rel
                                WHERE pd_rel.partner_id = %s
                            )
                        """
                        self.env.cr.execute(meal_dislikes_query, (meal_id, basic_data['partner_id']))
                        dislikes = [f"No {dislike['dislike']}" for dislike in self.env.cr.dictfetchall()]
                        if dislikes:
                            meal_name += f" ({', '.join(dislikes)})"
                        meals_list.append(meal_name)
                    meals_data[meal_category_name]['meals'] = ', '.join(meals_list)

            all_dislikes_query = """
                SELECT ingredient.name ->> 'en_US' AS dislike
                FROM partner_dislike_rel pd_rel
                JOIN product_template ingredient ON ingredient.id = pd_rel.dislike_id
                WHERE pd_rel.partner_id = %s
            """
            self.env.cr.execute(all_dislikes_query, (basic_data['partner_id'],))
            all_dislikes = [dislike['dislike'] for dislike in self.env.cr.dictfetchall()]
            customer_data.update({
                'meals_data': meals_data,
                'customer_dislikes': ', '.join(all_dislikes)
            })
            if customer_tag_ids:
                customer_tags = self.emv['res.partner.category'].browse(customer_tag_ids)
                if customer.category_id in customer_tags:
                    report_data.append(customer_data)
            else:
                report_data.append(customer_data)
            queue_number += 1
        if report_type == 'delivery_report_with_dislikes':
            report_data = [customer for customer in report_data if customer['customer_dislikes']]
        elif report_type == 'delivery_report_without_dislikes':
            report_data = [customer for customer in report_data if not customer['customer_dislikes']]
        if shift_id:
            report_data = [customer for customer in report_data if customer['shift_id'] == shift_id]
            
        return {
            'doc_ids': docids,
            'doc_model': self.env['delivery.report.wizard'],
            'data': data,
            'report_data': report_data,
            'docs': self.env['customer.meal.calendar'].browse(docids),
        }
    
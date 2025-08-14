from odoo import models
from datetime import datetime

class DeliveryStickerTemplate(models.AbstractModel):
    _name = 'report.diet.delivery_sticker_template'
    _description = 'Delivery Sticker Template'

    def _get_report_values(self, docids, data):
        date = data.get('date', False)
        status = data.get('status', False)
        shift_id = data.get('shift_id', False)
        customer_tag_ids = data.get('customer_tag_ids', [])
        report_data = []
        query = f"""select Distinct ON (partner.id)
            partner.full_name as name,
            partner.id as id,
            partner.customer_sequence_no as customer_no,
            partner.phone as phone,
            cal.so_id as order_id,
            cal.date as date,
            plan.short_code as plan_code,
            subscription.pc_combination as pc_combination,
            area.name as area,
            address.street as street,
            address.jedha as jedha,
            address.house_number as house_no,
            address.floor_number as floor_no,
            address.apartment_no as apartment_no,
            shift.shift as shift,
            subscription.order_number as order_number,
            subscription.actual_start_date as start_date,
            subscription.end_date as end_date,
            subscription.id as subscription_id
            from customer_meal_calendar as cal
            left join res_partner as partner on cal.partner_id = partner.id
            left join diet_subscription_order as subscription on cal.so_id=subscription.id
            left join subscription_package_plan plan ON subscription.plan_id = plan.id
            left join res_partner as address on address.id=cal.address_id
            left join customer_area as area on area.id=address.area_id
            left join customer_shift as shift on shift.id=cal.shift_id
            left join res_partner_res_partner_category_rel as customer_tags on customer_tags.partner_id = cal.partner_id
            WHERE cal.date ='{date}' and cal.state in ('active', 'active_with_meal')"""
        if shift_id:
            query += f""" AND cal.shift_id = {shift_id} """
            
        if customer_tag_ids:
            query += f""" AND customer_tags.category_id IN ({','.join(str(i) for i in customer_tag_ids)}) """
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()

        for basic_data in result:
            pc_combination = ''.join(basic_data['pc_combination'].split('/')) if basic_data['pc_combination'] else ''
            formatted_date = basic_data['date'].strftime('%d-%m-%Y')
            customer_data = {
                'name': basic_data['name'],
                'id': basic_data['id'],
                'order_id':basic_data['order_id'],
                'phone': basic_data['phone'],
                'date': formatted_date,
                'customer_no': basic_data['customer_no'],
                'plan_code': basic_data['plan_code'],
                'pc_combination': pc_combination,
                'area': basic_data['area'],
                'street': basic_data['street'],
                'jedha': basic_data['jedha'],
                'house_no': basic_data['house_no'],
                'floor': basic_data['floor_no'],
                'apartment_no': basic_data['apartment_no'],
                'order_number': basic_data['order_number'],
                'start_date': basic_data['start_date'],
                'end_date': basic_data['end_date'],
                'subcription_id': basic_data['subscription_id'],
                'shift':basic_data['shift']
            }
            meals_data = {}
            meal_category_query = f"""select 
                category.id, category.name from meals_count as so_line
                join meals_category as category on category.id=so_line.meal_category_id
                join diet_subscription_order as subscription on subscription.id=so_line.meal_subscription_id
                where subscription.id={basic_data['subscription_id']}"""
            self.env.cr.execute(meal_category_query)
            meal_categories = self.env.cr.fetchall()
            meal_category_ids = [category[0] for category in meal_categories]
            meal_category_names = [category[1] for category in meal_categories]
            for meal_category_id, meal_category_name in zip(meal_category_ids, meal_category_names):
                category_meal_calendar_entry_query = f"""select 
                    meal.id, meal.name ->>'en_US' as meal
                    from customer_meal_calendar AS cal
                    join product_template AS meal ON meal.id = cal.meal_id
                    where cal.meal_category_id = {meal_category_id} AND cal.partner_id = {basic_data['id']} and cal.date= '{date}' 
                    """
                self.env.cr.execute(category_meal_calendar_entry_query)
                meal_category_meals = self.env.cr.fetchall()
                meal_names = [meal[1] for meal in meal_category_meals]
                meal_ids = [meal[0] for meal in meal_category_meals]
            
                if meal_ids:
                    order_id = basic_data['order_id']
                    meal_category_dislikes_query = f"""
                        SELECT ingredient.id,ingredient.name->>'en_US' as dislike
                        FROM meal_ingredient mc
                        JOIN product_template ingredient ON ingredient.id=mc.ingredient_id
                        WHERE mc.meal_id IN ({','.join(map(str, meal_ids))}) AND mc.dislikable=True
                        AND ingredient.id in (
	                SELECT pd_rel.dislike_id
	                FROM partner_dislike_rel pd_rel
	                JOIN diet_subscription_order subs ON subs.partner_id=pd_rel.partner_id
	                WHERE subs.id={order_id})"""
                    self.env.cr.execute(meal_category_dislikes_query)
                    dislikes = [dislike['dislike'] for dislike in self.env.cr.dictfetchall()]
                    meals_data[meal_category_name] = {'meals': meal_names, 'dislikes': ', '.join(dislikes)}

            customer_data['meals_data'] = meals_data
            report_data.append(customer_data)

        domain = [('date', '=', date), ('state', 'in', ['active', 'active_with_meal'])]
        if shift_id:
            domain += [('shift_id', '=', shift_id)]
        if customer_tag_ids:
            domain += [('partner_id.category_id', 'in', customer_tag_ids)]

        meal_calendar_ids = self.env['customer.meal.calendar'].search(domain)
        customer_ids = meal_calendar_ids.mapped('partner_id')
        for customer in customer_ids:
            customer_meal_calendar_ids = meal_calendar_ids.filtered(lambda x: x.partner_id == customer)
            subscription_id = customer_meal_calendar_ids[0].so_id if customer_meal_calendar_ids else False
            remaining_days = subscription_id.sub_end_in if subscription_id else ''
            for data in report_data:
                if data['id'] == customer.id:
                    data['remaining_days'] = remaining_days
                    break
        return {
            'report_data': report_data,
        }
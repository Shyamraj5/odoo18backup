from odoo import fields,models,api
from datetime import datetime

class MealStickerTemplate(models.AbstractModel):
    _name = 'report.diet.meal_sticker_template'
    _description = 'Meal Sticker Template'

    def _get_report_values(self,docids, data):
        date = data.get('date')
        meal_category_id = data.get('meal_category_id')
        meal_id = data.get('meal_id')
        query = f"""
                    SELECT so_id as order_id,so.order_number,p.protein,p.carbohydrates,pt.name->>'en_US' as name,ms.date,
                    ms.meal_id as meal_id,ms.meal_category_id,mc.name as mealcategory
                    FROM customer_meal_calendar  ms
                    JOIN diet_subscription_order so ON ms.so_id = so.id
                    JOIN subscription_package_plan p ON so.plan_id = p.id
                    JOIN meals_category mc ON ms.meal_category_id = mc.id
                    LEFT JOIN product_template pt ON ms.meal_id = pt.id
                    WHERE ms.date = '{date}' AND ms.state in ('active','active_with_meal')
                    AND ms.meal_id IS NOT NULL
                """
        if meal_category_id:
            query += f""" AND ms.meal_category_id = {meal_category_id} """
            
        if meal_id:
            query += f""" AND ms.meal_id = {meal_id} """

        query += " ORDER BY ms.meal_id, so.order_number"
        self.env.cr.execute(query)
        meal_records = self.env.cr.dictfetchall()
        for meal in meal_records:
            meal_id = meal['meal_id']
            order_id = meal['order_id']
            dislike_query = f"""
                SELECT ingredient.name->>'en_US' as dislike
                FROM meal_ingredient mc
                JOIN product_template ingredient ON ingredient.id=mc.ingredient_id
                WHERE mc.meal_id={meal_id} AND mc.dislikable=True
                AND ingredient.id in (
	                SELECT pd_rel.dislike_id
	                FROM partner_dislike_rel pd_rel
	                JOIN diet_subscription_order subs ON subs.partner_id=pd_rel.partner_id
	                WHERE subs.id={order_id})"""
            self.env.cr.execute(dislike_query)
            dislikes = [dislike['dislike'] for dislike in self.env.cr.dictfetchall()]
            meal['dislikes'] = ", ".join(dislikes)
        return {
            'doc_ids': docids,
            'meal_records': meal_records,
        }

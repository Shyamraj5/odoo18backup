from odoo import models, fields

class OrderReportHTML(models.AbstractModel):
    _name = 'report.diet.order_report_html'
    _description = 'Order Report HTML'

    def _get_report_values(self, docids, data=None):
        date = data['date']
        pc_combinations_query = """
            SELECT so.pc_combination, cmc.meal_id 
            FROM customer_meal_calendar cmc
            JOIN diet_subscription_order so ON cmc.so_id = so.id
            WHERE cmc.date = '%s' AND cmc.state in ('active','active_with_meal')
        """ % date
        self.env.cr.execute(pc_combinations_query)
        query_result = self.env.cr.fetchall()
        pc_combinations = list(set([x[0] for x in query_result]))
        pc_combinations.sort()
        calendar_meals = [x[1] for x in query_result if x is not None]
        calendar_meals = list(set(calendar_meals))
        calendar_meals = list(filter(lambda x: x is not None, calendar_meals))
        order_data = []
        sl_no = 1
        calendar_meals = self.env['product.template'].browse(calendar_meals)
        for meal in calendar_meals:
            meal_data = {
                'sl_no': sl_no,
                'meal_name': meal.name
            }
            for pc_combination in pc_combinations:
                meal_count_query = """
                    SELECT COUNT(*)
                    FROM customer_meal_calendar cmc
                    JOIN diet_subscription_order so ON cmc.so_id = so.id
                    WHERE cmc.date = '%s' AND cmc.meal_id = %s AND so.pc_combination = '%s'
                    AND cmc.state in ('active','active_with_meal')
                """ % (date, meal.id, pc_combination)
                self.env.cr.execute(meal_count_query)
                meal_count = self.env.cr.fetchone()[0]
                meal_data[pc_combination] = meal_count
            order_data.append(meal_data)
            dislikables = meal.ingredients_line_ids.filtered(lambda x: x.dislikable)
            for dislikable in dislikables:
                dislike = dislikable.ingredient_id
                meal_name = f"{meal.name} (w/o {dislike.name})"
                meal_dislikable_data = {
                    'sl_no': '',
                    'meal_name': meal_name
                }
                for pc_combination in pc_combinations:
                    meal_dislikable_data[pc_combination] = 0
                    subscription_query = """
                        SELECT so.id
                        FROM customer_meal_calendar cmc
                        JOIN diet_subscription_order so ON cmc.so_id = so.id
                        WHERE cmc.date = '%s' AND cmc.meal_id = %s AND so.pc_combination = '%s'
                        AND cmc.state in ('active','active_with_meal')
                    """ % (date, meal.id, pc_combination)
                    self.env.cr.execute(subscription_query)
                    subscriptions = self.env.cr.fetchall()
                    subscriptions = [x[0] for x in subscriptions]
                    subscriptions = list(set(subscriptions))
                    subscriptions = self.env['diet.subscription.order'].browse(subscriptions)
                    for subscription in subscriptions:
                        if dislike in subscription.partner_id.dislikes_ids:
                            meal_dislikable_data[pc_combination] += 1
                if sum(list(meal_dislikable_data.values())[2:]) > 0:
                    order_data.append(meal_dislikable_data)
            sl_no += 1
        return {
            'report_data': order_data,
            'pc_combinations': pc_combinations,
        }
    
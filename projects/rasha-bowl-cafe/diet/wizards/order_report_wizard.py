from odoo import models, fields

class OrderReportWizard(models.Model):
    _name = 'order.report.wizard'
    _description = 'Order Report Wizard'
    
    date = fields.Date('Date', default=fields.Date.today())

    def view_report(self):
        data = {'date': self.date}
        return self.env.ref('diet.order_report_html_action').report_action(self, data=data, config=False)

    def export_report(self):
        # Search for all active meal calendar entries for the given date
        calendar_entries = self.env['customer.meal.calendar'].search([
            ('date', '=', self.date),
            ('state', 'in', ['active', 'active_with_meal'])
        ])  

        # Initialize an empty dictionary to store the data
        order_data = {}

        # Initialize serial number tracker for each meal category
        sl_no_tracker = {}

        # Tracker to keep track of totals for combining
        combined_tracker = {}

        # Iterate through each calendar entry
        for entry in calendar_entries:
            if entry.so_id.state == 'in_progress':
                # Extract relevant details
                meal_category_name = entry.meal_category_id.name
                meal_name = entry.meal_id.name
                pc_combination = entry.so_id.pc_combination

                # Check if the meal contains disliked ingredients
                disliked_ingredients = entry.partner_id.dislikes_ids.mapped('name')
                meal_ingredients = entry.meal_id.ingredients_line_ids.filtered(lambda line: line.dislikable).mapped('ingredient_id.name')

                # Determine disliked ingredients present in the meal
                present_disliked_ingredients = [ingredient for ingredient in disliked_ingredients if ingredient in meal_ingredients]
                is_dislike = bool(present_disliked_ingredients)
                if is_dislike:
                    disliked_part = ', '.join(f'No {ingredient}' for ingredient in present_disliked_ingredients)
                    meal_name_with_dislike = f"{meal_name} ({disliked_part})"
                else:
                    meal_name_with_dislike = meal_name

                # If the meal category is not already in the dictionary, add it
                if meal_category_name not in order_data:
                    order_data[meal_category_name] = []
                    sl_no_tracker[meal_category_name] = 1  # Initialize serial number for this category
                    combined_tracker[meal_category_name] = {}  # Initialize combined tracker per category

                # Find if the meal with the same PC combination already exists in the list
                existing_meal_data = next((item for item in order_data[meal_category_name] if item['meal_name'] == meal_name_with_dislike), None)

                if existing_meal_data:
                    # If it exists, update the count for the PC combination
                    if pc_combination in existing_meal_data:
                        existing_meal_data[pc_combination] += 1
                    else:
                        existing_meal_data[pc_combination] = 1
                    # Update the subtotal
                    existing_meal_data['sub_total'] += 1
                else:
                    # If it doesn't exist, create a new entry
                    meal_data = {
                        'meal_name': meal_name_with_dislike,
                        pc_combination: 1,
                        'sub_total': 1,
                        'is_dislike': is_dislike  # Remove sl_no here for individual meals
                    }
                    order_data[meal_category_name].append(meal_data)

                # Track the total for the combined row (base meal without dislikes)
                base_meal_name = meal_name  # The meal name without dislikes
                if base_meal_name not in combined_tracker[meal_category_name]:
                    combined_tracker[meal_category_name][base_meal_name] = {}

                # Update combined data
                if pc_combination not in combined_tracker[meal_category_name][base_meal_name]:
                    combined_tracker[meal_category_name][base_meal_name][pc_combination] = 1
                else:
                    combined_tracker[meal_category_name][base_meal_name][pc_combination] += 1

        # Add combined rows for each meal (with and without dislikes)
        for category, meals in combined_tracker.items():
            combined_meals = []
            for base_meal_name, pc_combinations in meals.items():
                # Create a new row for the base meal (with sl_no)
                combined_row = {
                    'sl_no': sl_no_tracker[category],  # Only this row gets a serial number
                    'meal_name': base_meal_name,  # Just the base meal name
                    'sub_total': sum(pc_combinations.values()),  # Sum of all PC combinations
                    'is_dislike': False  # It's a combined row, not a specific dislike entry
                }
                # Add the counts for each PC combination
                for pc_combination, count in pc_combinations.items():
                    combined_row[pc_combination] = count

                combined_meals.append(combined_row)  # Add the combined row with sl_no
                sl_no_tracker[category] += 1  # Increment serial number

                # Append the original rows (with and without dislikes) under this meal
                for meal in order_data[category]:
                    if meal['meal_name'].startswith(base_meal_name):
                        meal['sl_no'] = ''  # No sl_no for individual rows under the combined row
                        combined_meals.append(meal)  # Add the individual meal row

            # Replace the original meals with the combined sorted list
            order_data[category] = combined_meals
            
        for category, meals in order_data.items():
            unique_meals = {}
            for meal in meals:
                key = (meal['meal_name'], meal['sub_total'])
                if key not in unique_meals or meal['sl_no']:
                    unique_meals[key] = meal
            # Update the order_data with unique meals
            order_data[category] = list(unique_meals.values())

        data = {
            'report_data': order_data,
            'pc_combinations': list(set(calendar_entries.mapped('so_id').mapped('pc_combination')))
        }
        return self.env.ref('diet.order_report_xlsx').report_action(self, data=data, config=False)

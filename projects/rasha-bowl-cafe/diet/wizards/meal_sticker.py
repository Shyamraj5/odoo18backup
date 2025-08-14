from odoo import api,fields,models
from datetime import timedelta
import base64
import pdfkit

class CustomerMealsPrintWizard(models.TransientModel):
    _name = "meal.sticker.menu"
    _description = "Wizard for Customer Meals Print"


    date = fields.Date(string ="Date", required =True)
    meal_category_id= fields.Many2one('meals.category', string="Meal Category")
    meal_id = fields.Many2one('product.template', string="Meal")


    def pdf_report(self):
        data = {
            'date': self.date,
            'meal_category_id': self.meal_category_id.id,
            'meal_id':self.meal_id.id
        }

        query = f"""
                    SELECT so_id as order_id,so.order_number,so.protein,so.carbs,pt.name->>'en_US' as name,ms.date,
                    ms.meal_id as meal_id,ms.meal_category_id,mc.name as mealcategory, mc.show_pc_combination_in_report as show_category
                    FROM customer_meal_calendar  ms
                    JOIN diet_subscription_order so ON ms.so_id = so.id
                    JOIN subscription_package_plan p ON so.plan_id = p.id
                    JOIN meals_category mc ON ms.meal_category_id = mc.id
                    LEFT JOIN product_template pt ON ms.meal_id = pt.id
                    WHERE ms.date = '{self.date.strftime('%Y-%m-%d')}' AND ms.state in ('active','active_with_meal')
                    AND ms.meal_id IS NOT NULL AND so.state IN ('in_progress')
                """
        if self.meal_category_id:
            query += f""" AND ms.meal_category_id = {self.meal_category_id.id} """
            
        if self.meal_id:
            query += f""" AND ms.meal_id = {self.meal_id.id} """

        # query += " ORDER BY name, so.protein,so.carbs"
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
	                WHERE subs.id={order_id}
                )
                ORDER BY dislike;"""
            self.env.cr.execute(dislike_query)
            dislikes = [f"No {dislike['dislike']}"  for dislike in self.env.cr.dictfetchall()]
            meal['dislikes'] = ", ".join(dislikes)

        sorted_meals = sorted(
            meal_records,
            key=lambda meal: (
                meal['name'], 
                meal.get('dislikes'),
                meal['protein'], 
                meal['carbs'],
            )
        )
        
            
        options = {
            'page-width': '58mm',
            'page-height': '38mm',
            'margin-top': '2mm',  # Adjust margins if needed
            'margin-right': '2mm',
            'margin-bottom': '2mm',
            'margin-left': '2mm'
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
                <style>
                    body {
                        margin: 0;
                        padding: 0;
                        font-size: 12px; /* Adjusted font size for smaller page */
                    }
                    table {
                        width: 100%;
                        height: 160px;
                        border: 1px solid black;
                        margin-bottom: 0.5em;
                        table-layout: fixed;
                    }
                    td {
                        text-align: center;
                        padding: 1px;
                        font-size: 10px;
                    }
                    .name-cell {
                        font-weight: bold;
                        height: auto; /* Allow height to adjust based on content */
                    }
                    .details-cell, .icon-cell, .date-cell {
                        font-weight: bold;
                        height: auto; /* Allow height to adjust based on content */
                    }
                    .logo-cell {
                        text-align: right;
                    }
                    img {
                        width: 8%; /* Adjusted logo size */
                    }
                    .page-break {
                        page-break-after: always;
                    }
                </style>
            </head>
            <body>
            """
        for sticker in sorted_meals:
            html_content += f"""
                <table>
                    <tr>
                        <td class="name-cell">
                            <span>{sticker['name']}</span><br/>
            """
            if sticker['dislikes']:
                html_content += f"""
                        <span>({sticker['dislikes']})</span>
                            """
            protein = int(sticker['protein'])
            carbohydrates = int(sticker['carbs'])
            prd = sticker['date'] - timedelta(days=1)
            exp = sticker['date'] + timedelta(days=1)
            html_content += f"""
                        </td>
                    </tr>
                    <tr>
                        <td class="details-cell">
                            <span>{sticker['order_number']}</span>
            """
            if sticker['show_category']:
                html_content += f"""
                            <span>&#160;&#160;&#160;P{protein}/</span>
                            <span>C{carbohydrates}</span>
                """
            html_content += f"""
                        </td>
                    </tr>
                    <tr>
                        <td class="icon-cell">
                            <i class="fa-solid fa-utensils"></i>&#160;&#160;&#160;{sticker['mealcategory']}<br/>
                        </td>
                    </tr>
                    <tr>
                        <td class="date-cell" style="position: relative;">
                            <span>PRD {prd.strftime('%b %d %Y')}</span><br/>
                            <span>EXP {exp.strftime('%b %d %Y')}</span><br/>
                            <div class="logo-cell" style="position: absolute; bottom: 0; right: 0;">
                                <img src="file:///odoo/diet_done/miscellaneous/diet/static/src/img/logo.jpg" alt="Logo" style="width:10%;"/>
                            </div>
                        </td>
                    </tr>
                </table>
                <div class="page-break"></div>
            """

        html_content += """
            </body>
            </html>
            """
        pdfkit_val = pdfkit.from_string(html_content, options=options)

        attachment_id = self.env['ir.attachment'].create({
            'name': 'Meal Sticker',
            'type': 'binary',
            'datas': base64.b64encode(pdfkit_val).decode('utf-8'),
            'is_meal_sticker_report_file': True
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment_id.id,
            'target': 'self',
        }      
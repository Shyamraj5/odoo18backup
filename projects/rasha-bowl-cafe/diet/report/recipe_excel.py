from odoo import models
import re


class RecipeExcelReport(models.AbstractModel):
    _name = "report.recipe_excel"
    _description = "Excel report of Recipe"
    _inherit = "report.report_xlsx.abstract"
    

    def generate_xlsx_report(self, workbook, data, lines):
        format1a =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "center",
                    "bold": True,
                    "valign": "vcenter",}
        )
        format1b =workbook.add_format(
            {
                "font_size": 11,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "valign": "vcenter",
                "num_format": "#,##0.00",
                })
        format1c =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "left",
                    "bold": True,
                    "valign": "vcenter",
                    "bg_color" :"#8bc388",
                    }
        )
        format1d =workbook.add_format(
            {
                "font_size": 20,
                "bottom" : True,
                "right" : True,
                "left": True,
                "top": True,
                "align": "center",
                "bold": True,
                "bg_color" :"#8bc388",
                "font_color" : "white",
                "valign": "vcenter"
            }
        )
        format1e =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "left",
                    "bold": True,
                    "valign": "vcenter",
                    "bg_color" :"#b7dfa9",
                    }
        )
        worksheet = workbook.add_worksheet("MEAL RECIPE")
        worksheet.merge_range(
            "A1:D1", "FEED", format1d)
        worksheet.merge_range(
            "A2:D2", lines.name, format1a)
        worksheet.merge_range(
            "A3:D3", lines.meal_id.name.upper(), format1a)
        category = [category.name for category in lines.meal_id.meal_category_id]
        worksheet.merge_range(
            "A4:D4", ",".join(category), format1a)
        worksheet.set_row(0, 30)
        worksheet.set_row(1, 30)
        worksheet.set_row(2, 30)
        worksheet.set_column("A:A", 7)
        worksheet.set_column("B:B", 60)
        worksheet.set_column("C:C", 15)
        worksheet.set_column("D:D", 15)

        worksheet.merge_range("A5:D5", "INGREDIENTS :", format1c)
        worksheet.write("A6", "NO",format1e)
        worksheet.write("B6", "NAME",format1e)
        worksheet.write("C6", "QTY",format1e )
        worksheet.write("D6", "UNIT",format1e )
        row = 7
        i = 0
        for line in lines.recipe_ingredient_line_ids: 
            i += 1
            worksheet.write("A%s" %row, str(int(i)), format1b)
            worksheet.write("B%s" %row, line.ingredient_id.name, format1b)
            worksheet.write("C%s" %row, line.qty, format1b)
            worksheet.write("D%s" %row, line.unit.name, format1b)
            row += 1
        # merge range for notes heading
        line_length=len(lines.recipe_ingredient_line_ids)
        steps_merge_range ='A{}:D{}'.format(7 + line_length, 7 + line_length)
        worksheet.merge_range(steps_merge_range, "STEPS:", format1c)

        recipe_formatted =str(lines.recipe)
        if  "<p>" in recipe_formatted:
            recipe_formatted =recipe_formatted.replace("<p>","")
        if  "<br>" in recipe_formatted:
            recipe_formatted =recipe_formatted.replace("<br>","\n")
        if "</p>" in recipe_formatted:
                recipe_formatted = recipe_formatted.replace("</p>","\n")
        if "<ol>" in recipe_formatted:
             recipe_formatted = recipe_formatted.replace("<ol>","")
        if "<ul>" in recipe_formatted:
             recipe_formatted = recipe_formatted.replace("<ul>","")
        if "</ol>" in recipe_formatted:
             recipe_formatted = recipe_formatted.replace("</ol>","")
        if "</ul>" in recipe_formatted:
             recipe_formatted = recipe_formatted.replace("</ul>","")
        if "<li>" in recipe_formatted:
             recipe_formatted = recipe_formatted.replace("<li>","")
        if "</li>" in recipe_formatted:
             recipe_formatted = recipe_formatted.replace("</li>","\n")
        
        # merge range for recipe data
        recipe_merge_range ='A{}:D{}'.format(8 + line_length, 8 + line_length)
        worksheet.merge_range(recipe_merge_range, recipe_formatted, format1b)
        # set row length for recipe
        leng = len(recipe_formatted.split('\n'))
        worksheet.set_row(7 + line_length, 15 * leng)
        # merge range for nutrient heading
        nutrient_merge_range ='A{}:D{}'.format(9 + line_length, 9 + line_length)
        worksheet.merge_range(nutrient_merge_range, "NUTRIENTS LABEL :", format1c)
        # merge range for nutrient data
        label_merge_range ='A{}:D{}'.format(10 + line_length, 10 + line_length)
        label =  "Protein: " + str(lines.protein) + "\n" + "Carbohydrates: "  + str(lines.carbohydrates ) + "g" + "\n" + ("Fat: "+ str(lines.fats) +"g" + "\n" )+ "Calories: "+ str(lines.calorie)
        worksheet.merge_range(label_merge_range,label, format1b)
        worksheet.set_row(9 + line_length, 60)
        # merge range for notes heading
        notes_merge_range ='A{}:D{}'.format(11 + line_length, 11 + line_length)
        worksheet.merge_range(notes_merge_range, "NOTES :", format1c)
        # merge range for notes data
        note_data_merge_range ='A{}:D{}'.format(12 + line_length, 12 + line_length)
        worksheet.merge_range(note_data_merge_range, "", format1b)
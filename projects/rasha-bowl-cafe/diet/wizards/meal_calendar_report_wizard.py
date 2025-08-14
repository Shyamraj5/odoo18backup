from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from datetime import timedelta



class MealCalendarReportWizard(models.TransientModel):
    _name = "meal.calendar.report.wizard"
    _description = "Wizard for Meal Calendar Report"


    date_from = fields.Date(string ="Start date", required =True)
    date_to = fields.Date(string ="End date", required =True)


    @api.constrains('date_to', 'date_from')
    def check_dates(self):
        date_range = (self.date_to - self.date_from).days + 1
        if self.date_to and self.date_from:
            if self.date_to < self.date_from:
                raise ValidationError(_("End date must be greate than Start date !!!"))
            elif self.print_pdf() and date_range > 7:
                raise ValidationError(_("Meal calendar can print only for 7 days"))

    def print_excel(self):
        data = {
            "date_from" : self.date_from,
            "date_to" : self.date_to
        }
        return self.env.ref("diet.action_meal_calendar_report").report_action(self, data =data, config =False)
    
    def pdf_preview(self):
        calendar = self.env['customer.meal.calendar'].search([('date','>=', self.date_from),('date','<=', self.date_to),'|',('state','=','active'),('state','=','active_with_meal')])
        customer ={}
        days1 = (self.date_to - self.date_from).days + 1
        date_list =[]
        company_id =self.env.company
        company =company_id.name
        street =company_id.street
        street2 =company_id.street2
        city =company_id.city
        state =company_id.state_id.name
        zip =company_id.zip
        country =company_id.country_id.name
        for i in range(days1):
            dates_available = self.date_from + timedelta(days=i)
            date_list.append(dates_available.strftime('%d-%m-%Y'))

        for records in calendar:
            id = records.partner_id.customer_sequence_no
            partner_name= records.partner_id.name
            plan = records.so_id.plan_id.name
            meal_type = records.meal_category_id.name
            meal_date = str(records.date)
            meal = records.meal_id.name
            if id not in customer:
                customer[id] = {"meal_type":{}, "plan":plan, "cus_name":partner_name}
            if meal_type not in customer[id]["meal_type"]:
                customer[id]["meal_type"][meal_type] = []

            customer[id]["meal_type"][meal_type].append({'date': meal_date, 'meal': meal})
        data = {
            "date_from" : self.date_from.strftime('%d-%m-%Y'),
            "date_to" : self.date_to.strftime('%d-%m-%Y'),
            "cus_dict": customer,
            "date_list":date_list,
            "company":company,
            "street":street,
            "street2":street2,
            "city": city,
            "state":state,
            "zip_code":self.env.company.zip,
            "country":country
        }
        return self.env.ref("diet.action_meal_calendar_report_preview").report_action(self, data =data, config =False)
    
    def print_pdf(self):
        calendar = self.env['customer.meal.calendar'].search([('date','>=', self.date_from),('date','<=', self.date_to),'|',('state','=','active'),('state','=','active_with_meal')])
        customer ={}
        days1 = (self.date_to - self.date_from).days + 1
        date_list =[]
        company_id =self.env.company
        company =company_id.name
        street =company_id.street
        street2 =company_id.street2
        city =company_id.city
        state =company_id.state_id.name
        zip =company_id.zip
        country =company_id.country_id.name
        for i in range(days1):
            dates_available = self.date_from + timedelta(days=i)
            date_list.append(dates_available.strftime('%d-%m-%Y'))

        for records in calendar:
            id = records.partner_id.customer_sequence_no
            partner_name= records.partner_id.name
            plan = ', '.join(plan.name for plan in calendar.mapped('so_id.plan_id'))
            meal_type = records.meal_category_id.name
            meal_date = str(records.date.strftime('%d-%m-%Y'))
            meal = records.meal_id.name
            if id not in customer:
                customer[id] = {"meal_type":{}, "plan":plan, "cus_name":partner_name}
            if meal_type not in customer[id]["meal_type"]:
                customer[id]["meal_type"][meal_type] = []

            existing_meal = next((item for item in customer[id]["meal_type"][meal_type] if item['date'] == meal_date), None)
            if existing_meal:
                existing_meal['meal'] += f", {meal}"
            else:
                customer[id]["meal_type"][meal_type].append({'date': meal_date, 'meal': meal})
        data = {
            "date_from" : self.date_from.strftime('%d-%m-%Y'),
            "date_to" : self.date_to.strftime('%d-%m-%Y'),
            "cus_dict": customer,
            "date_list":date_list,
            "company":company,
            "street":street,
            "street2":street2,
            "city": city,
            "state":state,
            "zip_code":self.env.company.zip,
            "country":country,
        }
        return self.env.ref("diet.action_meal_calendar_report_pdf").report_action(self, data =data, config =False)
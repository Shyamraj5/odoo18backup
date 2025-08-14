from odoo import models, fields



class DriverReportWizard(models.TransientModel):
    _name = "driver.report.wizard"
    _description = "Wizard for Driver Report"


    date = fields.Date(string ="Date", required =True)
    driver_id = fields.Many2one('area.driver', string =" Driver")


    def print_excel(self):
        data={
            "date" :self.date
        }
        return self.env.ref("diet.action_driver_report").report_action(self, data =data, config =False)
    
    def preview_report(self):
        domain =[('date', '=', self.date)]
        if self.driver_id:
            domain.append(('so_id.address_id.area_id','=',self.driver_id.service_area_ids.ids))
        meal_calendar =self.env['customer.meal.calendar'].search(domain)
        company_id =self.env.company
        company =company_id.name
        street =company_id.street
        street2 =company_id.street2
        city =company_id.city
        state =company_id.state_id.name
        zip =company_id.zip
        country =company_id.country_id.name
        driver_dict ={}
        for meals in meal_calendar:
            partner = meals.partner_id.customer_sequence_no
            area =meals.so_id.address_id.area_id.name
            address = meals.so_id.address_id
            partner_address = ""
            if address.zone_id:
                partner_address += address.zone_id.name
            if address.area_id:
                partner_address += ", " + address.area_id.name
            if address.street:
                partner_address += ", " + address.street
            if address.avenue:
                partner_address += ", Avenue: " + address.avenue
            if address.house_number:
                partner_address += " House No: " + address.house_number
            if address.floor_number:
                partner_address += ", Floor No:" + address.floor_number
            if address.apartment_no:
                partner_address += ", Apartment No: " + address.apartment_no
            cus_phone = ""
            if meals.partner_id.phone:
                cus_phone += "Phone: " + meals.partner_id.phone
            if meals.partner_id.mobile:
                cus_phone += ", "+ meals.partner_id.mobile
            drivers = self.env['area.driver'].search([('service_area_ids','=',meals.so_id.address_id.area_id.id)])
            if drivers:
                driver_code =drivers[0].code
                if driver_code not in driver_dict:
                    driver_dict[driver_code] ={area :{}, "driver" :drivers[0].name}
                if area not in driver_dict[driver_code]:
                    driver_dict[driver_code][area] = {partner:{"name":meals.partner_id.name, "shift":meals.partner_id.shift_id.shift,"address":partner_address, "phone": cus_phone}}
                if partner not in driver_dict[driver_code][area]:
                    driver_dict[driver_code][area][partner] ={"name":meals.partner_id.name, "shift":meals.partner_id.shift_id.shift,"address":partner_address, "phone": cus_phone}
            
        data ={
            "driver_dict": driver_dict,
            "date": self.date.strftime("%d-%m-%Y"),
            "company":company,
            "street":street,
            "street2":street2,
            "city": city,
            "state":state,
            "zip_code":self.env.company.zip,
            "country":country
        }
        return self.env.ref("diet.action_driver_report_preview").report_action(self, data =data, config =False)
    
    def pdf_report(self):
        domain =[('date', '=', self.date)]
        if self.driver_id:
            domain.append(('so_id.address_id.area_id','=',self.driver_id.service_area_ids.ids))
        meal_calendar =self.env['customer.meal.calendar'].search(domain)
        company_id =self.env.company
        company =company_id.name
        street =company_id.street
        street2 =company_id.street2
        city =company_id.city
        state =company_id.state_id.name
        zip =company_id.zip
        country =company_id.country_id.name
        driver_dict ={}
        for meals in meal_calendar:
            partner = meals.partner_id.customer_sequence_no
            area =meals.so_id.address_id.area_id.name
            drivers = self.env['area.driver'].search([('service_area_ids','=',meals.so_id.address_id.area_id.id)])
            
            
            address = meals.so_id.address_id
            partner_address = ""
            if address.zone_id:
                partner_address += address.zone_id.name
            if address.area_id:
                partner_address += ", " + address.area_id.name
            if address.street:
                partner_address += ", " + address.street
            if address.avenue:
                partner_address += ", Avenue: " + address.avenue
            if address.house_number:
                partner_address += " House No: " + address.house_number
            if address.floor_number:
                partner_address += ", Floor No:" + address.floor_number
            if address.apartment_no:
                partner_address += ", Apartment No: " + address.apartment_no
            cus_phone = ""
            if meals.partner_id.phone:
                cus_phone += "Phone: " + meals.partner_id.phone
            if meals.partner_id.mobile:
                cus_phone += ", "+ meals.partner_id.mobile
            if drivers:
                driver_code =drivers[0].code
                if driver_code not in driver_dict:
                    driver_dict[driver_code] ={area :{}, "driver" :drivers[0].name}
                if area not in driver_dict[driver_code]:
                    driver_dict[driver_code][area] = {partner:{"name":meals.partner_id.name, "shift":meals.partner_id.shift_id.shift, "address":partner_address, "phone": cus_phone}}
                if partner not in driver_dict[driver_code][area]:
                    driver_dict[driver_code][area][partner] ={"name":meals.partner_id.name, "shift":meals.partner_id.shift_id.shift,"address":partner_address, "phone": cus_phone}
            
        data ={
            "driver_dict": driver_dict,
            "date": self.date.strftime("%d-%m-%Y"),
            "company":company,
            "street":street,
            "street2":street2,
            "city": city,
            "state":state,
            "zip_code":self.env.company.zip,
            "country":country
        }
        return self.env.ref("diet.action_driver_report_pdf").report_action(self, data =data, config =False)
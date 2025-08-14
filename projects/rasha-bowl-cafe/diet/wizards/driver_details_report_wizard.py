from odoo import models, fields



class DriverDetailsReportWizard(models.TransientModel):
    _name = "driver.details.report.wizard"
    _description = "Wizard for Driver Details Report"


    area_id =fields.Many2one('customer.area', string ="Area")

        
    def print_excel(self):
        data ={
            "data": self.read()
            }
        return self.env.ref("diet.action_driver_details_report").report_action(self, data= data, config=False)
    def preview_report(self):
        driver_records =self.env['area.driver'].search([])
        company_id =self.env.company
        company =company_id.name
        street =company_id.street
        street2 =company_id.street2
        city =company_id.city
        state =company_id.state_id.name
        zip_code =company_id.zip
        country =company_id.country_id.name
        driver_list =[]
        for driver in driver_records:
            area_english =[]
            area_arabic =[]
            for area in driver.service_area_ids:
                area_english.append(area.name)
            vals ={
                "code" :driver.code,
                "name" :driver.name,
                "phone": driver.phone,
                "area_english":area_english,
            }
            driver_list.append(vals)
        data ={
            "driver_list": driver_list,
            "company":company,
            "street":street,
            "street2":street2,
            "city": city,
            "state":state,
            "zip_code":self.env.company.zip,
            "country":country
            }
        return self.env.ref("diet.action_driver_details_report_preview").report_action(self, data= data, config=False)
        
    def pdf_report(self):
        driver_records =self.env['area.driver'].search([])
        company_id =self.env.company
        company =company_id.name
        street =company_id.street
        street2 =company_id.street2
        city =company_id.city
        state =company_id.state_id.name
        zip_code =company_id.zip
        country =company_id.country_id.name
        driver_list =[]
        for driver in driver_records:
            area_english =[]
            area_arabic =[]
            for area in driver.service_area_ids:
                area_english.append(area.name)
            vals ={
                "code" :driver.code,
                "name" :driver.name,
                "phone": driver.phone,
                "area_english":area_english,
            }
            driver_list.append(vals)
        data ={
            "driver_list": driver_list,
            "company":company,
            "street":street,
            "street2":street2,
            "city": city,
            "state":state,
            "zip_code":self.env.company.zip,
            "country":country
            }
        return self.env.ref("diet.action_driver_details_report_pdf").report_action(self, data= data, config=False)
    
from odoo import models


class DriverReport(models.AbstractModel):
    _name = "report.driver_report_xlsx"
    _description = "Report for Drivers"
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
                    "valign": "vcenter",
                    "bg_color": "#8bc388"
            }
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
                })
        format1d =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "center",
                    "valign": "vcenter",
            }
        )
        format1e =workbook.add_format(
            {
                    "font_size": 18,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "center",
                    "bold": True,
                    "valign": "vcenter",
                    "bg_color": "#8bc388",
                    "color":"white"
            }
        )
        domain =[('date', '=', lines.date)]
        if lines.driver_id:
            domain.append(('so_id.address_id.area_id','=',lines.driver_id.service_area_ids
            .id))
        meal_calendar =self.env['customer.meal.calendar'].search(domain)
        driver_dict ={}
        for meals in meal_calendar:
            partner = meals.partner_id.customer_sequence_no
            area =meals.so_id.address_id.area_id.name
            address =meals.so_id.address_id
            partner_address = ""
            if address.zone_id:
                partner_address += address.zone_id.name
            if address.area_id:
                partner_address += ", " + address.area_id.name
            if address.street:
                partner_address += ", " + address.street
            if address.avenue:
                partner_address += """\nAvenue: """ + address.avenue
            if address.house_number:
                partner_address += " House No: " + address.house_number
            if address.floor_number:
                partner_address += ", Floor No:" + address.floor_number
            if address.apartment_no:
                partner_address += """\nApartment No: """ + address.apartment_no
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
                    driver_dict[driver_code][area][partner] ={"name":meals.partner_id.name, "shift":meals.partner_id.shift_id.shift, "address":partner_address, "phone": cus_phone}
            
        for name, vals in driver_dict.items():
            worksheet = workbook.add_worksheet(name.upper() + " DELIVERY DAILY REPORT")
            worksheet.merge_range("A1:C1", "FEED", format1e)
            worksheet.merge_range("A2:C2", "DRIVER DELIVERY DAILY REPORT                                                                                      "+ "Date : " + lines.date.strftime("%d-%m-%Y"), format1a)
            worksheet.set_row(0, 50)
            worksheet.set_row(1, 30)
            worksheet.set_row(2, 20)
            worksheet.set_row(3, 20)
            worksheet.set_column("A:A", 5)
            worksheet.set_column("B:B", 40)
            worksheet.set_column("C:C", 70)
            row = 4
            i = 0
            boxes = 0
            
            for areas, val in vals.items():
                if areas != 'driver':
                    worksheet.merge_range("A%s:C%s"%(row,row), "Area: " + areas + "           " 
                                          +"                                                                Count: "+ str(len(val)-1), format1c)
                    boxes += (len(val)- 1)
                    row +=1
                    for cus, details in val.items():
                        
                        if cus != 'arabic':
                            i += 1
                            worksheet.merge_range("A%s:A%s"%(row,row+4), str(int(i)),format1d)
                            if details['shift']:
                                worksheet.merge_range("B%s:B%s"%(row,row+4), cus + "           "+ details['name'] +"\n"+"\n"+ details['shift'],format1b)
                            else:
                                worksheet.merge_range("B%s:B%s"%(row,row+4), cus + "           "+ details['name'] +"\n"+"\n",format1b)
                            worksheet.merge_range("C%s:C%s"%(row,row+4),details['address'] +"\n"+details['phone'],format1b)
                            row+=6
            worksheet.merge_range("A3:C3", "Driver: " + vals['driver'] + "                                       "+"Driver Code : " + name + "                                       "+ "Boxes: "+ str(boxes), format1a)


                
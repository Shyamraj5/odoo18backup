from odoo import models, fields
from datetime import datetime, timedelta , date


class DeliveryReport(models.AbstractModel):
    _name = "report.delivery_report_xlsx"
    _description = "Report for Delivery Report"
    _inherit = "report.report_xlsx.abstract"


    def generate_xlsx_report(self, workbook, data, lines):
        main_head = workbook.add_format({
            "font_size": 20,
            "bottom": True,
            "right": True,
            "left": True,
            "top": True,
            "align": "center",
            "bold": True,
            "valign": "vcenter",
            "bg_color": "#eb3489",
            "font_color": "#ffffff"
        })

        sub_head = workbook.add_format({
            "font_size": 11,
            "bottom": True,
            "right": True,
            "left": True,
            "top": True,
            "bold" : True,
            "valign": "vcenter",
            "align" : "center"
        })
        
        right_align_format = workbook.add_format({'align': 'right'})
        center_align_format = workbook.add_format({'align': 'center'})

        date = data.get('date')
        status = data.get('status')
        shift = data.get('shift_id')
        customer_tag_ids = data.get('customer_tag_ids', [])

        worksheet = workbook.add_worksheet("Delivery Report")
        worksheet.merge_range(
            0,0,0,13, "DELIVERY REPORT", main_head
        )
        worksheet.set_row(0, 40)
        worksheet.set_row(1, 30)
        worksheet.set_column("A:A", 3)
        worksheet.set_column("B:B",30)
        worksheet.set_column("C:C",12)
        worksheet.set_column("D:D",12)
        worksheet.set_column("E:E",14)
        worksheet.set_column("F:F",12)
        worksheet.set_column("G:G",10)
        worksheet.set_column("H:H",20)
        worksheet.set_column("I:I",10)
        worksheet.set_column("J:J",15)
        worksheet.set_column("K:K",15)
        worksheet.set_column("L:L",12)
        worksheet.set_column("M:M",12)
        worksheet.set_column("N:N",15)
        
        worksheet.write("A2", "Q#", sub_head)
        worksheet.write("B2", "Name", sub_head)
        worksheet.write("C2", "ID", sub_head)
        worksheet.write("D2", "Tag", sub_head)
        worksheet.write("E2", "Mobile", sub_head)
        worksheet.write("F2", "Shift", sub_head)
        worksheet.write("G2", "City", sub_head)
        worksheet.write("H2", "District", sub_head)
        worksheet.write("I2", "Street", sub_head)
        worksheet.write("J2", "House No", sub_head)
        worksheet.write("K2", "Floor No", sub_head)
        worksheet.write("L2", "Delivery Date", sub_head)
        worksheet.write("M2", "Start Date", sub_head)
        worksheet.write("N2", "End Date", sub_head)
        
        query_params = [date]
        query = """
            SELECT
                partner.id AS partner_id,
                partner.full_name AS name,
                partner.customer_sequence_no AS customer_no,
                partner.phone AS phone,
                drv_order.delivery_queue_number AS queue_number,
                drv_order.date AS date,
                plan.short_code AS plan_code,
                subscription.order_number AS order_number,
                subscription.pc_combination AS pc_combination,
                district.name AS district,
                city.name AS city,
                address.street AS street,
                address.house_number AS house_no,
                address.floor_number AS floor_no,
                address.apartment_no AS apartment_no,
                address.jedha AS jedha,
                shift.shift AS shift,
                subscription.actual_start_date AS start_date,
                subscription.end_date AS end_date,
                subscription.id AS subscription_id,
                drv_order.id AS order_id
            FROM
                driver_order AS drv_order
            JOIN res_partner AS partner ON drv_order.customer_id = partner.id
            JOIN diet_subscription_order AS subscription ON drv_order.subscription_id = subscription.id
            JOIN subscription_package_plan AS plan ON subscription.plan_id = plan.id
            JOIN res_partner AS address ON address.id = drv_order.address_id
            JOIN customer_district AS district ON district.id = address.district_id
            JOIN res_country_state AS city ON city.id = address.state_id
            JOIN customer_shift AS shift ON shift.id = drv_order.shift_id
            WHERE
                drv_order.date = %s
        """
        if shift:
            query += " AND drv_order.shift_id = %s"
            query_params.append(shift)
        if status:
            if status == 'pending':
                delivery_status = ['pending']
            elif status == 'delivered':
                delivery_status = ['delivered']
            elif status == 'not_delivered':
                delivery_status = ['not_delivered']
            else:
                delivery_status = ['pending', 'delivered', 'not_delivered']
            query += " AND drv_order.status in %s"
            query_params.append(tuple(delivery_status))
        query += """
            ORDER BY
                drv_order.delivery_queue_number
        """
        self.env.cr.execute(query, tuple(query_params))
        result = self.env.cr.dictfetchall()

        row = 2
        col = 0
        for data in result:
            customer = self.env['res.partner'].search([('id', '=', data['partner_id'])])
            if customer_tag_ids:
                customer_tags = self.env['res.partner.category'].browse(customer_tag_ids)
                if customer.category_id not in customer_tags:
                    continue
            tags_string = ', '.join(customer.category_id.mapped('name'))
            worksheet.write(row, col, data.get('queue_number', ''))
            worksheet.write(row, col+1, data.get('name'))
            worksheet.write(row, col+2, data.get('customer_no', ''))
            worksheet.write(row, col+3, tags_string or '', center_align_format)
            worksheet.write(row, col+4, data.get('phone', ''), center_align_format)
            worksheet.write(row, col+5, data.get('shift', ''))
            worksheet.write(row, col+6, data.get('city', ''))
            worksheet.write(row, col+7, data.get('district', ''))
            worksheet.write(row, col+8, data.get('street', ''))
            worksheet.write(row, col+9, data.get('house_no', ''),right_align_format)
            worksheet.write(row, col+10, data.get('floor_no', ''),right_align_format)
            delivery_date = fields.Date.from_string(date).strftime('%b %d, %Y')
            start_date = fields.Date.from_string(data.get('start_date', '')).strftime('%b %d, %Y')
            end_date = fields.Date.from_string(data.get('end_date', '')).strftime('%b %d, %Y')
            worksheet.write(row, col+11, delivery_date, center_align_format)
            worksheet.write(row, col+12, start_date, center_align_format)
            worksheet.write(row, col+13, end_date, center_align_format)
            row += 1

        

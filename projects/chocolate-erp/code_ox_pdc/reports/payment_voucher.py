from odoo import models
import io
import base64
import xlsxwriter
import os


class PaymentVoucherXlsx(models.AbstractModel):
    _name = 'report.code_ox_pdc.report_payment_voucher_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Payment Vocher Report"

    def generate_xlsx_report(self, workbook, data, payment_vouchers):
        worksheet = workbook.add_worksheet("Payment Voucher")
        bold_centered = workbook.add_format({'bold': True,'align': 'center','font_color': '#3944BC','border': 5,'font_size': 18,'bg_color': '#F0F0F0'})
        bold_centered1 = workbook.add_format({'bold': True,'align': 'center','font_color': '#3944BC','border': 2,'font_size': 12,'bg_color': '#cfe2f3'})
        bold_left1 = workbook.add_format({'bold': True,'align': 'left','border': 2,'font_size': 14,'font_color': '#3944BC'})
        bold_left = workbook.add_format({'bold': True,'align': 'left','border': 2,})
        text_format = workbook.add_format({'align': 'left','border': 2})
        number_format = workbook.add_format({'align': 'right', 'num_format': '#,##0.00','border': 2})
        number_format1 = workbook.add_format({'align': 'right', 'num_format': '#,##0.00','border': 2,'bold': True})# To format numbers
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'align': 'left' ,'border': 2})
        worksheet.set_column("A:A", 10)
        worksheet.set_column("B:B", 20)
        logo_path = '//bi_pdc/static/mohideen.png'
        worksheet.insert_image('A2:D7', logo_path, {'x_scale': 0.11, 'y_scale': 0.11})

        worksheet.merge_range('A2:D7', '')
        worksheet.merge_range('E2:R7', '')
        worksheet.merge_range('A8:R8', '', bold_centered)
        worksheet.merge_range('A9:R10', 'PAYMENT VOUCHER', bold_centered)
        if payment_vouchers:
            payment_voucher = payment_vouchers[0]
            company_name = self.env.company.name
            company_address = self._get_company_address(payment_voucher.company_id)
            company_email = payment_voucher.company_id.email
            worksheet.merge_range('A11:D12', '')
            worksheet.merge_range('A13:D13', '')
            worksheet.merge_range('A14:D14', '')
            worksheet.write('A11:D12', company_name, bold_left1)
            worksheet.write('A13:D13', company_address, text_format)
            worksheet.write('A14:D14', company_email, text_format)
            worksheet.merge_range('E11:H14', '')
            worksheet.merge_range('I11:J11', 'PARTY:',bold_left)
            worksheet.merge_range('K11:R11', payment_voucher.partner_id.name, text_format)
            worksheet.merge_range('I12:J12', 'Voucher No:',bold_left)
            worksheet.merge_range('K12:R12', payment_voucher.name, text_format)
            worksheet.merge_range('I13:J13', 'Date:',bold_left)
            worksheet.merge_range('K13:R13', str(payment_voucher.date), text_format)
            worksheet.merge_range('I14:J14', 'Pay mode:',bold_left)
            worksheet.merge_range('K14:R14', 'PDC', text_format)
            worksheet.merge_range('A15:R15', '', bold_centered)
            worksheet.merge_range('A16:D17', 'Transaction Type : PDC',bold_centered1)
            payment_date = str(payment_voucher.date)
            worksheet.merge_range('E16:H17',  f'Dated On: {payment_date}', bold_centered1)
            account_name = payment_voucher.account_id.name if payment_voucher.account_id else 'N/A'
            worksheet.merge_range('I16:R17', f'Drawn On: {account_name}', bold_centered1)
            amount = payment_voucher.check_amount
            currency_symbol = self.env.company.currency_id.symbol
            worksheet.merge_range('A18:D19', f'Amount : {currency_symbol}{amount}', bold_centered1)
           
            worksheet.merge_range('A20:R20','',bold_centered)
            row = 22
            worksheet.merge_range('A21:B22','Date Issued',bold_left1)
            worksheet.merge_range('C21:D22', 'Description',bold_left1)
            worksheet.merge_range('E21:F22', 'Bill Reference', bold_left1)
            worksheet.merge_range('G21:H22', 'Orig. Amount',bold_left1)
            worksheet.merge_range('I21:J22', 'Deduction',bold_left1)
            worksheet.merge_range('K21:L22', 'Due Date',bold_left1)
            worksheet.merge_range('M21:N22', 'Balance', bold_left1)
            worksheet.merge_range('O21:P22', 'Amount to be Paid', bold_left1)
            worksheet.merge_range('Q21:R22', 'Applied Amount', bold_left1)

            total_applied_amount = 0.0
            row = 23
            for payment_voucher in payment_vouchers:
                for payment_line in payment_voucher.payment_line_ids.filtered(lambda a: a.amountpaid != 0.0):
                    if payment_line:
                        bill = payment_line.invoice_id
                        date_issued = payment_line.invoice_date or ''
                        description = payment_line.invoice_no or ''
                        orig_amount = payment_line.amount or 0.0
                        deduction = 0.0
                        applied_amount = orig_amount - deduction
                        move_ref = payment_line.move_ref
                        balance = payment_line.balance
                        duedate =payment_line.invoice_duedate
                        amountpaid = payment_line.amountpaid
                        refund_bills = self.env['account.move'].search([
                            ('reversed_entry_id', '=', bill.id),
                            ('move_type', '=', 'in_refund'),
                            ('state', '=', 'posted')
                        ])

                        if refund_bills:
                            deduction = sum(refund.amount_total for refund in refund_bills)
                            applied_amount = orig_amount - deduction
                        total_applied_amount += applied_amount

                        worksheet.merge_range(f'A{row}:B{row}', date_issued if date_issued else '',
                                              date_format)  # Date Issued
                        worksheet.merge_range(f'C{row}:D{row}', description, text_format)  # Description
                        worksheet.merge_range(f'E{row}:F{row}', move_ref, text_format)
                        worksheet.merge_range(f'G{row}:H{row}', orig_amount, number_format)  # Orig. Amount
                        worksheet.merge_range(f'I{row}:J{row}', deduction if deduction > 0 else 0.0,
                                              number_format)  # Deduction
                        worksheet.merge_range(f'K{row}:L{row}', duedate, date_format) # Due Date
                        worksheet.merge_range(f'M{row}:N{row}', balance, number_format)  # Balance
                        worksheet.merge_range(f'O{row}:P{row}', amountpaid,number_format )   # Amount to be Paid
                        worksheet.merge_range(f'Q{row}:R{row}', applied_amount, number_format)  # Applied Amount

                        row += 1
            worksheet.merge_range(f'I{row}:K{row}', 'TOTAL', bold_centered1)
            worksheet.merge_range(f'L{row}:R{row}', total_applied_amount, number_format1)
            worksheet.merge_range('E18:R19', f'Amount in words: {payment_voucher.currency_id.amount_to_text(total_applied_amount)}', bold_centered1)
            row += 1
            company_name = self.env.company.name
            message = f"Make all checks payable to {company_name}"
            worksheet.merge_range(f'A{row}:R{row}', message, bold_centered1)
            row += 1
            thank_you_message = "THANK YOU FOR YOUR BUSINESS!"
            worksheet.merge_range(f'A{row}:R{row}', thank_you_message,
                                  bold_centered1)
            row += 1
            remarks="Remarks :"
            worksheet.merge_range(f'A{row}:N{row}',remarks,bold_left)

            row += 1
            worksheet.merge_range(f'A{row}:D{row}',"Prepared By :",bold_left)
            worksheet.merge_range(f'E{row}:I{row}', "Verified By :", bold_left)
            worksheet.merge_range(f'J{row}:N{row}', "Approved By :", bold_left)
            worksheet.merge_range(f'O{row}:R{row}', "Authorised By :", bold_left)

            row += 2


            worksheet.merge_range(f'A{row}:C{row}', "Received By :", bold_left1)
            row += 1
            worksheet.merge_range(f'A{row}:C{row}', "Name :", bold_left)
            row += 1
            worksheet.merge_range(f'A{row}:C{row}', "Designation :", bold_left)
            row += 1
            worksheet.merge_range(f'A{row}:C{row}', "Signature :", bold_left)
            row += 1
            worksheet.merge_range(f'A{row}:C{row}', "Date :", bold_left)
            row += 1
            worksheet.merge_range(f'A{row}:C{row}', "Mobile Number :", bold_left)


    def _get_company_address(self, company):
        address_parts = []
        if company.street:
            address_parts.append(company.street)
        if company.street2:
            address_parts.append(company.street2)
        if company.city:
            address_parts.append(company.city)
        if company.state_id:
            address_parts.append(company.state_id.name)
        if company.zip:
            address_parts.append(company.zip)
        if company.country_id:
            address_parts.append(company.country_id.name)
        return ", ".join(address_parts) if address_parts else "No Address Available"

   
    def _get_related_bills(self, payment_voucher):
        bills = self.env['account.move'].search([
            ('invoice_id', '=', payment_voucher.id),
            ('state', 'in', ['draft', 'posted']),
        ])
        return bills


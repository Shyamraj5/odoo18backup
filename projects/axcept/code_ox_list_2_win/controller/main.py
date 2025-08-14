from odoo import http
from odoo.http import request, Response
import json
import base64
from datetime import datetime
from odoo import fields
from .token_utils import validate_token


class List2WinController(http.Controller):
    
    def _prepare_response(self, statusOk, statusCode, message, payload, error):
        """
        Standardize API response with status codes
        """
        return request.make_response(
            json.dumps({
            "statusOk": statusOk,
            "statusCode": statusCode,
            "message": message,
            "payload": payload,
            "error": error
        }), 
            headers=[('Content-Type', 'application/json')],
            status=statusCode
        )
    
    def get_base_url(self):
        return request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    
    @http.route('/invoice/<string:invoice_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_invoice_pdf(self, invoice_id):
        """Get invoice pdf for public access"""
        try:
            invoice = request.env['account.move'].sudo().browse(int(invoice_id))
            if not invoice.exists():
                return self._prepare_response(False, 404, "", None, "Invoice not found")

            report_action = request.env.ref('account.account_invoices').sudo()
            pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(report_action.report_name, [invoice.id])
            
            if not pdf_content:
                return self._prepare_response(False, 404, "", None, "PDF could not be generated")

            headers = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', f'attachment; filename=invoice_{invoice_id}.pdf')
            ]

            return request.make_response(pdf_content, headers=headers)

        except (ValueError, Exception) as e:
            return self._prepare_response(False, 500, "", None, str(e))
    
    @http.route('/auth/login', type='http', auth='public', methods=['POST'], csrf=False)
    def authenticate(self):
        """
        Mobile/Web app authentication endpoint with status codes
        """
        try:
            # Parse JSON data
            params = json.loads(request.httprequest.data)
            username = params.get('username')
            password = params.get('password')

            # Validate input
            if not username or not password:
                return self._prepare_response(
                    False, 400, "", None, 'Missing username or password'
                )

            # Authenticate
            db = request.env.cr.dbname
            try:
                credential = {'login': username, 'password': f"{password}", 'type': 'password'}
                uid = request.session.authenticate(db, credential)
                if not uid:
                    return self._prepare_response(False, 401, "", None, 'Invalid Credentials')
                
                # Generate access token
                user = request.env['res.users'].sudo().browse(uid.get('uid'))
                token = request.env['mobile.api.token'].sudo().create_token(user)
                return self._prepare_response(
                    statusOk=True,
                    statusCode=200,
                    message='Authentication successful',
                    payload={
                        'token': token,
                        'user_id': user.id,
                        'name': user.name,
                        'email': user.email,
                    },
                    error=None
                    )
            
            except Exception as e:
                return self._prepare_response(
                    False, 500, "", None, "Authentication failed"
                )
        
        except json.JSONDecodeError:
            return self._prepare_response(
                False, 400, "", None, "Invalid JSON")
        except Exception as e:
            return self._prepare_response(
                False, 500, "", None, str(e)
            )

    @validate_token
    @http.route('/api/be/renew/<be_id>', type='http', auth='public', methods=['POST'], csrf=False)
    def be_membership_renewal(self, be_id, **kwargs):
        if not be_id:
            return self._prepare_response(
                False, 400, "Missing be_id parameter", None, "be_id is required"
            )

        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
        except ValueError:
            return self._prepare_response(
                False, 400, "Invalid JSON data", None, "Request body must be valid JSON"
            )

        partner = request.env['res.partner'].sudo().search([('be_code', '=', be_id)], limit=1)
        if not partner:
            return self._prepare_response(
                False, 404, f"No partner found with be_code: {be_id}", None, "Partner not found"
            )

        payment_details = data.get('payment_details', {})
        profile = data.get('profile')
        update_vals = {}

        if profile:
            if 'country_id' in profile:
                country = request.env['res.country'].sudo().browse(int(profile['country_id']))
                if not country.exists():
                    return self._prepare_response(
                        False, 400, "Invalid country", None,
                        f"Country ID '{profile['country_id']}' not found."
                    )
                update_vals['country_id'] = country.id

            if 'state_id' in profile:
                state = request.env['res.country.state'].sudo().browse(int(profile['state_id']))
                if not state.exists():
                    return self._prepare_response(
                        False, 400, "Invalid state", None,
                        f"State ID '{profile['state_id']}' not found."
                    )
                update_vals['state_id'] = state.id

            if 'district_id' in profile:
                district = request.env['res.district'].sudo().browse(int(profile['district_id']))
                if not district.exists():
                    return self._prepare_response(
                        False, 400, "Invalid district", None,
                        f"District ID '{profile['district_id']}' not found."
                    )
                update_vals['district'] = district.id

        # Validate required fields
        missing_fields = [field for field in ['payment_date'] if field not in payment_details]
        if missing_fields:
            return self._prepare_response(
                False, 400, "Missing required payment fields", None,
                f"Missing fields in payment_details: {', '.join(missing_fields)}"
            )
        payment_method_str = payment_details.get('payment_method')
        axcept_method = request.env['axcept.payment.method'].sudo().search([
            ('name', '=', payment_method_str)
        ], limit=1)

        if not axcept_method:
            axcept_method = request.env['axcept.payment.method'].sudo().create({
                'name': payment_method_str
            })

        journals = request.env['account.journal'].sudo().search([
                ('default_bank_payment_method', '=', True),
            ], limit=1)

        payment_date = payment_details.get('payment_date')

        try:
            renewal_product = request.env.ref('code_ox_list_2_win.renewal_service_product_corn').sudo()
        except ValueError:
            return self._prepare_response(
                False, 404, "Renewal product not found", None, "External ID 'renewal_service_product_corn' not found"
            )

        if not renewal_product:
            return self._prepare_response(
                False, 404, "Renewal product not found", None, "Product with default_code 'RENEWAL' not found"
            )

        invoice_lines = []
        for line in payment_details.get('lines', []):
            line_vals = {
                'product_id': renewal_product.id,
                'quantity': line.get('quantity', 1),
                'price_unit': line.get('price_unit', 0.0),
            }

            if line.get('discount'):
                line_vals['discount'] = line['discount']

            if line.get('tax_ids'):
                line_vals['tax_ids'] = [(6, 0, line['tax_ids'])]

            invoice_lines.append((0, 0, line_vals))

        invoice_vals = {
            'partner_id': partner.id,
            'move_type': 'out_invoice',
            'invoice_date': payment_date,
            'invoice_line_ids': invoice_lines,
        }

        if payment_details.get('narration'):
            invoice_vals['narration'] = payment_details['narration']

        invoice = request.env['account.move'].sudo().create(invoice_vals)
        invoice.action_post()
        payment_journal = journals[0]
        payment_method_line = payment_journal.inbound_payment_method_line_ids[0]
        invoice_lines = invoice.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')

        # Create payment
        payment_vals = {
            'amount': invoice.amount_total,
            'journal_id': payment_journal.id,
            'partner_id': partner.id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'payment_method_line_id': payment_method_line.id,
            'payment_date': payment_date,
            'communication': invoice.name,
            'line_ids': [(6, 0, invoice_lines.ids)],
        }

        payment = request.env['account.payment.register'].sudo().create(payment_vals)
        payment.action_create_payments()
        invoice_id = invoice.id

        # Update existing partner from profile if provided
        if profile:
            direct_fields = [
                'email', 'last_name', 'gender', 'dob',
                'post_office', 'zip', 'city', 'aadhar_no',
                'father_name', 'mother_name', 'image_1920', 'education_qualification', 'phone'
            ]
            for field in direct_fields:
                if field in profile:
                    update_vals[field] = profile[field]

            if 'pancard_no' in profile and profile['pancard_no']:
                update_vals['l10n_in_pan'] = profile['pancard_no']

            if 'first_name' in profile and profile['first_name']:
                update_vals['name'] = profile['first_name']

            if 'house_no' in profile and profile['house_no']:
                update_vals['street'] = profile['house_no']

            partner.sudo().write(update_vals)
        base_url = self.get_base_url()
        payload_data = {
            'invoice_id': invoice_id,
            'pdf': f'{base_url}/invoice/{invoice_id}' if invoice_id else None,
            'invoice_number': invoice.name,
            'payment_id': payment.id,
            'partner_id': partner.id,
            'partner_name': partner.name,
        }

        return self._prepare_response(
            True, 201, "Membership Renewal Created", payload_data, None
        )

    @validate_token
    @http.route('/api/be/registration', type='http', auth='public', methods=['POST'], csrf=False)
    def register_be(self):
        data = json.loads(request.httprequest.data)

        be_details = data.get('be_details')
        payment_details = data.get('payment_details')
        bank_details = data.get('bank_details')
        referring_be = data.get('referring_be')

        required_be_fields = [
            'be_code', 'email', 'first_name', 'last_name', 'gender',
            'lsgd_name', 'country_id', 'state_id', 'district_id'
        ]

        existing_be = request.env['res.partner'].sudo().search([
            ('be_code', '=', be_details.get('be_code'))
        ], limit=1)

        if existing_be:
            return self._prepare_response(
                False,
                400,
                f"BE already exists with BE Code {be_details.get('be_code')}",
                None,
                f"A Business Executive with BE Code {be_details.get('be_code')} already exists. Registration Cancelled."
            )

        if not be_details:
            return self._prepare_response(
                False, 400, "", None, "Missing required key: be_details is mandatory."
            )

        missing_be_fields = [field for field in required_be_fields if not be_details.get(field)]
        if missing_be_fields:
            return self._prepare_response(
                False, 400, "", None, f"Missing - {', '.join(missing_be_fields)}"
            )

        district_rec = request.env['res.district'].sudo().browse(int(be_details.get('district_id')))
        if not district_rec.exists():
            return self._prepare_response(
                False,
                400,
                f"District ID '{be_details.get('district_id')}' not found.",
                None,
                f"Invalid District ID: {be_details.get('district_id')}"
            )
        district_id = district_rec.id

        country_rec = request.env['res.country'].sudo().browse(int(be_details.get('country_id')))
        if not country_rec.exists():
            return self._prepare_response(
                False,
                400,
                f"Country ID '{be_details.get('country_id')}' not found or invalid.",
                None,
                f"Invalid Country ID: {be_details.get('country_id')}"
            )
        country_id = country_rec.id

        state_rec = request.env['res.country.state'].sudo().browse(int(be_details.get('state_id')))
        if not state_rec.exists():
            return self._prepare_response(
                False,
                400,
                f"State ID '{be_details.get('state_id')}' not found or invalid.",
                None,
                f"Invalid State ID: {be_details.get('state_id')}"
            )
        state_id = state_rec.id

        if bank_details:
            if bank_details.get('account_number') != bank_details.get('confirm_account_number'):
                return self._prepare_response(
                    False, 400, "Bank account number mismatch", None,
                    "Account number and confirm account number do not match"
                )

        if payment_details:
            if 'payment_date' not in payment_details:
                return self._prepare_response(
                    False, 400, "Missing required payment fields", None,
                    "Missing field in payment_details: payment_date"
                )

            payment_method_str = payment_details.get('payment_method')
            axcept_method = request.env['axcept.payment.method'].sudo().search([
                ('name', '=', payment_method_str)
            ], limit=1)

            if not axcept_method:
                axcept_method = request.env['axcept.payment.method'].sudo().create({
                    'name': payment_method_str
                })

            journals = request.env['account.journal'].sudo().search([
                ('default_bank_payment_method', '=', True),
            ], limit=1)

            registration_product = request.env.ref('registration_service_product_corn', raise_if_not_found=False)
            if not registration_product:
                registration_product = request.env['product.product'].sudo().search([
                    ('default_code', '=', 'REGISTRATION'),
                    ('type', '=', 'service')
                ], limit=1)

            if not registration_product:
                return Response(json.dumps({
                    'status': 'error',
                    'message': "Registration product not found."
                }), content_type='application/json', status=400)

        if referring_be:
            ref_be_code = referring_be.get('be_code')
            ref_amount = referring_be.get('amount')

            if ref_be_code and ref_amount:
                referring_partner = request.env['res.partner'].sudo().search([
                    ('be_code', '=', ref_be_code)
                ], limit=1)

                if not referring_partner:
                    return self._prepare_response(
                        False, 404, "Referring BE not found", None,
                        f"No BE found with be_code: {ref_be_code}"
                    )

                try:
                    float(ref_amount)
                except ValueError:
                    return self._prepare_response(
                        False, 400, "Invalid referring_be amount", None,
                        "Amount must be a valid number."
                    )


        partner_created = False

        if existing_be:
            partner = existing_be
        else:
            partner_vals = {
                'be_code': be_details.get('be_code'),
                'email': be_details.get('email'),
                'name': be_details.get('first_name'),
                'last_name': be_details.get('last_name'),
                'gender': be_details.get('gender', '').lower(),
                'dob': be_details.get('dob'),
                'street': be_details.get('house_no'),
                'post_office': be_details.get('post_office'),
                'lsgd_name': be_details.get('lsgd_name'),
                'zip': be_details.get('pincode'),
                'country_id': country_id,
                'state_id': state_id,
                'district': district_id,
                'city': be_details.get('city'),
                'aadhar_no': be_details.get('aadhar_no'),
                'l10n_in_pan': be_details.get('pancard_no'),
                'father_name': be_details.get('father_name'),
                'mother_name': be_details.get('mother_name'),
                'image_1920': be_details.get('image_1920'),
                'education_qualification': be_details.get('education_qualification'),
                'phone': be_details.get('phone'),
                'is_company': False,
                'company_type': 'person',
                'customer_rank': 1,
                'is_be': True
            }
            partner = request.env['res.partner'].sudo().create(partner_vals)
            partner_created = True

        if bank_details:
            bank = request.env['res.bank'].sudo().search([
                ('bic', '=', bank_details.get('ifsc_code'))
            ], limit=1)
            if not bank:
                bank = request.env['res.bank'].sudo().create({
                    'name': bank_details.get('bank_name'),
                    'bic': bank_details.get('ifsc_code'),
                    'branch': bank_details.get('bank_branch')
                })

            request.env['res.partner.bank'].sudo().create({
                'partner_id': partner.id,
                'bank_id': bank.id,
                'acc_number': bank_details.get('account_number'),
                'account_type': bank_details.get('account_type'),
            })

        invoice_id = None
        pdf_content = None
        if payment_details:
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'invoice_date': payment_details.get('payment_date'),
                'invoice_date_due': payment_details.get('payment_date'),
                'invoice_line_ids': []
            }

            invoice_lines = []
            for line in payment_details.get('lines', []):
                invoice_lines.append((0, 0, {
                    'product_id': registration_product.id,
                    'quantity': line.get('quantity', 1),
                    'price_unit': line.get('price_unit', 0),
                    'discount': line.get('discount', 0),
                    'tax_ids': [(6, 0, line.get('tax_ids', []))],
                }))

            invoice_vals['invoice_line_ids'] = invoice_lines

            invoice = request.env['account.move'].sudo().create(invoice_vals)
            invoice.action_post()
            invoice_id = invoice.id

            journals = request.env['account.journal'].sudo().search([
                ('default_bank_payment_method', '=', True),
            ], limit=1)
            payment_journal = journals[0]
            payment_method_line = payment_journal.inbound_payment_method_line_ids[0]

            payment_vals = {
                'amount': invoice.amount_total,
                'journal_id': payment_journal.id,
                'partner_id': partner.id,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'payment_method_line_id': payment_method_line.id,
                'payment_date': payment_details.get('payment_date'),
                'communication': invoice.name,
                'line_ids': [(6, 0, invoice.line_ids.filtered(
                    lambda l: l.account_id.account_type == 'asset_receivable').ids)],
            }

            payment = request.env['account.payment.register'].sudo().create(payment_vals)
            payment.action_create_payments()

        if referring_be:
            wallet = request.env['wallet.wallet'].sudo().search([
                ('customer_id', '=', referring_partner.id)
            ], limit=1)

            if not wallet:
                wallet = request.env['wallet.wallet'].sudo().create({
                    'customer_id': referring_partner.id
                })

            request.env['wallet.received'].sudo().create({
                'wallet_id': wallet.id,
                'amount': float(referring_be.get('amount')),
            })
            vendor_bill_vals = {
                    'move_type': 'in_invoice',
                    'partner_id': referring_partner.id,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': []
                }
            
            try:
                referral_product = request.env.ref('code_ox_list_2_win.referral_commission_service_product_corn').sudo()
            except ValueError:
                return self._prepare_response(False, 404, "Referral product not found", None,
                                              "External ID 'referral_commission_service_product_corn' not found")
            
            tax_ids = referring_be.get('tax_ids', [])
            tds_tax = request.env['account.tax'].sudo().search([('name', '=', '5% TDS 194H P')], limit=1)
            if tds_tax:
                tax_ids.append(tds_tax.id)

            invoice_line = (0, 0, {
                'product_id': referral_product.id,
                'quantity': 1,
                'price_unit': ref_amount,
                'name': 'Referral Amount',
                'tax_ids': [(6, 0, tax_ids)]
            })

            vendor_bill_vals['invoice_line_ids'] = [invoice_line]
            vendor_bill = request.env['account.move'].sudo().create(vendor_bill_vals)
            vendor_bill.action_post()
            amount = vendor_bill.amount_total
            invoice_lines = vendor_bill.line_ids.filtered(lambda l: l.account_id.account_type == 'liability_payable')

        base_url = self.get_base_url()
        return self._prepare_response(
            True,
            200,
            'BE created successfully.' if partner_created else 'Partner already exists, new invoice created.',
            {
                'be_code': be_details.get('be_code'),
                'customer_id': partner.id,
                'invoice_id': invoice_id,
                'pdf': f'{base_url}/invoice/{invoice_id}' if payment_details else None,
                'referral_receipt_pdf': f'{base_url}/invoice/{vendor_bill.id}' if referring_be else None
            },
            None
        )
    
    @validate_token
    @http.route('/api/advertisement/<string:be_code>', type='http', auth='public', methods=['POST'], csrf=False)
    def create_advertisement_bo(self, be_code):
        try:
            data = json.loads(request.httprequest.data)
        except Exception:
            return self._prepare_response(False, 400, "Invalid JSON", None, "Request body must be valid JSON.")

        payment_details = data.get('payment_details')
        referring_be = data.get('referring_be')

        required_bo_fields = ['bo_code']

        missing_bo_fields = [field for field in required_bo_fields if field not in data]
        if missing_bo_fields:
            return self._prepare_response(False, 400, "", None, f"Missing - {', '.join(missing_bo_fields)}")

        existing_bo = request.env['res.partner'].sudo().search([
            ('bo_code', '=', data.get('bo_code'))
        ], limit=1)

        if not existing_bo:
            return self._prepare_response(False, 400, "BO user not exists", None, "BO user not exists")

        partner = existing_bo
        invoice_id = None
        pdf_content = None

        try:
            advertisement_product = request.env.ref('code_ox_list_2_win.advertisement_service_product_corn').sudo()
        except ValueError:
            return self._prepare_response(
                False, 404, "Advertisement product not found", None,
                "External ID 'advertisement_service_product_corn' not found"
            )

        if not advertisement_product:
            return self._prepare_response(
                False, 404, "Advertisement product not found", None,
                "Product with default_code 'ADVERTISEMENT' not found"
            )

        if payment_details:
            payment_method_name = payment_details.get('payment_method')
            if not payment_method_name:
                return self._prepare_response(False, 400, "Missing Payment Method", None, "Payment method is required.")

            payment_method_obj = request.env['axcept.payment.method'].sudo().search([
                ('name', '=', payment_method_name)
            ], limit=1)

            if not payment_method_obj:
                payment_method_obj = request.env['axcept.payment.method'].sudo().create({
                    'name': payment_method_name
                })
            journals = request.env['account.journal'].sudo().search([
                ('default_bank_payment_method', '=', True),
            ], limit=1)

            payment_journal = journals
            payment_method_line = payment_journal.inbound_payment_method_line_ids[0]

            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'invoice_date': payment_details.get('payment_date'),
                'invoice_date_due': payment_details.get('payment_date'),
                'invoice_line_ids': []
            }

            invoice_lines = [(0, 0, {
                'product_id': advertisement_product.id,
                'quantity': line.get('quantity', 1),
                'price_unit': line.get('price_unit', 0),
                'discount': line.get('discount', 0),
                'tax_ids': [(6, 0, line.get('tax_ids', []))],
            }) for line in payment_details.get('lines', [])]

            invoice_vals['invoice_line_ids'] = invoice_lines
            invoice = request.env['account.move'].sudo().create(invoice_vals)
            invoice.action_post()
            invoice_id = invoice.id

            amount = invoice.amount_total

            invoice_lines = invoice.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')
            payment_vals = {
                'amount': amount,
                'journal_id': payment_journal.id,
                'partner_id': partner.id,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'payment_method_line_id': payment_method_line.id,
                'payment_date': payment_details.get('payment_date'),
                'communication': invoice.name,
                'line_ids': [(6, 0, invoice_lines.ids)],
            }

            payment = request.env['account.payment.register'].sudo().create(payment_vals)
            payment.action_create_payments()

        referral_pdf_content = None
        if referring_be:
            ref_amount = referring_be.get('amount')

            if ref_amount:
                referring_partner = request.env['res.partner'].sudo().search([
                    ('be_code', '=', be_code)
                ], limit=1)

                if not referring_partner:
                    return self._prepare_response(False, 404, "Referring BE not found", None,
                                                f"No BE found with be_code: {be_code}")

                try:
                    ref_amount = float(ref_amount)
                except ValueError:
                    return self._prepare_response(False, 400, "Invalid referring_be amount", None,
                                                "Amount must be a valid number.")

                wallet = request.env['wallet.wallet'].sudo().search([
                    ('customer_id', '=', referring_partner.id)
                ], limit=1)

                if not wallet:
                    wallet = request.env['wallet.wallet'].sudo().create({
                        'customer_id': referring_partner.id
                    })

                request.env['wallet.received'].sudo().create({
                    'wallet_id': wallet.id,
                    'amount': ref_amount,
                })

                vendor_bill_vals = {
                    'move_type': 'in_invoice',
                    'partner_id': referring_partner.id,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': []
                }

                try:
                    referral_product = request.env.ref('code_ox_list_2_win.referral_commission_service_product_corn').sudo()
                except ValueError:
                    return self._prepare_response(False, 404, "Referral product not found", None,
                                                "External ID 'referral_commission_service_product_corn' not found")
                
                tax_ids = referring_be.get('tax_ids', [])
                tds_tax = request.env['account.tax'].sudo().search([('name', '=', '5% TDS 194H P')], limit=1)
                if tds_tax:
                    tax_ids.append(tds_tax.id)

                invoice_line = (0, 0, {
                    'product_id': referral_product.id,
                    'quantity': 1,
                    'price_unit': ref_amount,
                    'name': referral_product.name,
                    'tax_ids': [(6, 0, tax_ids)],
                })


                vendor_bill_vals['invoice_line_ids'] = [invoice_line]
                vendor_bill = request.env['account.move'].sudo().create(vendor_bill_vals)
                vendor_bill.action_post()
                amount = vendor_bill.amount_total

                invoice_lines = vendor_bill.line_ids.filtered(lambda l: l.account_id.account_type == 'liability_payable')

        base_url = self.get_base_url()
        return self._prepare_response(
            True,
            200,
            'Advertisement for BO created successfully.',
            {
                'bo_code': partner.bo_code,
                'customer_id': partner.id,
                'invoice_id': invoice_id,
                'pdf': f'{base_url}/invoice/{invoice_id}' if payment_details else None,
                'referral_receipt_pdf': f'{base_url}/invoice/{vendor_bill.id}' if referring_be else None
            },
            None
        )

    @validate_token
    @http.route('/api/be/updateprofile/<string:be_code>', type='http', auth='public', methods=['PATCH'], csrf=False)
    def update_be_profile(self, be_code, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
        except json.JSONDecodeError:
            return self._prepare_response(
                False, 400, "", None, "Invalid JSON"
            )

        partner = request.env['res.partner'].sudo().search([('be_code', '=', be_code)], limit=1)

        if not partner:
            return self._prepare_response(
                False, 400, "", None, f"No profile found with be_code {be_code}"
            )

        fields_to_update = [
            'email', 'first_name', 'last_name', 'gender', 'dob', 'street', 'post_office',
            'pincode', 'country_id', 'state_id', 'lsgd_name', 'city', 'aadhar_no', 'pancard_no',
            'father_name', 'mother_name', 'image_1920', 'education_qualification', 'phone', 'account_number',
            'bank_name', 'ifsc_code', 'bank_branch', 'account_type'
        ]

        vals = {}

        try:
            for field in fields_to_update:
                value = data.get(field)
                if value is not None:
                    if field == 'country_id':
                        country = request.env['res.country'].sudo().browse([value])
                        if not country.exists():
                            return self._prepare_response(
                                False, 400, "", None, f"Country {value} not found"
                            )
                        vals['country_id'] = country.id
                    elif field == 'state_id':
                        state = request.env['res.country.state'].sudo().browse([value])
                        if not state.exists():
                            return self._prepare_response(
                                False, 400, "", None, f"State {value} not found"
                            )
                        vals['state_id'] = state.id
                    elif field == 'pincode':
                        vals['zip'] = value
                    elif field == 'pancard_no':
                        vals['l10n_in_pan'] = value
                    elif field == 'first_name':
                        vals['name'] = value
                    elif field == 'house_no':
                        vals['street'] = value
                    elif field == 'account_number':
                        bank_account = request.env['res.partner.bank'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                        if bank_account:
                            bank_account.write({'acc_number': value})
                        else:
                            request.env['res.partner.bank'].sudo().create({
                                'partner_id': partner.id,
                                'acc_number': value
                            })
                    elif field == 'account_type':
                        bank_account = request.env['res.partner.bank'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                        if bank_account:
                            bank_account.write({'account_type': value})
                    elif field == 'bank_name' or field == 'ifsc_code' or field == 'bank_branch':
                        bank = request.env['res.bank'].sudo().search([('bic', '=', data.get('ifsc_code'))], limit=1)
                        if not bank:
                            bank = request.env['res.bank'].sudo().create({
                                'name': data.get('bank_name'),
                                'bic': data.get('ifsc_code'),
                                'branch': data.get('bank_branch')
                            })
                        
                        bank_account = request.env['res.partner.bank'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                        if bank_account:
                            bank_account.write({'bank_id': bank.id})
                        else:
                            request.env['res.partner.bank'].sudo().create({
                                'partner_id': partner.id,
                                'bank_id': bank.id,
                                'acc_number': data.get('account_number', '')
                            })
                    else:
                        vals[field] = value

            if vals:
                partner.write(vals)
                return self._prepare_response(
                    True, 200, "BE profile updated successfully", None, None
                )
            else:
                return self._prepare_response(
                    True, 200, "", None, "No fields provided to update"
                )
        except Exception as e:
            return self._prepare_response(
                False, 500, "", None, "Internal Server Error " + str(e)
            )

    @validate_token
    @http.route('/api/bo/advertisement/<string:bo_code>', type='http', auth='public', methods=['POST'], csrf=False)
    def create_bo_invoice(self, bo_code, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
        except json.JSONDecodeError:
            return self._prepare_response(False, 400, "", None, "Invalid JSON")

        partner = request.env['res.partner'].sudo().search([('bo_code', '=', bo_code)], limit=1)

        if not partner:
            return self._prepare_response(False, 400, "", None, f"No profile found with bo_code {bo_code}")

        try:
            try:
                advertisement_product = request.env.ref('code_ox_list_2_win.advertisement_service_product_corn').sudo()
            except ValueError:
                return self._prepare_response(
                    False, 404, "Advertisement product not found", None, "External ID 'advertisement_service_product_corn' not found"
                )

            if not advertisement_product:
                return self._prepare_response(
                    False, 404, "Advertisement product not found", None, "Product with default_code 'ADVERTISEMENT' not found"
                )

            advertisement_name = data.get('advertisement_name', advertisement_product.name)

            lines = data.get('lines', [])
            if not lines or not isinstance(lines, list):
                return self._prepare_response(False, 400, "", None, "Invoice lines not found")

            lines_ids = []
            for line in lines:
                price_unit = line.get('amount')
                tax_ids = line.get('tax_ids', [])
                quantity = line.get('quantity', 1)
                discount = line.get('discount', 0)

                if not price_unit:
                    return self._prepare_response(False, 400, "", None, "Each line must include amount")

                valid_tax_ids = []
                for tax_id in tax_ids:
                    tax = request.env['account.tax'].sudo().browse(tax_id)
                    if not tax.exists():
                        return self._prepare_response(False, 400, "", None, f"Invalid tax_id: {tax_id}")
                    valid_tax_ids.append(tax.id)

                lines_ids.append((0, 0, {
                    'name': advertisement_name,
                    'quantity': quantity,
                    'discount': discount,
                    'price_unit': price_unit,
                    'tax_ids': [(6, 0, valid_tax_ids)] if valid_tax_ids else [],
                    'product_id': advertisement_product.id,
                }))

            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'invoice_date': data.get('payment_date'),
                'invoice_date_due': data.get('payment_date'),
                'invoice_line_ids': lines_ids
            }

            invoice = request.env['account.move'].sudo().create(invoice_vals)
            invoice.action_post()

            amount_total = invoice.amount_total

            payment_method_name = data.get('payment_method')

            if payment_method_name:
                payment_method_obj = request.env['axcept.payment.method'].sudo().search([('name', '=', payment_method_name)], limit=1)

                if not payment_method_obj:
                    payment_method_obj = request.env['axcept.payment.method'].sudo().create({'name': payment_method_name})

                journals = request.env['account.journal'].sudo().search([
                    ('default_bank_payment_method', '=', True),
                ], limit=1)
                
                payment_method_line = journals.inbound_payment_method_line_ids[0]

                invoice_lines = invoice.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')
                payment_vals = {
                    'amount': amount_total,
                    'journal_id': journals.id,
                    'partner_id': partner.id,
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'payment_method_line_id': payment_method_line.id,
                    'payment_date': data.get('payment_date'),
                    'communication': invoice.name,
                    'line_ids': [(6, 0, invoice_lines.ids)],
                }

                payment = request.env['account.payment.register'].sudo().create(payment_vals)
                payment.action_create_payments()
            base_url = self.get_base_url()
            return self._prepare_response(
                statusOk=True,
                statusCode=200,
                message='Advertisement Created Successfully.',
                payload={
                    'bo_code': bo_code,
                    'invoice_id': invoice.id,
                    'invoice_number': invoice.name,
                    'pdf': f'{base_url}/invoice/{invoice.id}' if invoice else None
                },
                error=None
            )

        except Exception as e:
            return self._prepare_response(False, 500, "", None, "Internal Server Error: " + str(e))

    @validate_token
    @http.route('/api/bo/create', type='http', auth='public', methods=['POST'], csrf=False)
    def register_bo(self):
        data = json.loads(request.httprequest.data)

        bo_details = data.get('bo_details')
        payment_details = data.get('payment_details')
        referring_be = data.get('referring_be')

        required_bo_fields = [
            'email', 'first_name', 'gender',
            'country_id', 'state_id', 'bo_code'
        ]

        if not data:
            return self._prepare_response(False, 400, "", None, "Missing data.")
        
        existing_bo = request.env['res.partner'].sudo().search([
            ('bo_code', '=', bo_details.get('bo_code'))
        ], limit=1)

        if existing_bo:
            return self._prepare_response(
                False,
                400, 
                f"BO already exists with BO Code {bo_details.get('bo_code')}",
                None,
                f"A Business Office with BO Code {bo_details.get('bo_code')} already exists. Registration Cancelled."
            )

        missing_fields = [field for field in required_bo_fields if not bo_details.get(field)]
        if missing_fields:
            return self._prepare_response(False, 400, "", None, f"Missing - {', '.join(missing_fields)}")
        
        district_id = False
        if bo_details.get('district_id'):
            district_rec = request.env['res.district'].sudo().browse(int(bo_details.get('district_id')))
            if not district_rec.exists():
                return self._prepare_response(
                    False,
                    400,
                    "Invalid District",
                    None,
                    f"District ID '{bo_details.get('district_id')}' not found."
                )
            district_id = district_rec.id

        country_rec = request.env['res.country'].sudo().browse(int(bo_details.get('country_id')))
        if not country_rec.exists():
            return self._prepare_response(
                False,
                400,
                "Invalid Country",
                None,
                f"Country ID '{bo_details.get('country_id')}' not found or invalid."
            )
        country_id = country_rec.id

        state_rec = request.env['res.country.state'].sudo().browse(int(bo_details.get('state_id')))
        if not state_rec.exists():
            return self._prepare_response(
                False,
                400,
                "Invalid State",
                None,
                f"State ID '{bo_details.get('state_id')}' not found or invalid."
            )
        state_id = state_rec.id

        if payment_details:
            if 'payment_date' not in payment_details:
                return self._prepare_response(
                    False, 400, "Missing required payment fields", None,
                    "Missing field in payment_details: payment_date"
                )

            payment_method_str = payment_details.get('payment_method')
            axcept_method = request.env['axcept.payment.method'].sudo().search([
                ('name', '=', payment_method_str)
            ], limit=1)

            if not axcept_method:
                axcept_method = request.env['axcept.payment.method'].sudo().create({
                    'name': payment_method_str
                })
            journals = request.env['account.journal'].sudo().search([
                ('default_bank_payment_method', '=', True),
            ], limit=1)

            registration_product = request.env.ref('listing_service_product_corn', raise_if_not_found=False)
            if not registration_product:
                registration_product = request.env['product.product'].sudo().search([
                    ('default_code', '=', 'LISTING'),
                    ('type', '=', 'service')
                ], limit=1)

            if not registration_product:
                return Response(json.dumps({
                    'status': 'error',
                    'message': "Listing product not found."
                }), content_type='application/json', status=400)

        if referring_be:
            ref_be_code = referring_be.get('be_code')
            ref_amount = referring_be.get('amount')

            if ref_be_code and ref_amount:
                referring_partner = request.env['res.partner'].sudo().search([
                    ('be_code', '=', ref_be_code)
                ], limit=1)

                if not referring_partner:
                    return self._prepare_response(
                        False, 404, "Referring BE not found", None,
                        f"No BE found with be_code: {ref_be_code}"
                    )

                try:
                    float(ref_amount)
                except ValueError:
                    return self._prepare_response(
                        False, 400, "Invalid referring_be amount", None,
                        "Amount must be a valid number."
                    )

        partner_vals = {
            'bo_code': bo_details.get('bo_code'),
            'email': bo_details.get('email'),
            'name': bo_details.get('first_name'),
            'last_name': bo_details.get('last_name'),
            'phone': bo_details.get('phone'),
            'gender': bo_details.get('gender', '').lower(),
            'street': bo_details.get('house_no'),
            'street2': bo_details.get('place'),
            'post_office': bo_details.get('post_office'),
            'lsgd_name': bo_details.get('lsgd_name'),
            'zip': bo_details.get('pincode'),
            'country_id': country_id,
            'state_id': state_id,
            'district': district_id,
            'city': bo_details.get('city'),
            'aadhar_no': bo_details.get('aadhar_no'),
            'l10n_in_pan': bo_details.get('pancard_no'),
            'image_1920': bo_details.get('image_1920'),
            'vat': bo_details.get('gst_number'),
            'is_company': False,
            'company_type': 'company',
            'customer_rank': 1,
            'is_bo': True
        }

        partner = request.env['res.partner'].sudo().create(partner_vals)
        partner_created = True

        invoice_id = None
        pdf_content = None
        if payment_details:
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'invoice_date': payment_details.get('payment_date'),
                'invoice_date_due': payment_details.get('payment_date'),
                'invoice_line_ids': []
            }

            invoice_lines = []
            for line in payment_details.get('lines', []):
                invoice_lines.append((0, 0, {
                    'product_id': registration_product.id,
                    'quantity': line.get('quantity', 1),
                    'price_unit': line.get('price_unit', 0),
                    'discount': line.get('discount', 0),
                    'tax_ids': [(6, 0, line.get('tax_ids', []))],
                }))

            invoice_vals['invoice_line_ids'] = invoice_lines

            invoice = request.env['account.move'].sudo().create(invoice_vals)
            invoice.action_post()
            invoice_id = invoice.id

            journals = request.env['account.journal'].sudo().search([
                ('default_bank_payment_method', '=', True),
            ], limit=1)
            payment_journal = journals[0]
            payment_method_line = payment_journal.inbound_payment_method_line_ids[0]

            payment_vals = {
                'amount': invoice.amount_total,
                'journal_id': payment_journal.id,
                'partner_id': partner.id,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'payment_method_line_id': payment_method_line.id,
                'payment_date': payment_details.get('payment_date'),
                'communication': invoice.name,
                'line_ids': [(6, 0, invoice.line_ids.filtered(
                    lambda l: l.account_id.account_type == 'asset_receivable').ids)],
            }

            payment = request.env['account.payment.register'].sudo().create(payment_vals)
            payment.action_create_payments()

            report_action = request.env.ref('account.account_invoices').sudo()
            pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                report_action.report_name, [invoice.id])

        if referring_be:
            wallet = request.env['wallet.wallet'].sudo().search([
                ('customer_id', '=', referring_partner.id)
            ], limit=1)

            if not wallet:
                wallet = request.env['wallet.wallet'].sudo().create({
                    'customer_id': referring_partner.id
                })

            request.env['wallet.received'].sudo().create({
                'wallet_id': wallet.id,
                'amount': float(referring_be.get('amount')),
            })
            vendor_bill_vals = {
                    'move_type': 'in_invoice',
                    'partner_id': referring_partner.id,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': []
                }

            try:
                referral_product = request.env.ref('code_ox_list_2_win.referral_commission_service_product_corn').sudo()
            except ValueError:
                return self._prepare_response(
                    False, 404, "Referral product not found", None,
                    "External ID 'referral_commission_service_product_corn' not found"
                )
            
            tax_ids = referring_be.get('tax_ids', [])
            tds_tax = request.env['account.tax'].sudo().search([('name', '=', '5% TDS 194H P')], limit=1)
            if tds_tax:
                tax_ids.append(tds_tax.id)

            invoice_line = (0, 0, {
                'product_id': referral_product.id,
                'quantity': 1,
                'price_unit': ref_amount,
                'name': 'Referral Amount',
                'tax_ids': [(6, 0, tax_ids)],
            })

            vendor_bill_vals['invoice_line_ids'] = [invoice_line]
            vendor_bill = request.env['account.move'].sudo().create(vendor_bill_vals)
            vendor_bill.action_post()
            amount = vendor_bill.amount_total
            invoice_lines = vendor_bill.line_ids.filtered(lambda l: l.account_id.account_type == 'liability_payable')

        base_url = self.get_base_url()
        return self._prepare_response(
            True,
            201,
            'BO created successfully.',
            {
                'bo_code': bo_details.get('bo_code'),
                'customer_id': partner.id,
                'invoice_id': invoice_id,
                'pdf': f'{base_url}/invoice/{invoice_id}' if payment_details else None,
                'referral_receipt_pdf': f'{base_url}/invoice/{vendor_bill.id}' if referring_be else None
            },
            None
        )
        
    @http.route('/api/countries', type='http', auth='public', methods=['GET'], csrf=False)
    def get_country(self):
        countries = request.env['res.country'].sudo().search([('show_in_app', '=', True)], order='name')
        country_list = [{'id': c.id, 'name': c.name} for c in countries]

        response = {
            'statusOk': True,
            'statusCode': 200,
            'message': 'Country data fetched successfully',
            'payload': country_list,
            'error': None
        }

        return request.make_response(
            json.dumps(response),
            headers=[('Content-Type', 'application/json')],
            status=200
        )

    @http.route('/api/states', type='http', auth='public', methods=['GET'], csrf=False)
    def get_states(self):
        states = request.env['res.country.state'].sudo().search([('show_in_app', '=', True)], order='name')
        state_list = [{'id': s.id, 
                       'name': s.name,
                       'country_id': s.country_id.id,
                       'country_name': s.country_id.name
                       } for s in states]

        response = {
            'statusOk': True,
            'statusCode': 200,
            'message': 'State data fetched successfully',
            'payload': state_list,
            'error': None
        }

        return request.make_response(
            json.dumps(response),
            headers=[('Content-Type', 'application/json')],
            status=200
        )
    
    @http.route('/api/districts', type='http', auth='public', methods=['GET'], csrf=False)
    def get_districts(self):
        districts = request.env['res.district'].sudo().search([], order='name')
        district_list = [{'id': d.id, 'name': d.name} for d in districts]

        response = {
            'statusOk': True,
            'statusCode': 200,
            'message': 'District data fetched successfully',
            'payload': district_list,
            'error': None
        }

        return request.make_response(
            json.dumps(response),
            headers=[('Content-Type', 'application/json')],
            status=200
        )
    
    @validate_token
    @http.route('/api/bo/renew/<bo_code>', type='http', auth='public', methods=['POST'], csrf=False)
    def renew_bo(self, bo_code):
        data = json.loads(request.httprequest.data)
        payment_details = data.get('payment_details')
        referring_be = data.get('referring_be')
        if not data:
            return self._prepare_response(False, 400, "Missing payment_details", None, "Payment details required")

        partner = request.env['res.partner'].sudo().search([('bo_code', '=', bo_code)], limit=1)
        if not partner:
            return self._prepare_response(False, 404, "BO not found", None, f"No BO found with code {bo_code}")
        
        if referring_be:
            ref_be_code = referring_be.get('be_code')
            ref_amount = referring_be.get('amount')

            if ref_be_code and ref_amount:
                referring_partner = request.env['res.partner'].sudo().search([
                    ('be_code', '=', ref_be_code)
                ], limit=1)

                if not referring_partner:
                    return self._prepare_response(
                        False, 404, "Referring BE not found", None,
                        f"No BE found with be_code: {ref_be_code}"
                    )

                try:
                    float(ref_amount)
                except ValueError:
                    return self._prepare_response(
                        False, 400, "Invalid referring_be amount", None,
                        "Amount must be a valid number."
                    )
        
        if payment_details:
            if 'payment_date' not in payment_details:
                return self._prepare_response(False, 400, "Missing payment_date", None, "Field 'payment_date' is required")
        
            payment_method_str = payment_details.get('payment_method')
            axcept_method = request.env['axcept.payment.method'].sudo().search([
                ('name', '=', payment_method_str)
            ], limit=1)

            if not axcept_method:
                axcept_method = request.env['axcept.payment.method'].sudo().create({
                    'name': payment_method_str
                })
            
            journals = request.env['account.journal'].sudo().search([
                ('default_bank_payment_method', '=', True),
            ], limit=1)

            try:
                renewal_product = request.env.ref('code_ox_list_2_win.renewal_service_product_corn').sudo()
            except ValueError:
                return self._prepare_response(False, 404, "Renewal product not found", None, "External ID 'renewal_service_product_corn' not found")

            if not renewal_product:
                return self._prepare_response(False, 404, "Renewal product not found", None, "Product with default_code 'RENEWAL' not found")

            invoice_line_ids = []
            for line in payment_details.get('lines', []):
                tax_ids_list = line.get('tax_ids', [])
                tax_ids = [(6, 0, tax_ids_list)] if tax_ids_list else []

                invoice_line_ids.append((0, 0, {
                    'product_id': renewal_product.id,
                    'quantity': line.get('quantity', 1),
                    'price_unit': line.get('price_unit', 0.0),
                    'tax_ids': tax_ids,
                    'name': renewal_product.name or 'Renewal Invoice',
                }))

            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'invoice_date': payment_details.get('payment_date'),
                'invoice_date_due': payment_details.get('payment_date'),
                'invoice_line_ids': invoice_line_ids
            }

            invoice = request.env['account.move'].sudo().create(invoice_vals)
            invoice.action_post()

            amount = invoice.amount_total
            payment_journal = journals[0]
            payment_method_line = payment_journal.inbound_payment_method_line_ids[0]
            invoice_lines = invoice.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')

            payment_vals = {
                'amount': amount,
                'journal_id': payment_journal.id,
                'partner_id': partner.id,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'payment_method_line_id': payment_method_line.id,
                'payment_date': payment_details.get('payment_date'),
                'communication': invoice.name,
                'line_ids': [(6, 0, invoice_lines.ids)],
            }

            payment = request.env['account.payment.register'].sudo().create(payment_vals)
            payment.action_create_payments()
        
        if referring_be:
            wallet = request.env['wallet.wallet'].sudo().search([
                ('customer_id', '=', referring_partner.id)
            ], limit=1)

            if not wallet:
                wallet = request.env['wallet.wallet'].sudo().create({
                    'customer_id': referring_partner.id
                })

            request.env['wallet.received'].sudo().create({
                'wallet_id': wallet.id,
                'amount': float(referring_be.get('amount')),
            })
            vendor_bill_vals = {
                    'move_type': 'in_invoice',
                    'partner_id': referring_partner.id,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': []
                }
            
            try:
                referral_product = request.env.ref('code_ox_list_2_win.referral_commission_service_product_corn').sudo()
            except ValueError:
                return self._prepare_response(False, 404, "Referral product not found", None,
                                              "External ID 'referral_commission_service_product_corn' not found")
            
            tax_ids = referring_be.get('tax_ids', [])
            tds_tax = request.env['account.tax'].sudo().search([('name', '=', '5% TDS 194H P')], limit=1)
            if tds_tax:
                tax_ids.append(tds_tax.id)
            invoice_line = (0, 0, {
                'product_id': referral_product.id,
                'quantity': 1,
                'price_unit': float(referring_be.get('amount')),
                'name': 'Referral Amount',
                'tax_ids': [(6, 0, tax_ids)]
            })

            vendor_bill_vals['invoice_line_ids'] = [invoice_line]
            vendor_bill = request.env['account.move'].sudo().create(vendor_bill_vals)
            vendor_bill.action_post()

        base_url = self.get_base_url()
        return self._prepare_response(
            True, 200, "BO membership renewed and invoice paid",
            {
                'bo_code': bo_code,
                'customer_id': partner.id,
                'invoice_id': invoice.id,
                'pdf': f'{base_url}/invoice/{invoice.id}' if invoice else None,
                'referral_receipt_pdf': f'{base_url}/invoice/{vendor_bill.id}' if referring_be else None
            },
            None
        )

    @http.route('/api/taxes', type='http', auth='public', methods=['GET'], csrf=False)
    def get_taxes(self):
        taxes = request.env['account.tax'].sudo().search([])
        result = [
            {
                'id': tax.id,
                'name': tax.name,
                'type': tax.type_tax_use,
            }
            for tax in taxes
        ]
        return self._prepare_response(
            True, 200, "Tax data fetched successfully",
            {
                'taxes': result
            },
            None
        )
    
    @validate_token
    @http.route('/api/be/redeem_commission/<be_code>', type='http', auth='public', methods=['POST'], csrf=False)
    def redeem_referral_commission(self, be_code):
        data = json.loads(request.httprequest.data)
        if not data:
            return self._prepare_response(False, 400, "Missing details", None, "Missing details")

        partner = request.env['res.partner'].sudo().search([('be_code', '=', be_code)], limit=1)
        if not partner:
            return self._prepare_response(False, 404, "BE not found", None, f"No BO found with code {be_code}")
        
        if not data.get('amount'):
            return self._prepare_response(False, 404, "Amount is missing", None, "Amount is missing")
        
        if not data.get('payment_method'):
            return self._prepare_response(False, 404, "Payment method is missing", None, "Payment method is missing")
        
        payment_method_str = data.get('payment_method')
        axcept_method = request.env['axcept.payment.method'].sudo().search([
            ('name', '=', payment_method_str)
        ], limit=1)

        if not axcept_method:
            axcept_method = request.env['axcept.payment.method'].sudo().create({
                'name': payment_method_str
            })

        journals = request.env['account.journal'].sudo().search([
                ('default_bank_payment_method', '=', True),
            ], limit=1)

        
        wallet = request.env['wallet.wallet'].sudo().search([
                ('customer_id', '=', partner.id)
            ], limit=1)
        if not wallet:
            return self._prepare_response(False, 404, "Wallet not found", None, "Wallet not found")
        if wallet.balance_amount < data.get('amount'):
            return self._prepare_response(False, 404, "Commission amount exceeded", None, "Commission amount exceeded")

        request.env['wallet.spend'].sudo().create({
                'wallet_id': wallet.id,
                'amount': float(data.get('amount')),
            })
        
        vendor_bills = request.env['account.move'].sudo().search([
            ('partner_id', '=', partner.id), ('move_type', '=', 'in_invoice'), ('payment_state', 'in', ['not_paid', 'partial'])])
        payment_journal = journals[0]
        amount = data.get('amount')
        for vendor_bill in vendor_bills:
            if amount > 0:
                if amount > vendor_bill.amount_residual:
                    payment_amount = vendor_bill.amount_residual
                else:
                    payment_amount = amount
                amount -= vendor_bill.amount_residual
                invoice_lines = vendor_bill.line_ids.filtered(lambda l: l.account_id.account_type == 'liability_payable')
                payment_vals = {
                    'amount': payment_amount,
                    'journal_id': payment_journal.id,
                    'partner_id': partner.id,
                    'payment_type': 'outbound',
                    'partner_type': 'supplier',
                    'payment_method_line_id': payment_journal.outbound_payment_method_line_ids[0].id,
                    'payment_date': fields.Date.today(),
                    'communication': vendor_bill.name,
                    'line_ids': [(6, 0, invoice_lines.ids)],
                }

                payment = request.env['account.payment.register'].sudo().create(payment_vals)
                payment.action_create_payments()
                for vendor_payment in vendor_bill.matched_payment_ids:
                    vendor_payment.action_validate()

        if data.get('list2win_amount'):
            list2win_amount = data.get('list2win_amount')
            if not isinstance(list2win_amount, (int, float)):
                return self._prepare_response(False, 400, "Invalid amount", None, "Amount must be a valid number")
            
            if list2win_amount <= 0:
                return self._prepare_response(False, 400, "Invalid amount", None, "Amount must be greater than zero")

            if list2win_amount > 0:
                if not data.get('list2win_tax_ids'):
                    return self._prepare_response(False, 400, "Missing tax_ids", None, "Tax IDs are required for List2Win commission payment")
                tax_ids = data.get('list2win_tax_ids', [])
                vendor_bill = request.env['account.move'].sudo().create({
                    'move_type': 'in_invoice',
                    'partner_id': partner.id,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': [
                        (0, 0, {
                            'quantity': 1,
                            'price_unit': list2win_amount,
                            'name': f'List2Win Commission for {be_code}',
                            'tax_ids': [(6, 0, tax_ids)],
                        })
                    ]
                })
                vendor_bill.action_post()
                invoice_lines = vendor_bill.line_ids.filtered(lambda l: l.account_id.account_type == 'liability_payable')
                payment_vals = {
                    'amount': vendor_bill.amount_total,
                    'journal_id': payment_journal.id,
                    'partner_id': partner.id,
                    'payment_type': 'outbound',
                    'partner_type': 'supplier',
                    'payment_method_line_id': payment_journal.outbound_payment_method_line_ids[0].id,
                    'payment_date': fields.Date.today(),
                    'communication': vendor_bill.name,
                    'line_ids': [(6, 0, invoice_lines.ids)],
                }

                payment = request.env['account.payment.register'].sudo().create(payment_vals)
                payment.action_create_payments()

        if data.get('cash_free_amount'):
            cash_free_amount = data.get('cash_free_amount')
            if not isinstance(cash_free_amount, (int, float)):
                return self._prepare_response(False, 400, "Invalid amount", None, "Amount must be a valid number")
            
            if cash_free_amount <= 0:
                return self._prepare_response(False, 400, "Invalid amount", None, "Amount must be greater than zero")

            if cash_free_amount > 0:
                if not data.get('cash_free_tax_ids'):
                    return self._prepare_response(False, 400, "Missing tax_ids", None, "Tax IDs are required for List2Win commission payment")
                tax_ids = data.get('cash_free_tax_ids', [])
                customer_invoice = request.env['account.move'].sudo().create({
                    'move_type': 'out_invoice',
                    'partner_id': partner.id,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': [
                        (0, 0, {
                            'quantity': 1,
                            'price_unit': cash_free_amount,
                            'name': f'Cash Free Commission paid by {be_code}',
                            'tax_ids': [(6, 0, tax_ids)],
                        })
                    ]
                })
                customer_invoice.action_post()
                invoice_lines = customer_invoice.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')
                payment_vals = {
                    'amount': customer_invoice.amount_total,
                    'journal_id': payment_journal.id,
                    'partner_id': partner.id,
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'payment_method_line_id': payment_journal.outbound_payment_method_line_ids[0].id,
                    'payment_date': fields.Date.today(),
                    'communication': vendor_bill.name,
                    'line_ids': [(6, 0, invoice_lines.ids)],
                }

                payment = request.env['account.payment.register'].sudo().create(payment_vals)
                payment.action_create_payments()
                
        return self._prepare_response(
            True, 200, "Referral Commission Redeemed",
            {
                'be_code': be_code,
                'customer_id': partner.id,
            },
            None
        )
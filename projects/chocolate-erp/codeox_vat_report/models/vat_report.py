from odoo import models,api,fields
from datetime import datetime,date
from calendar import monthrange

class AccountVatReport(models.AbstractModel):
    _name = "report.codeox_vat_report.html_report"
    _description = "VAT Report Template"

    
    @api.model
    def _get_report_values(self, docids, data=None):
        tax_line = []
        start_date = datetime.strptime(data['start_date'], "%Y-%m-%d").date()
        end_date = datetime.strptime(data['end_date'], "%Y-%m-%d").date()
        company = self.env.company
        company_id = int(data['company']) if data['company'] else False
        if company_id:
            company = self.env['res.company'].sudo().browse(company_id)
        domain = {}

        # tax_tag_ids for SALES BASE category
        # Define all tax tag names up front
        tax_tag_map = {
            'standard_15': ['+1. Standard Rates 15% (Base)', '-1. Standard Rates 15% (Base)'],
            'special_local': ['+2. Special Sales to Locals (Base)', '-2. Special Sales to Locals (Base)'],
            'local_zero': ['+3. Local Sales Subject to 0% (Base)', '-3. Local Sales Subject to 0% (Base)'],
            'export': ['+4. Export Sales (Base)', '-4. Export Sales (Base)'],
            'exempt': ['+5. Exempt Sales (Base)', '-5. Exempt Sales (Base)']
        }

        # Get all tax tags in one query
        all_tags = self.env['account.account.tag'].search([('name', 'in', 
            [tag for tags in tax_tag_map.values() for tag in tags])])
        
        # Create tag id mappings
        tag_ids = {
            key: all_tags.filtered(lambda t: t.name in tags).ids
            for key, tags in tax_tag_map.items()
        }

        # Combine all tag ids
        vat_tag_ids_for_sales_base = sum((tag_ids[key] for key in tag_ids), [])

        # Base query parameters
        base_domain = [
            ('parent_state', 'in', ['posted']),
            ('company_id', '=', company.id), 
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ]

        # Function to calculate balance for specific tags
        def get_sales_balance(tag_ids):
            domain = base_domain + [('tax_tag_ids', 'in', tag_ids)]
            return sum(self.env['account.move.line'].search(domain).mapped('balance'))

        # Calculate all balances
        sales_data = {
            'sale_untaxed': get_sales_balance(vat_tag_ids_for_sales_base),
            'standard_rated_base': get_sales_balance(tag_ids['standard_15']),
            'special_sales_to_local_base': get_sales_balance(tag_ids['special_local']),
            'local_sales_subject_to_zero_base': get_sales_balance(tag_ids['local_zero']),
            'export_sales_base': get_sales_balance(tag_ids['export']),
            'exempt_sales_base': get_sales_balance(tag_ids['exempt']),
            'net_sales_base': get_sales_balance(vat_tag_ids_for_sales_base)
        }

        # Add results to tax_line
        for key, amount in sales_data.items():
            tax_line.append({
            'id': key,
            'amount': f"{abs(amount):.2f}"
            })

        # Store domain for further use
        domain['sales_untaxed_domain'] = base_domain + [
            ('tax_tag_ids', 'in', vat_tag_ids_for_sales_base)
        ]

        # Define tax tag mappings for sales tax
        tax_tag_map_tax = {
            'standard_15': ['+1. Standard Rates 15% (Tax)', '-1. Standard Rates 15% (Tax)'],
            'special_local': ['+2. Special Sales to Locals (Tax)', '-2. Special Sales to Locals (Tax)'],
            'local_zero': ['+3. Local Sales Subject to 0% (Tax)', '-3. Local Sales Subject to 0% (Tax)'],
            'export': ['+4. Export Sales (Tax)', '-4. Export Sales (Tax)'],
            'exempt': ['+5. Exempt Sales (Tax)', '-5. Exempt Sales (Tax)']
        }

        # Get all tax tags in one query
        all_tags_tax = self.env['account.account.tag'].search([('name', 'in', 
            [tag for tags in tax_tag_map_tax.values() for tag in tags])])
        
        # Create tag id mappings
        tag_ids_tax = {
            key: all_tags_tax.filtered(lambda t: t.name in tags).ids
            for key, tags in tax_tag_map_tax.items()
        }

        # Combine all tag ids for sales tax
        vat_tag_ids_for_sales_tax = sum((tag_ids_tax[key] for key in tag_ids_tax), [])

        # Function to calculate tax balance for specific tags
        def get_sales_tax_balance(tag_ids):
            domain = base_domain + [('tax_tag_ids', 'in', tag_ids)]
            return sum(self.env['account.move.line'].search(domain).mapped('balance'))

        # Calculate all tax balances
        sales_tax_data = {
            'sale_tax': get_sales_tax_balance(vat_tag_ids_for_sales_tax),
            'standard_rated_tax': get_sales_tax_balance(tag_ids_tax['standard_15']),
            'special_sales_to_locals_tax': get_sales_tax_balance(tag_ids_tax['special_local']),
            'local_sales_subject_to_zero_percent_tax': get_sales_tax_balance(tag_ids_tax['local_zero']),
            'export_sales_tax': get_sales_tax_balance(tag_ids_tax['export']),
            'exempt_sales_tax': get_sales_tax_balance(tag_ids_tax['exempt']),
            'net_sales_tax': get_sales_tax_balance(vat_tag_ids_for_sales_tax)
        }

        # Add results to tax_line
        for key, amount in sales_tax_data.items():
            tax_line.append({
            'id': key,
            'amount': f"{abs(amount):.2f}"
            })

        # Store sale tax total for later use
        sale_tax_total = sales_tax_data['sale_tax']

        # Store domain for further use
        domain['sales_taxed_domain'] = base_domain + [
            ('tax_tag_ids', 'in', vat_tag_ids_for_sales_tax)
        ]
        
        # Purchase Section

        # tax_tag_ids for PURCHASE BASE category
        purchase_tax_tag_map = {
            'standard_15': ['+7. Standard rated 15% Purchases (Base)', '-7. Standard rated 15% Purchases (Base)'],
            'taxable_import': ['+8. Taxable Imports 15% Paid to Customs (Base)', '-8. Taxable Imports 15% Paid to Customs (Base)'],
            'reverse_charge': ['+9. Imports subject to reverse charge mechanism (Base)', '-9. Imports subject to reverse charge mechanism (Base)'],
            'zero_rated': ['+10. Zero Rated Purchases (Base)', '-10. Zero Rated Purchases (Base)'],
            'exempt': ['+11. Exempt Purchases (Base)', '-11. Exempt Purchases (Base)']
        }

        # Get all tax tags in one query
        all_purchase_tags = self.env['account.account.tag'].search([('name', 'in', 
            [tag for tags in purchase_tax_tag_map.values() for tag in tags])])
        
        # Create tag id mappings
        purchase_tag_ids = {
            key: all_purchase_tags.filtered(lambda t: t.name in tags).ids
            for key, tags in purchase_tax_tag_map.items()
        }

        # Combine all tag ids
        vat_tag_ids_for_purchases_base = sum((purchase_tag_ids[key] for key in purchase_tag_ids), [])

        # Function to calculate balance for specific tags
        def get_purchase_balance(tag_ids):
            domain = base_domain + [('tax_tag_ids', 'in', tag_ids)]
            return sum(self.env['account.move.line'].search(domain).mapped('balance'))

        # Calculate all balances
        purchase_data = {
            'purchase_untaxed': get_purchase_balance(vat_tag_ids_for_purchases_base),
            'standard_rated_purchases_base': get_purchase_balance(purchase_tag_ids['standard_15']),
            'taxable_imprts_paid_customs_base': get_purchase_balance(purchase_tag_ids['taxable_import']),
            'imports_subject_to_reverse_charge_mechanism_base': get_purchase_balance(purchase_tag_ids['reverse_charge']),
            'zero_rated_purchases_base': get_purchase_balance(purchase_tag_ids['zero_rated']),
            'exempt_purchases_base': get_purchase_balance(purchase_tag_ids['exempt']),
            'net_purchases_base': get_purchase_balance(vat_tag_ids_for_purchases_base)
        }

        # Add results to tax_line
        for key, amount in purchase_data.items():
            tax_line.append({
            'id': key,
            'amount': f"{abs(amount):.2f}"
            })

        # Store domain for further use
        domain['purchases_base_domain'] = base_domain + [
            ('tax_tag_ids', 'in', vat_tag_ids_for_purchases_base)
        ]

        # Define tax tag mappings for purchase tax
        purchase_tax_tag_map_tax = {
            'standard_15': ['+7. Standard rated 15% Purchases (Tax)', '-7. Standard rated 15% Purchases (Tax)'],
            'taxable_import': ['+8. Taxable Imports 15% Paid to Customs (Tax)', '-8. Taxable Imports 15% Paid to Customs (Tax)'],
            'reverse_charge': ['+9. Imports subject to reverse charge mechanism (Tax)', '-9. Imports subject to reverse charge mechanism (Tax)'],
            'zero_rated': ['+10. Zero Rated Purchases (Tax)', '-10. Zero Rated Purchases (Tax)'],
            'exempt': ['+11. Exempt Purchases (Tax)', '-11. Exempt Purchases (Tax)']
        }

        # Get all tax tags in one query
        all_purchase_tax_tags = self.env['account.account.tag'].search([('name', 'in', 
            [tag for tags in purchase_tax_tag_map_tax.values() for tag in tags])])
        
        # Create tag id mappings
        purchase_tax_ids = {
            key: all_purchase_tax_tags.filtered(lambda t: t.name in tags).ids
            for key, tags in purchase_tax_tag_map_tax.items()
        }

        # Combine all tag ids for purchase tax
        vat_tag_ids_for_purchases_tax = sum((purchase_tax_ids[key] for key in purchase_tax_ids), [])

        # Function to calculate tax balance for specific tags
        def get_purchase_tax_balance(tag_ids):
            domain = base_domain + [('tax_tag_ids', 'in', tag_ids)]
            return sum(self.env['account.move.line'].search(domain).mapped('balance'))

        # Calculate all tax balances
        purchase_tax_data = {
            'purchase_tax': get_purchase_tax_balance(vat_tag_ids_for_purchases_tax),
            'standard_rated_purchases_tax': get_purchase_tax_balance(purchase_tax_ids['standard_15']),
            'taxable_imprts_paid_customs_tax': get_purchase_tax_balance(purchase_tax_ids['taxable_import']),
            'imports_subject_to_reverse_charge_mechanism_tax': get_purchase_tax_balance(purchase_tax_ids['reverse_charge']),
            'zero_rated_purchases_tax': get_purchase_tax_balance(purchase_tax_ids['zero_rated']),
            'exempt_purchases_tax': get_purchase_tax_balance(purchase_tax_ids['exempt']),
            'net_purchases_tax': get_purchase_tax_balance(vat_tag_ids_for_purchases_tax)
        }

        # Store purchase tax total
        purchase_tax_total = purchase_tax_data['purchase_tax']

        # Add results to tax_line
        for key, amount in purchase_tax_data.items():
            tax_line.append({
            'id': key,
            'amount': f"{abs(amount):.2f}"
            })

        # Store domain for further use
        domain['purchases_tax_domain'] = base_domain + [
            ('tax_tag_ids', 'in', vat_tag_ids_for_purchases_tax)
        ]

        # Calculate net VAT values
        net_tax = abs(sale_tax_total) - abs(purchase_tax_total)

        # Append final tax summary values
        final_tax_data = [
            {'id': 'net_vat_due', 'amount': ''},
            {'id': 'total_value_of_due_tax_for_the_period', 'amount': f"{abs(sale_tax_total):.2f}"},
            {'id': 'total_value_of_recoverable_tax_for_the_period', 'amount': f"{abs(purchase_tax_total):.2f}"},
            {'id': 'net_vat_due_for_the_period', 'amount': f"{net_tax:.2f}"}
        ]
        
        tax_line.extend(final_tax_data)

        return {
            'vat_line': tax_line,
            'domain': domain
        }

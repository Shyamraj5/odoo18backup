from odoo import models,fields,api


class PackageReport(models.AbstractModel):
    _name = "report.diet.package_report_template"
    _description = "Package Report"

    def _get_report_values(self, docids, data=None):
        plan_ids = self.env['subscription.package.plan'].search([])
        report_data = []
        for plan in plan_ids:
            total_customers = 0
            total_amount = 0
            subscriptions = self.env['diet.subscription.order'].search([
                ('plan_id', '=', plan.id),
                ('state', 'in', ["paid","in_progress"])
            ])
            total_customers = len(subscriptions.mapped('partner_id'))
            total_amount = sum(subscriptions.mapped('grand_total'))
            report_data.append({
                'plan': plan.name,
                'subscribers': total_customers,
                'amount': total_amount
            })
        return {
            'doc_ids': docids,
            'doc_model': 'subscription.package.plan',
            'docs': report_data
        }
from odoo import api, fields, models
from datetime import timedelta

class DocumentTracking(models.Model):
    _name = 'document.tracking'
    _description = 'Document Tracking'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    document_type_id = fields.Many2one('document.type', string='Document Type', required=True)
    document_number = fields.Char(string="Document Number", required=True)
    document_attachment = fields.Binary(string="Upload Document")
    document_description = fields.Text(string="Document Description")
    start_date = fields.Date(string="Start Date")
    expiry_date = fields.Date(string="Expiry Date")
    status = fields.Selection(
        [('active', 'Active'), 
         ('expiry_soon', 'Expiry Soon'),
         ('expired', 'Expired')],
        string="Document Status", default='active'
    )

    def check_expiry_soon_status(self):
        today = fields.Date.today()
        documents = self.search([])
        documents_to_notify = self.env['document.tracking']

        for document in documents:
            if document.expiry_date:
                alert_days = document.document_type_id.alert
                alert_date = document.expiry_date - timedelta(days=alert_days)

                if today >= document.expiry_date:
                    document.write({'status': 'expired'})
                    documents_to_notify |= document
                elif today >= alert_date:
                    document.write({'status': 'expiry_soon'})
                    documents_to_notify |= document
                else:
                    document.write({'status': 'active'})

        if documents_to_notify:
            self._send_consolidated_notification(documents_to_notify)

    def _send_consolidated_notification(self, documents):
        admin_group = self.env.ref('base.group_erp_manager', raise_if_not_found=False)
        hr_officer_group = self.env.ref('hr.group_hr_user', raise_if_not_found=False)

        recipient_users = self.env['res.users']
        
        if admin_group:
            admin_users = self.env['res.users'].search([
                ('groups_id', 'in', admin_group.id),
                ('email', '!=', False)
            ])
            recipient_users |= admin_users

        if hr_officer_group:
            hr_officer_users = self.env['res.users'].search([
                ('groups_id', 'in', hr_officer_group.id),
                ('email', '!=', False)
            ])
            recipient_users |= hr_officer_users

        recipient_emails = list(set(recipient_users.mapped('email')))

        if not recipient_emails:
            return

        document_details = ''.join([
            f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{doc.employee_id.name or ''}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{doc.document_type_id.name or ''}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{doc.document_number or ''}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{doc.expiry_date.strftime('%d-%b-%Y') if doc.expiry_date else ''}</td>
            </tr>
            """
            for doc in documents
        ])

        subject = "Reminder: Upcoming Document Expiry for Employees"
        body = f"""
            <p>Dear HR Team,</p>
            <p>This is a notification regarding the upcoming expiry of employee documents. Please find the details below:</p>
            <table style="border-collapse: collapse; width: 100%;">
                <thead>
                    <tr>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Employee Name</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Document Type</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Document Number</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Expiry Date</th>
                    </tr>
                </thead>
                <tbody>
                    {document_details}
                </tbody>
            </table>
            <p>We recommend initiating the renewal process at the earliest to ensure compliance and avoid any inconvenience.</p>
            <p>If you need further assistance, please let us know.</p>
            <p>Best regards,<br/>
            {self.env.user.name or 'Automated System'}<br/>
            {self.env.user.company_id.name or 'Your Company'}</p>
        """

        self.env['mail.mail'].create({
            'subject': subject,
            'body_html': body,
            'email_from': self.env.user.email or 'noreply@example.com',
            'email_to': ','.join(recipient_emails),
        }).send()
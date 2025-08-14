from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_code = fields.Char(string="Customer Code")
    latitude = fields.Float(string="Latitude")
    longitude = fields.Float(string="Longitude")
    cr_number = fields.Char(string="CR Number")
    country_city_id = fields.Many2one('res.country.state.city', string="City")

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        result = super().name_search(name=name, args=args, operator=operator, limit=limit)
        
        if name:
            args = args or []
            domain = ['|',
                ('customer_code', operator, name),
                ('name', operator, name)
            ]
            partners = self._search(expression.AND([domain, args]), limit=limit)
            additional_results = [(partner.id, partner.name) for partner in self.browse(partners)]
            existing_ids = set(dict(result).keys())
            for partner_id, partner_name in additional_results:
                if partner_id not in existing_ids:
                    result.append((partner_id, partner_name))
            if limit:
                result = result[:limit]
        
        return result

    @api.constrains('cr_number', 'vat')
    def validate_cr_number_and_vat(self):
        for record in self:
            if record.cr_number:
                if not record.cr_number.isdigit():
                    raise ValidationError(_('CR Number should be numeric'))
                if not len(record.cr_number) == 10:
                    raise ValidationError(_('CR Number should be 10 digits'))
            if record.vat:
                if not record.vat.isdigit():
                    raise ValidationError(_('Vat should be numeric'))
                if not len(record.vat) == 15:
                    raise ValidationError(_('Vat should be 15 digits'))
                

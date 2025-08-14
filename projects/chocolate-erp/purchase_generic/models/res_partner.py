from odoo import models, fields, api
from odoo.osv import expression

class ResPartner(models.Model):
    _inherit = 'res.partner'

    vendor_type = fields.Selection([('local_vendor', 'Local Vendor'), ('import_vendor', 'Import Vendor')])
    arabic_name = fields.Char(string="Arabic Name")
    vendor_code = fields.Char(string="Vendor Code")
    vendor_sub_group_id = fields.Many2one('res.partner', string="Vendor Sub Group")

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        result = super().name_search(name=name, args=args, operator=operator, limit=limit)
        
        if name:
            args = args or []
            domain = []
            domain += ['|',
                ('vendor_code', operator, name),
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
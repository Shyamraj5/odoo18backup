from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    last_name = fields.Char(string='Last Name')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], string='Gender')
    post_office = fields.Char(string='Post office')
    district = fields.Many2one('res.district', string='District')
    aadhar_no = fields.Char(string='Aadhar Card Number')
    lsgd_name = fields.Char(string='LSGD Name', required=True)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name}  {rec.last_name if rec.last_name else ''}"


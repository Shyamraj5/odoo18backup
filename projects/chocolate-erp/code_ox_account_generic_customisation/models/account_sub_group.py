from odoo import models, fields, api

class AccountSubGroup(models.Model):
    _name = 'account.sub.group'
    _description = 'Account Sub Group'

    name = fields.Char(string='Name', required=True)
    parent_id = fields.Many2one('account.sub.group', string='Parent Group', domain="[('id', '!=', id)]")

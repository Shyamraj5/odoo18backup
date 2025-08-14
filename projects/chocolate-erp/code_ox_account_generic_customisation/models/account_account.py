from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.account'

    parent_id = fields.Many2one('account.account',string='Parent', domain="[('id', '!=', id)]")
    account_group_id = fields.Many2one('account.sub.group', string='Parent Group', domain="[('parent_id', '=', False)]")
    account_sub_group_id = fields.Many2one('account.sub.group', string='Sub Group', domain="[('parent_id', '=', account_group_id)]")
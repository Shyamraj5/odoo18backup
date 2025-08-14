from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    refer_bonus = fields.Integer(string="Refer Reward", config_parameter ='diet.refer_bonus')
    referer_bonus = fields.Integer(string="Referer Bonus", config_parameter ='diet.referer_bonus')
    referral_message = fields.Char(string="Referral Message", config_parameter ='diet.referral_message')


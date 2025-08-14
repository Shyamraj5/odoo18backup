from odoo import fields, models, api


class HrEmployee(models.Model):
    """Add field into hr employee"""
    _inherit = 'hr.employee'

    limited_discount = fields.Integer(string="Discount Limit",
                                      help="Provide discount limit to each "
                                           "employee")
    
    @api.model
    def _load_pos_data_fields(self, config_id):
        return ['name', 'limited_discount', 'user_id', 'parent_id', 'pin']

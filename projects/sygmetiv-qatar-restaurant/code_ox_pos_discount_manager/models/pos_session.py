# -*- coding: utf-8 -*-
from odoo import models, api


class PosSession(models.Model):
    _inherit = "pos.session"

    @api.model
    def _load_pos_data_models(self, config_id):
        data = super()._load_pos_data_models(config_id)
        data += ['hr.employee']
        return data

    def _pos_ui_models_to_load(self):
        """Load hr.employee model into pos session"""
        result = super()._pos_ui_models_to_load()
        result += ['hr.employee']
        return result

    def _loader_params_hr_employee(self):
        """load hr.employee parameters"""
        result = super()._loader_params_hr_employee()
        result['search_params']['fields'].extend(
            ['limited_discount'])
        return result

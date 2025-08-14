from odoo import models, _


class PosConfig(models.Model):
    _inherit = "pos.config"

    def write(self, vals):
        vals['self_ordering_pay_after'] = 'meal'
        res = super().write(vals)
        return res
    
    def _compute_selection_pay_after(self):
        selection_each_label = _("Each Order")
        # version_info = service.common.exp_version()['server_version_info']
        # if version_info[-1] == '':
        #     selection_each_label = f"{selection_each_label} {_('(require Odoo Enterprise)')}"
        return [("meal", _("Meal")), ("each", selection_each_label)]
    
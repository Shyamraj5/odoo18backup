from odoo import fields, models


class BiPdcWizard(models.TransientModel):
    _name = "post.dated.wizard"
    _description = "Post Dated Wizard"

    pdc_ids = fields.Many2many("post.dated.check")
    date = fields.Date(string="Date")

    def action_deposit(self):
        for rec in self:
            for pdc in rec.pdc_ids:
                pdc.action_pdc_deposit(self.date)

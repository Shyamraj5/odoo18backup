from odoo import models, fields,api,_
from datetime import date


class CustomerHealthHistory(models.Model):
    _name = "customer.health.history"
    _description = "Health History"


    date = fields.Date(string="Date")
    weight = fields.Float(string="Weight(Kg)")
    height = fields.Float(string="Height(cm)")
    smm = fields.Float(string="SMM(Kg)")
    pbf = fields.Float(string="PBF(%)")
    bmi = fields.Float(string="BMI(Kg/m2)")
    notes = fields.Char(string="Notes")
    update = fields.Char(string="Update")
    partner_id = fields.Many2one('res.partner', string="Partner")

    def add_health_history(self):
       return {
            'name':_('Health History'),
            'view_mode':'form',
            'view_type':'form',
            'type':'ir.actions.act_window',
            'res_model':'customer.health.wizard',
            'target':'new',
        }
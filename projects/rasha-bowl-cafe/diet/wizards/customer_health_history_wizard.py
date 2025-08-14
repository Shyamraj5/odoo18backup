from odoo import models, fields


class CustomerHealthWizard(models.TransientModel):
    _name = "customer.health.wizard"
    _description = "Wizard for customer health history"

    height = fields.Float(string="Height")
    body_water = fields.Float(string="Total Body Water(Proteins)")
    building_muscle = fields.Float(string="Total Building Muscle(Proteins)")
    strengthening_bone = fields.Float(string="Total Strengthening Bone(Minerals)")
    excess_energy = fields.Float(string=" Total Storing Excess Energy(Body Fat Mass)")
    sum = fields.Float(string="Sum of the above(Weight)")
    weight = fields.Float(string="Weight(Kg)")
    smm = fields.Float(string="SMM(Kg)")
    pbf = fields.Float(string="PBF(%)")
    bmi = fields.Float(string="BMI(Kg/m2)")
    body_fat_mass = fields.Float(string="Body Fat Mass")
    notes = fields.Text(string="notes")
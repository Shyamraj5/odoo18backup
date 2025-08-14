from odoo import api,fields,models
from odoo.exceptions import ValidationError


class RouteAssignment(models.Model):
    _name = 'sales.route.assignment'
    _description = 'Route Assignment'

    salesperson_id = fields.Many2one('res.users', string='Salesperson', required=True,domain=lambda self: [('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)])
    route_ids = fields.Many2many('route.route', string='Routes')
    van_id = fields.Many2one('van.detail',string="Van")


    @api.constrains('van_id')
    def _check_van_unique(self):
        for record in self:
            if record.van_id:
                existing_assignment = self.search([
                    ('van_id', '=', record.van_id.id),
                    ('id', '!=', record.id)
                ])
                if existing_assignment:
                    raise ValidationError(
                        f"The van '{record.van_id.name}' is already assigned to '{existing_assignment.salesperson_id.name}'"
                    )
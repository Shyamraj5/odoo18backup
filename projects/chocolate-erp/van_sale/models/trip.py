from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time

class SalesPersonTrip(models.Model):
    _name = 'sales.person.trip'
    _description = 'Sales Person'

    salesperson_id = fields.Many2one(
        'res.users', string='Sales Person', default=lambda self: self.env.user, readonly=True
    )
    start_kilometer = fields.Float(string='Start Kilometer', required=True)
    end_kilometer = fields.Float(string='End Kilometer')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('running', 'Running'),
            ('ended', 'Ended'),
        ],
        string='State',
        default='draft',
        required=True,
    )
    route_ids = fields.One2many('sales.person.trip.line', 'sale_person_trip_id', string='Assigned Routes')
    start_km_image = fields.Binary(string="Start Km Image")
    end_km_image = fields.Binary(string="End Km Image")
    sales_amount = fields.Float(string="Sales Amount", compute='get_sales_and_collected_amount')
    collected_amount = fields.Float(string="Collected Amount", compute='get_sales_and_collected_amount')
    validated = fields.Boolean("Is Validated" ,default=False)
    validation_status = fields.Selection([
        ('approved','Approved'),
        ('rejected','Rejected'),
        ('waiting','Waiting For Approval')
       
    ], compute='_compute_validation_status')
    trip_start_time = fields.Datetime(string='Trip Start Time')
    trip_end_time = fields.Datetime(string='Trip End Time' )
    start_location_id = fields.Many2one('res.partner', string='Start Location')
    end_location_id = fields.Many2one('res.partner', string='End Location')


    @api.depends('date', 'salesperson_id')
    def get_sales_and_collected_amount(self):
        for record in self:
            start_date = datetime.combine(record.date, time.min)
            end_date = datetime.combine(record.date, time.max)
            sales = self.env['sale.order'].search([('sale_type', '=', 'vansale'), ('user_id', '=', record.salesperson_id.id), 
                                                   ('date_order', '>=', start_date), ('date_order', '<=', end_date)])
            record.sales_amount = sum(sales.mapped('amount_total'))
            collected_amount = self.env['account.payment'].search([('date', '=', record.date), ('payment_type', '=', 'inbound'), 
                                                                   ('activity_user_id', '=', record.salesperson_id.id)])
            record.collected_amount = sum(collected_amount.mapped('amount'))
    
    def action_start(self):
        assigned_routes = self.env['sales.route.assignment'].search([('salesperson_id', '=', self.salesperson_id.id)])
        if self.start_kilometer <= 0.0:
            raise UserError("Starting kilometer cannot be zero")
        self.trip_start_time = fields.Datetime.now()
        if assigned_routes.route_ids:
            route_lines = []
            for route in assigned_routes:
                for routes in route.route_ids:
                    for shop in routes.shops_ids:
                        route_lines.append({
                            'shop_id': shop.id,
                            'route_id': routes.id,
                            'sale_person_trip_id': self.id
                        })
            self.env['sales.person.trip.line'].create(route_lines)
            self.state = "running"

    
    def action_stop(self):
        self.state = 'ended'
        self.trip_end_time = fields.Datetime.now()


    def validate(self):
        self.validated = True


    @api.depends('validated')
    def _compute_validation_status(self):
         for record in self:
            if record.validated:
                record.validation_status = 'approved'
            else:
                record.validation_status = 'waiting'
    
    @api.constrains('salesperson_id', 'date')
    def _check_unique_trip_per_day(self):
        for record in self:
            trip_count = len(self.search([('salesperson_id', '=', record.salesperson_id.id), ('date', '=', record.date)]))
            if trip_count > 1:
                raise ValidationError('A salesperson can only create one trip per day.')



class SalesPersonTripLine(models.Model):
    _name = 'sales.person.trip.line'
    _description = 'Sales Person Trip Line'

    salesperson_id = fields.Many2one('res.users', string='Salesperson', related='sale_person_trip_id.salesperson_id')
    route_id = fields.Many2one('route.route', string='Routes')
    sale_person_trip_id = fields.Many2one('sales.person.trip')
    shop_id = fields.Many2one('res.partner', string='Shop')
    order_taken = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Order Taken')
    sale_ids = fields.Many2many('sale.order', string='Sales Orders')
    invoice_ids = fields.Many2many('account.move', string='Invoices')
    no_order_reason_id = fields.Many2one('order.reason',string='No Order Reason')
    reason = fields.Text(string='Reason')



    class NoOrderReason(models.Model):
        _name = 'order.reason'

        name= fields.Char(string='No Order Reason')

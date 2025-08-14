from odoo import models, fields, api, _
from odoo.exceptions import UserError

class KitchenUsage(models.Model):
    _name = 'kitchen.usage'
    _descritption = 'Kitchen Usage'
    _order = 'id DESC'

    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default=lambda self: _('New') , )
    location_id = fields.Many2one('stock.location',string='Source location')
    location_dest_id = fields.Many2one('stock.location' , string='Dest location')
    date_id = fields.Date(default=fields.Date.today, string='Date')
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    line_ids = fields.One2many('kitchen.usage.line', 'kitchen_usage_id')
    picking_id = fields.Many2one('stock.picking', string="Stock Picking")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string="State", default='draft', required=True)



    @api.model
    def default_get(self, default_field):
        values = super(KitchenUsage, self).default_get(default_field)
        if self.env['ir.config_parameter'].sudo().get_param('code_ox_kitchen_usage.location_id'):
            values['location_id']= int(self.env['ir.config_parameter'].sudo().get_param('code_ox_kitchen_usage.location_id'))


        if self.env['ir.config_parameter'].sudo().get_param('code_ox_kitchen_usage.location_dest_id'):
            values['location_dest_id']= int(self.env['ir.config_parameter'].sudo().get_param('code_ox_kitchen_usage.location_dest_id'))

        return values


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('kitchen.usage') or 'New'
        return super(KitchenUsage, self).create(vals)

    def action_confirm(self):
        """Check stock availability and create an internal transfer."""
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)

        if not warehouse:
            raise UserError(_("No warehouse found for your company!"))


        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', warehouse.id)
        ], limit=1)

        if not picking_type:
            raise UserError(_("No internal transfer operation type found!"))

        picking_vals = {
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'picking_type_id': picking_type.id,
            'origin': self.name,
            'move_ids_without_package': []
        }

        picking = self.env['stock.picking'].create(picking_vals)
        self.picking_id = picking


        for line in self.line_ids:
            available_qty = self._get_available_quantity(line.product_id, self.location_id)

            if line.quantity > available_qty:
                raise UserError(_(
                    "Not enough stock for product '%s' in location '%s'.\n"
                    "Requested: %s, Available: %s"
                ) % (line.product_id.display_name, self.location_id.display_name, line.quantity, available_qty))

            move_vals = {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_id.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'picking_id': picking.id,
            }
            self.env['stock.move'].create(move_vals)

        # Confirm and validate the transfer
        picking.action_confirm()
        picking.button_validate()

        self.write({'state': 'done'})



        source_location_id = int(self.env['ir.config_parameter'].sudo().get_param('code_ox_kitchen_usage.source_location'))
    
        replenishment_needed = False  # Flag to check if replenishment is required
        move_lines = []
        for line in self.line_ids:
            # Get on-hand stock instead of free_qty
            onhand_qty = line.product_id.sudo().with_context(location=self.location_id.id).qty_available
            
            # Fetch minimum quantity from procurement rules
            kitchen_procurement = self.env['kitchen.procurement'].search(
                [('product_id', '=', line.product_id.id)], limit=1
            )
            min_qty = kitchen_procurement.product_min_qty if kitchen_procurement else 0

            # Check if on-hand stock is below minimum
            if onhand_qty < min_qty:
                required_qty = min_qty - onhand_qty  # Only replenish the needed amount
                replenishment_needed = True

                move_vals = {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': required_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': source_location_id,
                    'location_dest_id': self.location_id.id,
                }
                move_lines.append(move_vals)
        next_vals = {
            'location_dest_id': self.location_id.id,
            'location_id': source_location_id,
            'picking_type_id': picking_type.id,
            'origin': self.name,
            'move_ids_without_package': [(0, 0, move_line) for move_line in move_lines]
        }

        # Create replenishment picking only if needed
        if replenishment_needed:
            next_picking = self.env['stock.picking'].create(next_vals)
            next_picking.action_confirm()
   

    def _get_available_quantity(self, product, location):
        """Check available quantity of the product in the specified location."""
        quant = self.env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id)
        ], limit=1)
        return quant.quantity if quant else 0
    
    def action_picking_list_all(self):
        return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'res_id': self.picking_id.id,
                'target': 'new',
            }
    
    def unlink(self):
        for record in self:
            if record.state == 'done':
                raise UserError(_('You cannot delete done transfer'))
        return super(KitchenUsage, self).unlink()
   

class KitchenUsageLine(models.Model):
    _name = 'kitchen.usage.line'
    _description = 'Kitchen Usage Line'

    kitchen_usage_id = fields.Many2one('kitchen.usage', string="Kitchen Usage")
    product_id = fields.Many2one('product.product', string="Product")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    quantity = fields.Float(string="Quantity")
    

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
    


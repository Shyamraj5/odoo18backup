from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BranchTransferIn(models.Model):
    _name = 'branch.transfer.in'
    _description = 'Branch Transfer In'
    _inherit = ['mail.thread']

    name = fields.Char(string="Reference", default='New')
    branch_id = fields.Many2one('res.company', string="Branch", required=True)
    vendor_id = fields.Many2one('res.partner', string="Vendor", related='branch_id.partner_id', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='Status', default='draft', tracking=True)
    line_ids = fields.One2many('branch.transfer.in.line', 'transfer_id', string="Transfer Lines")
    picking_id = fields.Many2one('stock.picking', string="Internal Transfer", readonly=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id, readonly=True, store=True)

    amount_total = fields.Monetary(string="Total Amount", compute="_compute_totals", store=True)
    margin_total = fields.Monetary(string="Total Margin", compute="_compute_totals", store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    picking_ids = fields.One2many('stock.picking', 'branch_transfer_in_id')
    journal_entry_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    date = fields.Datetime(string="Date", default=fields.Datetime.now, tracking=True)
    return_transfer_ids = fields.One2many('branch.transfer.out', 'returned_transfer_in_id',  string="Returns")
    branch_transfer_out_id = fields.Many2one('branch.transfer.out', string='Source Branch Transfer Out')
    is_return = fields.Boolean(string="Is Return", store=True)

    @api.depends('line_ids.total')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(line.total for line in rec.line_ids)

    @api.depends('line_ids.total', 'line_ids.margin')
    def _compute_totals(self):
        for rec in self:
            rec.amount_total = sum(line.total for line in rec.line_ids)
            rec.margin_total = sum(line.total_margin for line in rec.line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('branch.transfer.in.sequence') or _('New')
        return super(BranchTransferIn, self).create(vals_list)
    
    def action_confirm(self):
        self.sudo().with_context(is_branch_return=self.is_return).create_receipt_picking()
        self.write({'state': 'confirmed'})

    def action_done(self):
        for record in self:
            for picking in record.picking_ids.filtered(lambda x: x.state not in ['done', 'cancel']):
                picking.button_validate()
            return_out_id = record.branch_transfer_out_id.sudo().returned_transfer_in_id
            if return_out_id:
                record.with_context(branch_transfer_out_id = return_out_id.id)._create_accounting_entry()
            else:
                record._create_accounting_entry()
            record.state = 'done'

    def action_return(self):
        self.ensure_one()

        # Create branch.transfer.out record
        transfer_out = self.env['branch.transfer.out'].create({
            'branch_id': self.branch_id.id,
            'customer_id': self.vendor_id.id, 
            'company_id': self.company_id.id,
            'state': 'draft',
            'returned_transfer_in_id': self.id,
        })
        picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'outgoing'),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
        location_id = picking_type.default_location_src_id.id

        # Create lines in transfer.out
        lines = []
        for line in self.line_ids:
            move = self.env['stock.move'].search([
                ('branch_transfer_in_line_id', '=', line.id),
                ('picking_id', '=', self.picking_id.id)
            ], limit=1)

            # Get lot_id from move_line_ids (if any)
            lot_id = move.move_line_ids[:1].lot_id.id if move.move_line_ids else False
            stock_quant = self.env['stock.quant'].search([
                ('location_id', '=', location_id),
                ('lot_id', '=', lot_id)
            ], limit=1)
            lines.append((0, 0, {
                'product_id': line.product_id.id,
                'description': line.description,
                'uom_id': line.uom_id.id,
                'qty': stock_quant.available_quantity if stock_quant else 0,
                'cost': line.cost,
                'sale_price':line.unit_price,
                'lot_id': lot_id,
                'returned_transfer_in_line_id': line.id,
            }))

        transfer_out.line_ids = lines

        return {
            'type': 'ir.actions.act_window',
            'name': 'Returned Transfer Out',
            'res_model': 'branch.transfer.out',
            'view_mode': 'form',
            'res_id': transfer_out.id,
            'target': 'current',
        }

    def action_view_return_transfers(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Return Transfers'),
            'view_mode': 'list,form',
            'res_model': 'branch.transfer.out',
            'domain': [('returned_transfer_in_id', '=', self.id)],
            'context': {'default_returned_transfer_in_id': self.id},
            'target': 'current',
        }
        if len(self.return_transfer_ids) == 1:
            action['res_id'] = self.return_transfer_ids.id
            action['view_mode'] = 'form'
        return action

    def create_receipt_picking(self):
        self.ensure_one()        
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        location_id = picking_type.default_location_src_id.id
        location_dest_id = picking_type.default_location_dest_id.id
        is_branch_return = self.is_return
        picking_vals = {
            'partner_id': self.vendor_id.id,
            'picking_type_id': picking_type.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'company_id': self.company_id.id,
            'origin': self.name,
            'branch_transfer_in_id': self.id,
            'is_branch_return': is_branch_return,
        }
        move_lines = []
        source_transfer_out_id = self.branch_transfer_out_id.returned_transfer_in_id.branch_transfer_out_id
        for line in self.line_ids:
            lot_id = False
            source_line = source_transfer_out_id.line_ids.filtered(lambda x: x.product_id == line.product_id)
            if source_line:
                source_move = self.env['stock.move'].search([('branch_transfer_out_line_id', '=', source_line[0].id)])
                lot_id = source_move.move_line_ids[:1].lot_id.id if source_move.move_line_ids else False
            # Compute product cost in the selected UoM
            product_cost = line.uom_id._compute_price(line.cost, line.product_id.uom_id)
            move_lines.append((0, 0, {
                'name': line.description or line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty,
                'product_uom': line.uom_id.id,
                'price_unit': product_cost,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'branch_transfer_in_line_id': line.id,
                'restrict_lot_id': line.source_lot_id.source_lot_id.id if is_branch_return else False,
            }))
        picking_vals['move_ids_without_package'] = move_lines

        picking = self.env['stock.picking'].create(picking_vals)
        picking.action_confirm()
        if not is_branch_return:
            for move in picking.move_ids:
                for line in move.move_line_ids:
                    source_lot = self.sudo().line_ids.filtered(lambda x: x.product_id.id == move.product_id.id)
                    company = self.sudo().branch_transfer_out_id.company_id
                    lot_name = f'{company.name}-{source_lot.source_lot_id.name}'
                    stock_lot = self.env['stock.lot'].search_count([
                        ('source_lot_id', '=', source_lot.source_lot_id.id)])
                    if stock_lot:
                        lot = self.env['stock.lot'].create({
                        'name': f'{company.branch_code if company.branch_code else company.name}-{source_lot.source_lot_id.name} ({stock_lot})',
                        'product_id': move.product_id.id,
                        'source_lot_id': source_lot.source_lot_id.id,
                    })
                    else:
                        lot = self.env['stock.lot'].create({
                            'name': f'{company.branch_code if company.branch_code else company.name}-{source_lot.source_lot_id.name}',
                            'product_id': move.product_id.id,
                            'source_lot_id': source_lot.source_lot_id.id,
                        })
                    line.lot_id = lot.id
        self.picking_id = picking
        return picking
    
    def open_picking(self):
        picking_ids = self.picking_ids
        if len(picking_ids) > 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Receipt Picking'),
                'view_mode': 'list,form',
                'res_model': 'stock.picking',
                'domain': [('id', 'in', picking_ids.ids)],
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Receipt Picking'),
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'res_id':picking_ids[0].id,
                'target': 'current',
            }
        
    def _create_accounting_entry(self):
        AccountMove = self.env['account.move']
        AccountMoveLine = self.env['account.move.line']
        IrConfig = self.env['ir.config_parameter'].sudo()

        for record in self:
            total_cost = sum(line.qty * line.cost for line in record.line_ids)
            total_margin = record.margin_total
            total_payable = record.amount_total
            partner = record.vendor_id

            if not partner.property_account_payable_id:
                raise UserError(_("Partner %s has no payable account configured.") % partner.name)

            # Fetch suspense account from config
            suspense_account_id = record.company_id.branch_suspense_account_id.id
            unrealized_account_id = record.company_id.unrealized_branch_profit_account_id.id
            is_return = record.is_return

            if not suspense_account_id:
                raise UserError(_("Please set Branch Suspense Account in General Settings."))
            
            returned_transfer_out_id = self.env.context.get('branch_transfer_out_id')
            move_lines = []

            # Credit partner payable account
            move_lines.append((0, 0, {
                'account_id': partner.property_account_payable_id.id,
                'partner_id': partner.id,
                'name': 'Payable from Branch Transfer',
                'credit': total_payable,
                'debit': 0.0,
            }))

            # Group products by category and sum their costs
            category_costs = {}
            for line in record.line_ids:
                category = line.product_id.categ_id
                if not category.branch_input_account_id:
                    raise UserError(_("Product category %s has no Branch Input Account set.") % category.name)
                
                line_cost = line.qty * line.cost
                if category in category_costs:
                    category_costs[category] += line_cost
                else:
                    category_costs[category] = line_cost

            # Create move lines for each category
           
            for category, cost in category_costs.items():
                move_lines.append((0, 0, {
                    'account_id': category.branch_input_account_id.id,
                    'partner_id': partner.id,
                    'name': f"Cost - {category.name}",
                    'credit': 0.0,
                    'debit': cost,
                }))

            # Debit  branch suspense
            move_lines.append((0, 0, {
                'account_id':  unrealized_account_id if returned_transfer_out_id or is_return  else suspense_account_id,
                'partner_id': partner.id,
                'name': "Unrealized Profit" if returned_transfer_out_id or is_return else "Branch Suspense", 
                'credit': 0.0,
                'debit': total_margin,
            }))

            # Create journal entry
            journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
            if not journal:
                raise UserError(_("No general journal found. Please configure at least one."))

            move = AccountMove.create({
                'ref': record.name,
                'journal_id': journal.id,
                'date': fields.Date.context_today(self),
                'line_ids': move_lines,
            })
            move.action_post()
            record.journal_entry_id = move.id

    def action_view_journal_entry(self):
        self.ensure_one()
        if not self.journal_entry_id:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entry',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.journal_entry_id.id,
            'target': 'current',
        }

class BranchTransferInLine(models.Model):
    _name = 'branch.transfer.in.line'
    _description = 'Branch Transfer In Line'

    transfer_id = fields.Many2one('branch.transfer.in', string="Transfer")
    product_id = fields.Many2one('product.product', string="Product", required=True)
    description = fields.Text(string="Description")
    lot_id = fields.Many2one('stock.lot', string="Lot", domain="[('product_id', '=', product_id)]")
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", domain="product_uom_domain")
    qty = fields.Float(string="Quantity", default=1.0)
    unit_price = fields.Float(string="Price")
    cost = fields.Float(string="Cost")
    total = fields.Float(string="Total", compute="_compute_total", store=True)
    margin = fields.Float(string="Margin")
    total_margin = fields.Float(string="Total Margin", compute="_compute_margin", store=True)
    product_uom_domain = fields.Binary(string='Product UoM Domain', compute='_compute_product_uom_domain')
    branch_transfer_out_line_id = fields.Many2one('branch.transfer.out.line')
    source_lot_id = fields.Many2one('stock.lot', string="Source Lot")

    @api.depends('product_id')
    def _compute_product_uom_domain(self):
        for line in self:
            uom_ids = [line.product_id.uom_id.id]
            if line.product_id.product_uom_ids:
                uom_ids += line.product_id.product_uom_ids.ids
            else:
                uom_ids += line.product_id.uom_id.category_id.uom_ids.ids
            line.product_uom_domain = [('id', 'in', uom_ids)]

    @api.depends('qty', 'unit_price')
    def _compute_total(self):
        for line in self:
            line.total = line.qty * line.unit_price

    @api.depends('margin', 'qty')
    def _compute_margin(self):
        for line in self:
            line.total_margin = line.margin * line.qty

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.uom_id = self.product_id.uom_id.id if self.product_id.uom_id else False
            self.unit_price = self.product_id.standard_price or 0.0
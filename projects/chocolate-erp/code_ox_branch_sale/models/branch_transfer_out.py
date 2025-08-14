# models/branch_transfer_out.py

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BranchTransferOut(models.Model):
    _name = 'branch.transfer.out'
    _description = 'Branch Transfer Out'
    _inherit = ['mail.thread']

    name = fields.Char(string="Reference",  default='New')
    branch_id = fields.Many2one('res.company', string="Branch", required=True)
    customer_id = fields.Many2one(
        'res.partner', string="Customer", domain="[('company_id', '=', branch_id)]" )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='Status', default='draft', tracking=True)
    line_ids = fields.One2many('branch.transfer.out.line', 'transfer_id', string="Transfer Lines")
    picking_id = fields.Many2one('stock.picking', string="Internal Transfer", readonly=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id, readonly=True, store=True)
    journal_entry_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)


    amount_total = fields.Monetary(string="Total Amount", compute="_compute_totals", store=True)
    margin_total = fields.Monetary(string="Total Margin", compute="_compute_totals", store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    location_id = fields.Many2one(
    'stock.location',
    string="Source Location",
    default=lambda self: self._get_default_location_id(),
    required=True)
    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    returned_transfer_in_id = fields.Many2one('branch.transfer.in', string="Returned In ID")
    branch_transfer_in_id = fields.Many2one('branch.transfer.in', string='Linked Branch Transfer In')
    is_return = fields.Boolean(string="Is Return", help="Indicates if this transfer is a return from a previous transfer in.")

    def _get_default_location_id(self):
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        return warehouse.lot_stock_id.id if warehouse and warehouse.lot_stock_id else False

    @api.depends('line_ids.total', 'line_ids.margin')
    def _compute_totals(self):
        for rec in self:
            rec.amount_total = sum(line.total for line in rec.line_ids)
            rec.margin_total = sum(line.total_margin for line in rec.line_ids)

    @api.onchange('branch_id')
    def _onchange_branch_id_set_customer(self):
        if self.branch_id:
            self.customer_id = self.branch_id.partner_id.id
        else:
            self.customer_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('branch.transfer.out.sequence') or _('New')
        records = super(BranchTransferOut, self).create(vals_list)
        return records

    def action_confirm(self):
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']

        for record in self:
            if not record.line_ids:
                raise UserError(_("You must add at least one product line before confirming the transfer."))

            warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)
            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'outgoing'),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
            location_id = picking_type.default_location_src_id.id
            location_dest_id = picking_type.default_location_dest_id.id

            if not picking_type:
                raise UserError(_("No internal picking type found for company: %s") % record.company_id.name)

            for line in record.line_ids:
                if line.returned_transfer_in_line_id:
                    original_qty = line.returned_transfer_in_line_id.qty
                    if line.qty > original_qty:
                        raise UserError(_("You cannot return more than the received quantity for the products."))
                if line.lot_id:
                    quant = self.env['stock.quant'].search([
                        ('lot_id', '=', line.lot_id.id),
                        ('product_id', '=', line.product_id.id),
                        ('location_id.usage', '=', 'internal'),
                    ], limit=1)

                    available_qty = quant.quantity if quant else 0.0

                    if available_qty < line.qty:
                        raise UserError(_(
                            "Insufficient stock in lot %s for product %s.\n"
                            "Required: %s, Available: %s") % (
                                line.lot_id.name,
                                line.product_id.display_name,
                                line.qty,
                                available_qty
                            ))

            picking = StockPicking.create({
                'partner_id': record.customer_id.id,
                'picking_type_id': picking_type.id,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'origin': record.name,
                'company_id': record.company_id.id,
                'branch_transfer_out_id': record.id,
            })
            for line in record.line_ids:
                StockMove.create({
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.qty,
                    'restrict_lot_id': line.lot_id.id if line.lot_id else False,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'picking_id': picking.id,
                    'company_id': record.company_id.id,
                    'branch_transfer_out_line_id': line.id,
                })
            picking.action_confirm()
            record.picking_id = picking.id
            record.write({'state': 'confirmed'})

    def open_picking(self):
        self.ensure_one()
        if not self.picking_id:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': _('Delivery Picking'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': self.picking_id.id,
            'target': 'current',
        }

    def action_done(self):
        for record in self:
            if not record.picking_id:
                raise UserError(_("No internal transfer (picking) is linked to this record."))

            if record.picking_id.state not in ('done', 'cancel'):
                record.picking_id.button_validate()
            if record.returned_transfer_in_id or record.is_return:
                record.with_context(
                    return_transfer_id=record.returned_transfer_in_id.id,is_return=record.is_return
                )._create_accounting_entry()
            else:
                record._create_accounting_entry()
            record.with_context(is_return=record.is_return).create_batch_transfer_in()
            record.state = 'done'

    def _create_accounting_entry(self):
        AccountMove = self.env['account.move']
        AccountMoveLine = self.env['account.move.line']
        IrConfig = self.env['ir.config_parameter'].sudo()

        for record in self:
            total_cost = sum(line.qty * line.cost for line in record.line_ids)
            total_margin = record.margin_total
            partner = record.customer_id

            if not partner.property_account_receivable_id:
                raise UserError(_("Partner %s has no receivable account configured.") % partner.name)

            # Fetch unrealized profit account from config
            unrealized_account_id = record.company_id.unrealized_branch_profit_account_id.id
            if not unrealized_account_id:
                raise UserError(_("Please set Unrealized Branch Profit Account in General Settings."))
            unrealized_account_id = int(unrealized_account_id)

            move_lines = []
            returned_transfer_in_id = self.env.context.get('return_transfer_id')
            is_return = self.env.context.get('is_return', False)
            out_suspense_account_id = record.company_id.branch_suspense_account_id.id            # Debit partner receivable account
            move_lines.append((0, 0, {
                'account_id': partner.property_account_receivable_id.id,
                'partner_id': partner.id,
                'name': 'Receivable from Branch Transfer',
                'debit': total_cost + total_margin,
                'credit': 0.0,
            }))

            # Group products by category and sum their costs
            category_costs = {}
            for line in record.line_ids:
                category = line.product_id.categ_id
                if not category.branch_output_account_id:
                    raise UserError(_("Product category %s has no Branch Output Account set.") % category.name)
                
                line_cost = line.qty * line.cost
                if category in category_costs:
                    category_costs[category] += line_cost
                else:
                    category_costs[category] = line_cost

            # Create move lines for each category
            
            for category, cost in category_costs.items():
                move_lines.append((0, 0, {
                    'account_id': category.branch_output_account_id.id,
                    'partner_id': partner.id,
                    'name': f"Cost - {category.name}",
                    'debit': 0.0,
                    'credit': cost,
                }))

            # Credit unrealized profit account
            move_lines.append((0, 0, {
                'account_id': out_suspense_account_id if returned_transfer_in_id or is_return else unrealized_account_id,
                'partner_id': partner.id,
                'name': "Branch Suspense" if  returned_transfer_in_id or  is_return else "Unrealized Profit ",
                'debit': 0.0,
                'credit': total_margin,
            }))

            # Create journal entry
            journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
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
    
    def create_batch_transfer_in(self):
        transfer_in = self.env['branch.transfer.in'].sudo().create({
            'branch_id': self.company_id.id,
            'vendor_id': self.company_id.partner_id.id,
            'company_id': self.branch_id.id,
            'branch_transfer_out_id': self.id,  
            'is_return': self.is_return,
            'line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'qty': line.qty,
                'uom_id': line.uom_id.id,
                'unit_price': line.sale_price,
                'cost': line.cost,
                'margin': line.margin,
                'total_margin': line.total_margin,
                'branch_transfer_out_line_id': line.id,
                'source_lot_id' : line.lot_id.id if line.lot_id else False,
            }) for line in self.line_ids]
        })
        self.branch_transfer_in_id = transfer_in.id


class BranchTransferOutLine(models.Model):
    _name = 'branch.transfer.out.line'
    _description = 'Branch Transfer Out Line'

    transfer_id = fields.Many2one('branch.transfer.out', string="Transfer")
    product_id = fields.Many2one('product.product', string="Product", required=True)
    description = fields.Text(string="Description")
    lot_id = fields.Many2one('stock.lot', string="Lot" , domain="[('product_id', '=', product_id)]")
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", domain="product_uom_domain")
    qty = fields.Float(string="Quantity", default=1.0)
    sale_price = fields.Float(string="Sale Price")
    cost = fields.Float(string="Cost", compute="_compute_purchase_price_calc", store=True)
    margin = fields.Float(string="Margin", compute="_compute_margin", store=True)
    total_margin = fields.Float(string="Total Margin", compute="_compute_margin", store=True)
    total = fields.Float(string="Total", compute="_compute_total", store=True)
    lot_domain = fields.Char(compute="_compute_lot_domain", store=True)
    product_uom_domain = fields.Binary(string='Product UoM Domain', compute='_compute_product_uom_domain')
    returned_transfer_in_line_id = fields.Many2one('branch.transfer.in.line', string="Returned In Line ID")
    branch_transfer_in_line_id = fields.Many2one('branch.transfer.in.line')

    @api.depends('product_id', 'lot_id', 'uom_id', 'transfer_id.is_return')
    def _compute_purchase_price_calc(self):
        for line in self:
            if line.lot_id and line.uom_id:
                line.cost = line.product_id.uom_id._compute_price(
                    line.lot_id.with_company(line.transfer_id.company_id).standard_price,
                    line.uom_id
                )
            else:
                line.cost = 0.0


    @api.depends('product_id')
    def _compute_product_uom_domain(self):
        for line in self:
            uom_ids = [line.product_id.uom_id.id]
            if line.product_id.product_uom_ids:
                uom_ids += line.product_id.product_uom_ids.ids
            else:
                uom_ids += line.product_id.uom_id.category_id.uom_ids.ids
            line.product_uom_domain = [('id', 'in', uom_ids)]

    @api.depends('product_id')
    def _compute_lot_domain(self):
        for line in self:
            if line.product_id:
                stock_quants = self.env['stock.quant'].search([('product_id', '=', line.product_id.id),
                                                               ('location_id.usage', '=', 'internal'),
                                                               ('company_id', '=', line.transfer_id.company_id.id)])
                lot_ids = stock_quants.mapped('lot_id').ids
                if lot_ids:
                    line.lot_domain = [('id', 'in', lot_ids)]
            else:
                line.lot_domain = [('id', '=', False)]


    @api.depends('sale_price', 'cost', 'qty')
    def _compute_margin(self):
        for line in self:
            line.margin = line.sale_price - line.cost
            line.total_margin = (line.sale_price - line.cost) * line.qty

    @api.depends('qty', 'sale_price')
    def _compute_total(self):
        for line in self:
            line.total = line.qty * line.sale_price    

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name or ''
            self.uom_id = self.product_id.uom_id.id if self.product_id.uom_id else False
            self.sale_price = self.product_id.lst_price or 0.0

            # Only set cost from product if no lot is selected yet
            if not self.lot_id:
                self.cost = self.product_id.standard_price or 0.0

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        for line in self:
            if line.lot_id and hasattr(line.lot_id, 'standard_price'):
                line.cost = line.lot_id.standard_price
                if line.transfer_id.is_return:
                    line.sale_price = line.cost + line.lot_id.margin or 0.0
                    picking_type = self.env['stock.picking.type'].search([
                            ('code', '=', 'outgoing'),
                            ('company_id', '=', self.transfer_id.company_id.id),
                        ], limit=1)
                    location_id = picking_type.default_location_src_id.id
                    stock_quant = self.env['stock.quant'].search([
                        ('location_id', '=', location_id),
                        ('lot_id', '=', line.lot_id.id),
                    ], limit=1)
                    line.qty = stock_quant.available_quantity if stock_quant else 0


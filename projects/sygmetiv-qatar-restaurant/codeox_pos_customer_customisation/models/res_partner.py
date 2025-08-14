from odoo import models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _load_pos_data_domain(self, data):
        config_id = self.env['pos.config'].browse(data['pos.config']['data'][0]['id'])

        # Collect partner IDs from loaded orders
        loaded_order_partner_ids = {order['partner_id'] for order in data['pos.order']['data']}

        # Extract partner IDs from the tuples returned by get_limited_partners_loading
        limited_partner_ids = {partner[0] for partner in config_id.get_limited_partners_loading()}

        limited_partner_ids.discard(self.env.user.partner_id.id)  # Ensure current user is excluded
        partner_ids = limited_partner_ids.union(loaded_order_partner_ids)

        # Refine partner list to exclude users and employees
        partners = self.env['res.partner'].search([
            ('id', 'in', list(partner_ids)),
            ('customer_rank', '>', 0),
            ('active', '=', True)
        ])
        return [('id', 'in', partners.ids)]

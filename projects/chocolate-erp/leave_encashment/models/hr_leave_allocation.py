from odoo import fields, models, api


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    leave_encashment_history_ids = fields.One2many('hr.leave.encashment.history', 'leave_allocation_id', string='Leave Encashment History')


class HrLeaveEncashmentHistory(models.Model):
    _name = 'hr.leave.encashment.history'
    _description = 'Leave Encashment History'

    leave_allocation_id = fields.Many2one('hr.leave.allocation', string='Leave Allocation')
    leave_encashment_id = fields.Many2one('leave.encashment', string='Leave Encashment')
    days_encashed = fields.Float(string='Days Encashed', related='leave_encashment_id.leave_encash')

    def create(self, vals):
        res = super(HrLeaveEncashmentHistory, self).create(vals)
        res.update_allocation_days()
        return res
    
    def update_allocation_days(self):
        for record in self:
            allocated_days = record.leave_allocation_id.number_of_days
            encash_days = record.leave_encashment_id.leave_encash
            record.leave_allocation_id.write({'number_of_days': allocated_days - encash_days})
        return True
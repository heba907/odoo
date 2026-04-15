# -*- coding: utf-8 -*-
# Part of NexOrionis Techsphere(https://nexorionis.site).

from odoo import models, fields, api,_

class SparePartConfirmWizard(models.TransientModel):
    _name = 'spare.part.confirm.wizard'
    _description = 'Spare Part Confirm Wizard'

    spare_part_stock_id = fields.Many2one('spare.part.stock', string='Spare Part Stock')
    spare_part_stock_line_id = fields.Many2one('spare.part.stock.line', string='Spare Part Line Stock')
    spare_part_stock_in_id = fields.Many2one('spare.part.stock.in', string='Spare Part In Stock')
    is_confirm = fields.Boolean(string='Confirm', default=False)
    is_done = fields.Boolean(string='Done', default=False)
    is_reverse = fields.Boolean(string='Done', default=False)
    is_return = fields.Boolean(string='Return', default=False)

    def action_confirm(self):
        # If confirmed, proceed with the main function from spare part stock
        if self.spare_part_stock_id:
            if self.is_confirm:
                self.spare_part_stock_id._action_confirm()
            if self.is_return:
                self.spare_part_stock_id.action_return()
            if self.is_done:
                self.spare_part_stock_id._action_done()
            if self.is_reverse:
                self.spare_part_stock_id._action_add_stock_in()
        if self.spare_part_stock_line_id:
            if self.is_confirm:
                self.spare_part_stock_line_id._action_done()
            if self.is_return:
                self.spare_part_stock_line_id._action_return()
        if self.spare_part_stock_in_id:
            if self.is_confirm:
                self.spare_part_stock_in_id._action_done()
            if self.is_return:
                self.spare_part_stock_in_id._action_return()

        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

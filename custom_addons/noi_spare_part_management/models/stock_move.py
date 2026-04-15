# -*- coding: utf-8 -*-
# Part of NexOrionis Techsphere(https://nexorionis.odoo.com).

from odoo import models, fields, api

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    spare_part_id = fields.Many2one(
        'spare.part.stock', string='Spare Parts'
    )


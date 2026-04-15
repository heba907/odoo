# -*- coding: utf-8 -*-
# Part of NexOrionis Techsphere(https://nexorionis.site).

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    spare_part_lines = fields.One2many(
        'product.spare.part.line', 'product_tmpl_id', string='Spare Parts'
    )


class ProductSparePartLine(models.Model):
    _name = 'product.spare.part.line'
    _description = 'Spare Part Line'

    product_tmpl_id = fields.Many2one('product.template', string='Parent Product', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    uom_id = fields.Many2one('uom.uom',related='product_tmpl_id.uom_id')
    cost = fields.Float(string='Cost', store=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost', store=True)

    @api.depends('quantity', 'cost')
    def _compute_total_cost(self):
        for line in self:
            line.total_cost = line.quantity * line.cost


    @api.onchange('product_id')
    def default_cost(self):
        for rec in self:
            if rec.product_id:
                rec.cost = rec.product_id.standard_price
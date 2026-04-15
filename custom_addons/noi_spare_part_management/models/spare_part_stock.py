# -*- coding: utf-8 -*-
# Part of NexOrionis Techsphere(https://nexorionis.site).

from odoo import models, fields, api,_
from odoo.cli.server import report_configuration
from odoo.exceptions import UserError
from odoo.sql_db import check


class SparePartStock(models.Model):
    _name = 'spare.part.stock'
    _description = 'Spare Part Stock'
    _rec_name = 'product_id'
    _order = 'id desc'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_tracking = fields.Selection(related='product_id.tracking')
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    uom_id = fields.Many2one('uom.uom',related='product_id.uom_id')

    date = fields.Date(string='Date', default=fields.Date.today)
    location_id = fields.Many2one(
        'stock.location',
        string='From',
        domain="[('usage', '=', 'internal'), ('company_id', '=', company_id)]",
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number',
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]")
    stock_lines = fields.One2many('spare.part.stock.line', 'stock_id', string='Stock Lines')
    stock_in_lines = fields.One2many('spare.part.stock.in', 'stock_id', string='Stock In')
    move_line_ids = fields.One2many('stock.move.line', 'spare_part_id', string='Move Lines')
    state = fields.Selection(
        [('draft', 'Draft'),
                ('confirm', 'Confirm'),
                ('done', 'Done'),
                ('reverse', 'Reverse'),
                ('cancel', 'Cancel'),
         ], string='Status', readonly=True, index=True, copy=False, default='draft',
        tracking=True)
    cost = fields.Float(string='Cost')
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost', store=True)

    @api.depends('quantity', 'cost')
    def _compute_total_cost(self):
        for line in self:
            line.total_cost = line.quantity * line.cost

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            # Clear existing lines
            self.stock_lines = [(5, 0, 0)]
            self.cost = self.product_id.standard_price

            # Search for spare parts related to the parent product
            spare_parts = self.env['product.spare.part.line'].search([
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)
            ])

            # Prepare new lines
            new_lines = []
            for part in spare_parts:
                if not part.product_id or not part.uom_id:
                    continue  # Skip invalid records

                line_values = {
                    'product_id': part.product_id.id,
                    'origin_quantity': part.quantity,
                    'quantity': (part.quantity * self.quantity) if self.quantity else 0,
                    'quantity_done': (part.quantity * self.quantity) if self.quantity else 0,
                    'uom_id': part.uom_id.id,
                    'cost': part.cost if part.cost else part.product_id.standard_price,
                    'movement_type': 'out',  # Ensure this field is provided
                }
                new_lines.append((0, 0, line_values))
            if new_lines:
                self.stock_lines = new_lines
    #
    @api.onchange('quantity')
    def change_product_spare_lines(self):
        for rec in self:
            for line in rec.stock_lines:
                line.quantity = line.origin_quantity * rec.quantity
                line.quantity_done = line.origin_quantity * rec.quantity

    def _update_valuation_cost(self,move,stock,is_add,is_reverse,is_transit):
        if is_reverse:
            valuation = self.env['stock.valuation.layer'].sudo().search([('stock_move_id', '=', move.id)])
            if valuation:
                remaining_qty = valuation.remaining_qty
                valuation.account_move_id.button_draft()
                valuation.account_move_id.unlink()
                valuation.sudo().unlink()
                if not is_transit:
                    fifo_vals = move.product_id._run_fifo(abs(move.quantity_done), move.company_id)
                    remaining_qty = fifo_vals.get('remaining_qty')
                    remaining_value = fifo_vals.get('remaining_value')
                    valuation_layer = self.env['stock.valuation.layer'].sudo().create({
                        'value': (move.quantity_done * stock.cost) if is_add else (-move.quantity_done * stock.cost),
                        'unit_cost': stock.cost,
                        'quantity': move.quantity_done if is_add else -move.quantity_done,
                        'description': move.reference and '%s - %s' % (move.reference, move.product_id.name) or move.product_id.name,
                        'stock_move_id': move.id,
                        'product_id': stock.product_id.id,
                        'company_id': stock.company_id.id,
                        'remaining_qty': remaining_qty if is_add else 0,
                        'remaining_value': (move.quantity_done * stock.cost) if is_add else 0,
                        })
                    move.product_price_update_before_done()
                    # if is_add:
                    #     move.product_id.sudo().write({'standard_price': valuation_layer.unit_cost})
                    valuation_layer._validate_accounting_entries()
                    valuation_layer._validate_analytic_accounting_entries()

                    valuation_layer._check_company()

                    # For every in move, run the vacuum for the linked product.
                    products_to_vacuum = move.mapped('product_id')
                    company = move.mapped('company_id') and move.mapped('company_id')[
                        0] or self.env.company
                    products_to_vacuum._run_fifo_vacuum(company)
            return True

    def action_done(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmation',
            'res_model': 'spare.part.confirm.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('noi_spare_part_management.spare_part_confirm_wizard_form_view').id,
            'target': 'new',
            'context': {
                'default_spare_part_stock_id': self.id,
                'default_is_done': True,
            },
        }

    def _action_done(self):
        for record in self:
            # Call _action_done on all related lines
            record.stock_lines._action_done()

            # Update the state of the main record
            record.state = 'done'

    def action_cancel(self):
        self.state='cancel'

    def action_confirm(self):
        # Open the confirmation wizard first
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmation',
            'res_model': 'spare.part.confirm.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('noi_spare_part_management.spare_part_confirm_wizard_form_view').id,
            'target': 'new',
            'context': {
                'default_spare_part_stock_id': self.id,
                'default_is_confirm': True,
                'default_is_return': False,
            },
        }

    def _action_confirm(self):
        transit_location = self.env['stock.location'].search([
            ('name', '=', 'Temporary Transit'),
            ('usage', '=', 'transit'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        if not transit_location:
            transit_location = self.env['stock.location'].search([
                ('usage', '=', 'transit'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)

        if not transit_location:
            raise UserError("Temporary Transit location not found.")

        for record in self:
            if record.product_id.tracking != 'none' and record.lot_id:
                check_onhand = self.env['stock.quant'].search([('product_id','=',record.product_id.id),('lot_id','=',record.lot_id.id),('location_id','=',record.location_id.id)])
            elif record.product_id.tracking != 'none' and not record.lot_id:
                check_onhand = self.env['stock.quant'].search([('product_id', '=', record.product_id.id),('location_id','=',record.location_id.id)])
            else:
                check_onhand = self.env['stock.quant'].search([('product_id', '=', record.product_id.id),('location_id','=',record.location_id.id)])

            onhand_qty = sum(check_onhand.mapped('quantity')) if check_onhand else 0
            if not onhand_qty or onhand_qty < record.quantity:
                raise UserError(_("This %s Product does not have quantity at %s!") % (record.product_id.name, record.location_id.complete_name))
            record.state = 'confirm'
            for rec in record.stock_lines:
                rec.state = record.state
                rec.product_qty = rec.quantity

            # Stock move for main product (Stock Out)
            move_values_main = {
                'name': record.product_id.display_name,
                'product_id': record.product_id.id,
                'product_uom_qty': record.quantity,
                'product_uom': record.product_id.uom_id.id,
                'location_id': record.location_id.id,
                'location_dest_id': transit_location.id,
                'company_id': record.company_id.id,
            }
            stock_move_main = self.env['stock.move'].create(move_values_main)
            stock_move_main._action_confirm()
            stock_move_main.quantity_done = record.quantity

            if stock_move_main.move_line_ids:
                for move_line in stock_move_main.move_line_ids:
                    move_line.lot_id = record.lot_id.id if record.lot_id else False
                    move_line.spare_part_id = record.id
            else:
                self.env['stock.move.line'].create({
                    'move_id': stock_move_main.id,
                    'lot_id': record.lot_id.id if record.lot_id else False,
                    'spare_part_id': record.id,
                    'qty_done': record.quantity,
                    'location_id': record.location_id.id,
                    'location_dest_id': transit_location.id,
                    'product_id': record.product_id.id,
                    'product_uom_id': record.product_id.uom_id.id,
                })
            stock_move_main._action_done()

    def action_add_stock_in(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmation',
            'res_model': 'spare.part.confirm.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('noi_spare_part_management.spare_part_confirm_wizard_form_view').id,
            'target': 'new',
            'context': {
                'default_spare_part_stock_id': self.id,
                'default_is_reverse': True,
            },
        }

    def create_stock_move(self, product, quantity, uom, lot, location_id, is_stock_in,is_parent):
        for record in self:
            transit_location = self.env['stock.location'].search([
                ('usage', '=', 'transit'),
                ('company_id', '=', record.company_id.id)
            ], limit=1)

            if not transit_location:
                raise UserError("Temporary Transit location not found.")

            production_location = self.env['stock.location'].search([
                ('name', '=', 'Spare Production'),
                ('usage', '=', 'production'),
                ('company_id', '=', record.company_id.id)
            ], limit=1)

            if not production_location:
                raise UserError("Spare Production location not found.")

            if not location_id:
                location_id = transit_location


            if is_stock_in:
                if record.state == 'done':
                    location = production_location
                elif record.state == 'confirm':
                    location = transit_location
                else:
                    raise UserError("Please check state!")
                if is_parent:
                    location = production_location

                move_values_in = {
                    'name': product.display_name,
                    'product_id': product.id,
                    'product_uom_qty': quantity,
                    'product_uom': uom.id,
                    'location_id': location.id,
                    'location_dest_id': location_id.id,
                    'company_id': record.company_id.id,
                }
                stock_move = self.env['stock.move'].create(move_values_in)
                stock_move._action_confirm()
                stock_move.quantity_done = quantity

                if stock_move.move_line_ids:
                    for move_line in stock_move.move_line_ids:
                        move_line.lot_id = lot.id if lot else False
                        move_line.spare_part_id = record.id
                else:
                    self.env['stock.move.line'].create({
                        'move_id': stock_move.id,
                        'lot_id': lot.id if lot else False,
                        'spare_part_id': record.id,
                        'qty_done': quantity,
                        'location_id': location.id,
                        'location_dest_id': location_id.id,
                        'product_id': product.id,
                        'product_uom_id': uom.id,
                    })
                stock_move._action_done()
            else:
                location = production_location
                check_onhand = self.env['stock.quant'].search(
                    [('product_id', '=', product.id), ('lot_id', '=', lot.id if lot else False),
                     ('location_id', '=', location_id.id)])
                onhand_qty = sum(check_onhand.mapped('quantity')) if check_onhand else 0
                if not onhand_qty or onhand_qty < quantity:
                    raise UserError(_("This %s Product does not have quantity at %s!") % (
                        product.name, location_id.complete_name))

                move_values_out = {
                    'name': product.display_name,
                    'product_id': product.id,
                    'product_uom_qty': quantity,
                    'product_uom': uom.id,
                    'location_id': location_id.id,
                    'location_dest_id': location.id,
                    'company_id': record.company_id.id,
                }
                stock_move = self.env['stock.move'].create(move_values_out)
                stock_move._action_confirm()
                stock_move.quantity_done = quantity

                if stock_move.move_line_ids:
                    for move_line in stock_move.move_line_ids:
                        move_line.lot_id = lot.id if lot else False
                        move_line.spare_part_id = record.id
                else:
                    self.env['stock.move.line'].create({
                        'move_id': stock_move.id,
                        'lot_id': lot.id if lot else False,
                        'spare_part_id': record.id,
                        'qty_done': quantity,
                        'location_id': location_id.id,
                        'location_dest_id': location.id,
                        'product_id': product.id,
                        'product_uom_id': uom.id,
                    })
                stock_move._action_done()
        return stock_move

    def _action_add_stock_in(self):
        for record in self:
            if not record.stock_in_lines:
                raise UserError(_("There is no line to show in!"))

            stock_line = record.stock_lines.filtered(lambda l: l.state in ('done', 'progress'))
            draft_stock_line = record.stock_lines.filtered(lambda l: l.state not in ('done', 'progress'))

            for draft_line in draft_stock_line:
                draft_in_lines = record.stock_in_lines.filtered(lambda l: l.spare_part_line_id.id == draft_line.id)
                if draft_in_lines:
                    raise UserError(_("%s must not have in stock in!") % draft_line.product_id.name)

            if not stock_line:
                raise UserError(_("There is no line to stock in!"))

            check_stock_line = stock_line.filtered(lambda l: l.state == 'done')

            for line in check_stock_line:
                in_lines = record.stock_in_lines.filtered(lambda l: l.spare_part_line_id.id == line.id)
                if not in_lines or len(in_lines) > 1:
                    raise UserError(_("%s must have one valid line!") % line.product_id.name)

                if in_lines.quantity != line.quantity_done:
                    raise UserError(_("%s qty must be same!") % line.product_id.name)

                move = record.create_stock_move(line.product_id, line.quantity_done, line.uom_id, line.lot_id,
                                                in_lines.location_id, False,False)
                # record._update_valuation_cost(move, in_lines, False, True,False)

            transit_move = record.create_stock_move(record.product_id, record.quantity, record.uom_id, record.lot_id,
                                                    False, False,True)
            record._update_valuation_cost(transit_move, record, True, False,True)
            main_move = record.create_stock_move(record.product_id, record.quantity, record.uom_id, record.lot_id,
                                                 record.location_id, True,True)
            record._update_valuation_cost(main_move, record, True, True,False)
            record.state = 'reverse'

    def action_reset_to_draft(self):
        stock_line =  self.stock_lines.filtered(lambda l: l.state  == 'done') if self.stock_lines else False
        if stock_line:
            raise UserError(_("This product has stock out. Click 'Backspace' to add a new stock in record."))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmation',
            'res_model': 'spare.part.confirm.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('noi_spare_part_management.spare_part_confirm_wizard_form_view').id,
            'target': 'new',
            'context': {
                'default_spare_part_stock_id': self.id,
                'default_is_return': True,
                'default_is_confirm': False,
            },
        }

    def action_move_lines(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Move Lines',
            'res_model': 'stock.move.line',
            'view_mode': 'tree',
            'domain': [('spare_part_id', '=', self.id)],
            'target': 'current',
        }

    def action_return(self):
        transit_location = self.env['stock.location'].search([
            ('name', '=', 'Temporary Transit'),
            ('usage', '=', 'transit'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        if not transit_location:
            transit_location = self.env['stock.location'].search([
                ('usage', '=', 'transit'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)

        if not transit_location:
            raise UserError("Temporary Transit location not found.")
        for record in self:
            if record.stock_lines:
                for line in record.stock_lines:
                    if line.state == 'done':
                        raise UserError("There's already progress.")
            record.state = 'draft'
            record.stock_lines.write({'state': 'draft'})

            move_values_main = {
                'name': record.product_id.display_name,
                'product_id': record.product_id.id,
                'product_uom_qty': record.quantity,
                'product_uom': record.product_id.uom_id.id,
                'location_dest_id': record.location_id.id,
                'location_id': transit_location.id,
                'company_id': record.company_id.id,
            }
            stock_move_main = self.env['stock.move'].create(move_values_main)
            stock_move_main._action_confirm()
            stock_move_main.quantity_done = record.quantity

            if stock_move_main.move_line_ids:
                for move_line in stock_move_main.move_line_ids:
                    move_line.lot_id = record.lot_id.id if record.lot_id else False
                    move_line.spare_part_id = record.id
            else:
                self.env['stock.move.line'].create({
                    'move_id': stock_move_main.id,
                    'lot_id': record.lot_id.id if record.lot_id else False,
                    'spare_part_id': record.id,
                    'qty_done': record.quantity,
                    'location_id': record.location_id.id,
                    'location_dest_id': transit_location.id,
                    'product_id': record.product_id.id,
                    'product_uom_id': record.product_id.uom_id.id,
                })
            stock_move_main._action_done()

class SparePartStockLine(models.Model):
    _name = 'spare.part.stock.line'
    _description = 'Spare Part Stock Line'
    _rec_name = 'product_id'

    stock_id = fields.Many2one('spare.part.stock', string='Stock')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    origin_quantity = fields.Float(string='Origin Quantity', required=True, default=1.0)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    quantity_done = fields.Float(string='Done Qty', required=True, default=0.0)
    product_qty = fields.Float(string='Produce Qty', required=True, default=1.0)
    uom_id = fields.Many2one('uom.uom',related='product_id.uom_id')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,related='stock_id.company_id')
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number',
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]")
    location_id = fields.Many2one('stock.location', string='From',related='stock_id.location_id',store=True)
    to_location_id = fields.Many2one(
        'stock.location',
        string='To',
        domain="[('usage', '=', 'internal'), ('company_id', '=', company_id)]"
    )
    movement_type = fields.Selection([
        ('in', 'In'),
        ('out', 'Out')
    ], string='Movement Type', required=True, default='out')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirm', 'Confirm'),
         ('progress', 'Progress'),
         ('done', 'Done'),
         ('cancel', 'Cancel'),
         ], string='Status', readonly=True, index=True, copy=False, default='draft',
        tracking=True)
    cost = fields.Float(string='Cost')
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost', store=True)
    product_cost = fields.Float(string='Produce Cost', compute='_compute_produce_cost', store=True)
    done_cost = fields.Float(string='Done Cost', compute='_compute_done_cost', store=True)


    @api.depends('quantity', 'cost')
    def _compute_total_cost(self):
        for line in self:
            line.total_cost = line.quantity * line.cost

    @api.depends('product_qty', 'cost')
    def _compute_produce_cost(self):
        for line in self:
            line.product_cost = line.product_qty * line.cost

    @api.depends('quantity_done', 'cost')
    def _compute_done_cost(self):
        for line in self:
            line.done_cost = line.quantity_done * line.cost

    @api.onchange('quantity')
    def change_done_qty(self):
        self.product_qty = self.quantity


    def action_done(self):
        for rec in self:
            if not self.to_location_id:
                raise UserError("Please add Location!")
            if self.quantity < self.product_qty + self.quantity_done:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Confirmation Over Qty Limit',
                    'res_model': 'spare.part.confirm.wizard',
                    'view_mode': 'form',
                    'view_id': self.env.ref('noi_spare_part_management.spare_part_confirm_wizard_form_view').id,
                    'target': 'new',
                    'context': {
                        'default_spare_part_stock_line_id': self.id,
                        'default_is_return': False,
                        'default_is_confirm': True,
                    },
                }
            else:

                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Confirmation',
                    'res_model': 'spare.part.confirm.wizard',
                    'view_mode': 'form',
                    'view_id': self.env.ref('noi_spare_part_management.spare_part_confirm_wizard_form_view').id,
                    'target': 'new',
                    'context': {
                        'default_spare_part_stock_line_id': self.id,
                        'default_is_return': False,
                        'default_is_confirm': True,
                    },
                }

    def _update_valuation_cost(self,move,stock_line,is_add):
        valuation = self.env['stock.valuation.layer'].sudo().search([('stock_move_id', '=', move.id)])
        if valuation:
            remaining_qty = valuation.remaining_qty
            valuation.account_move_id.button_draft()
            valuation.account_move_id.unlink()
            valuation.sudo().unlink()
            # if self.product_tmpl_id.cost_method == 'fifo':
            #     vals.update(fifo_vals)
            valuation_layer = self.env['stock.valuation.layer'].sudo().create({
                'value': (move.quantity_done * stock_line.cost) if is_add else (-move.quantity_done * stock_line.cost),
                'unit_cost': stock_line.cost,
                'quantity': move.quantity_done if is_add else -move.quantity_done,
                'description': move.reference and '%s - %s' % (move.reference, move.product_id.name) or move.product_id.name,
                'stock_move_id': move.id,
                'product_id': stock_line.product_id.id,
                'company_id': stock_line.company_id.id,
                'remaining_qty': remaining_qty if is_add else 0,
                'remaining_value': (move.quantity_done * stock_line.cost) if is_add else 0,
                })
            move.product_price_update_before_done()
            # if is_add:
            #     move.product_id.sudo().write({'standard_price': valuation_layer.unit_cost})
            valuation_layer._validate_accounting_entries()
            valuation_layer._validate_analytic_accounting_entries()

            valuation_layer._check_company()

            # For every in move, run the vacuum for the linked product.
            products_to_vacuum = move.mapped('product_id')
            company = move.mapped('company_id') and move.mapped('company_id')[
                0] or self.env.company
            products_to_vacuum._run_fifo_vacuum(company)
            if valuation_layer.product_id.standard_price == 0 and is_add:
                valuation_layer.product_id.standard_price = stock_line.cost
            return True

    def _action_done(self):
        for rec in self:
            if not self.to_location_id:
                raise UserError("Please add Location!")

            # Ensure product_qty is valid for processing
            if rec.product_qty == 0:
                pass

            # Stock move for main product (Stock Out)

            move = rec.stock_id.create_stock_move(rec.product_id, rec.product_qty, rec.uom_id, rec.lot_id,
                                                rec.to_location_id, True,True)
            rec._update_valuation_cost(move, rec, True)
            # **Fixing the State and Quantity Update Logic**
            rec.quantity_done += rec.product_qty  # Add processed quantity
            remaining_qty = rec.quantity - rec.quantity_done  # Calculate remaining qty

            if remaining_qty <= 0:
                rec.state = 'done'
                rec.product_qty = 0
            else:
                rec.state = 'progress'
                rec.product_qty = remaining_qty  # Update product_qty for next processing

            all_line_done = rec.stock_id.stock_lines.filtered(lambda l: l.state  == 'done')
            if all_line_done and len(all_line_done) == len(rec.stock_id.stock_lines) and rec.stock_id.state != 'done':

                transit_move = rec.stock_id.create_stock_move(rec.stock_id.product_id, rec.stock_id.quantity, rec.stock_id.uom_id,
                                                        rec.stock_id.lot_id,
                                                        False, False, True)

                rec.stock_id._update_valuation_cost(transit_move, rec.stock_id, True, True,True)
                main_move = rec.stock_id.create_stock_move(rec.stock_id.product_id, rec.stock_id.quantity, rec.stock_id.uom_id,
                                                        rec.stock_id.lot_id, rec.stock_id.location_id, True, True)

                # Finalize the state of the main record
                rec.stock_id.state = 'done'

    def action_return(self):
        if self.state in ('reverse', 'done'):
            raise UserError("You cannot return!")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmation',
            'res_model': 'spare.part.confirm.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('noi_spare_part_management.spare_part_confirm_wizard_form_view').id,
            'target': 'new',
            'context': {
                'default_spare_part_stock_line_id': self.id,
                'default_is_return': True,
                'default_is_confirm': False,
            },
        }

    def _action_return(self):
        for record in self:

            production_location = self.env['stock.location'].search([
                ('name', '=', 'Spare Production'),
                ('usage', '=', 'production'),
                ('company_id', '=', record.company_id.id)
            ], limit=1)
            if not production_location:
                production_location = self.env['stock.location'].search([
                    ('usage', '=', 'production'),
                    ('company_id', '=', record.company_id.id)
                ], limit=1)

            if not production_location:
                raise UserError("Spare Production location not found.")
            record.state = record.stock_id.state
            if record.product_id.tracking != 'none' and record.lot_id:
                check_onhand = self.env['stock.quant'].search([('product_id','=',record.product_id.id),('lot_id','=',record.lot_id.id),('location_id','=',record.location_id.id)])
            elif record.product_id.tracking != 'none' and not record.lot_id:
                check_onhand = self.env['stock.quant'].search([('product_id', '=', record.product_id.id),('location_id','=',record.to_location_id.id)])
            else:
                check_onhand = self.env['stock.quant'].search([('product_id', '=', record.product_id.id),('location_id','=',record.to_location_id.id)])
            onhand_qty = sum(check_onhand.mapped('quantity')) if check_onhand else 0
            if not onhand_qty or onhand_qty < record.quantity_done:
                raise UserError(_("This %s Product does not have quantity at %s!") % (record.product_id.name, record.to_location_id.complete_name))


            move_values_main = {
                'name': record.product_id.display_name,
                'product_id': record.product_id.id,
                'product_uom_qty': record.quantity_done,
                'product_uom': record.product_id.uom_id.id,
                'location_dest_id': production_location.id,
                'location_id': record.to_location_id.id,
                'company_id': record.company_id.id,
            }
            stock_move_main = self.env['stock.move'].create(move_values_main)
            stock_move_main._action_confirm()
            stock_move_main.quantity_done = record.quantity_done


            if stock_move_main.move_line_ids:
                for move_line in stock_move_main.move_line_ids:
                    move_line.lot_id = record.lot_id.id if record.stock_id else False
                    move_line.spare_part_id = record.stock_id.id if record.stock_id else False
            else:
                self.env['stock.move.line'].create({
                    'move_id': stock_move_main.id,
                    'lot_id': record.lot_id.id if record.lot_id else False,
                    'spare_part_id': record.stock_id.id if record.stock_id else False,
                    'qty_done': record.quantity_done,
                    'location_id': record.location_id.id,
                    'location_dest_id': production_location.id,
                    'product_id': record.product_id.id,
                    'product_uom_id': record.product_id.uom_id.id,
                })
            stock_move_main._action_done()
            record._update_valuation_cost(stock_move_main,record,False)

class SparePartStockIn(models.Model):
    _name = 'spare.part.stock.in'
    _description = 'Spare Part Stock In'
    _rec_name = 'product_id'

    stock_id = fields.Many2one('spare.part.stock', string='Stock')
    spare_part_line_id = fields.Many2one('spare.part.stock.line', string='Spare Part Line', domain="[('stock_id', '=', stock_id)]")
    product_id = fields.Many2one('product.product', string='Product', related='spare_part_line_id.product_id', store=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    uom_id = fields.Many2one('uom.uom', related='spare_part_line_id.uom_id')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company, related='stock_id.company_id')
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number',
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]")
    location_id = fields.Many2one(
        'stock.location',
        string='From',
        domain="[('usage', '=', 'internal'), ('company_id', '=', company_id)]",
        required=True
    )
    state = fields.Selection(
        [('confirm', 'Confirm'),
         ('done', 'Done'),
         ('cancel', 'Cancel'),
         ], string='Status', readonly=True, index=True, copy=False, default='confirm',
        tracking=True)
    cost = fields.Float(string='Cost')
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost', store=True)


    @api.onchange('spare_part_line_id')
    def _onchange_spare_part_line_id(self):
        if self.spare_part_line_id:
            self.product_id = self.spare_part_line_id.product_id
            self.uom_id = self.spare_part_line_id.uom_id
            self.cost = self.spare_part_line_id.product_id.standard_price

    @api.depends('quantity', 'cost')
    def _compute_total_cost(self):
        for line in self:
            line.total_cost = line.quantity * line.cost
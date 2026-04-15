from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Reparation(models.Model):
    _name = 'mecanicien.reparation'
    _description = 'Réparation'

    STATE_SELECTION = [
        ('draft', 'Brouillon'),
        ('in_progress', 'En cours'),
        ('done', 'Terminé'),
    ]

    name = fields.Char(string='Référence', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    description = fields.Text(string='Description')
    mecanicien_id = fields.Many2one(
        comodel_name='mecanicien.mecanicien',
        string='Mécanicien',
        required=True,
    )
    voiture_id = fields.Many2one(
        comodel_name='mecanicien.voiture',
        string='Voiture',
        required=True,
    )
    state = fields.Selection(
        selection=STATE_SELECTION,
        string='Statut',
        default='draft',
        required=True,
    )

    @api.constrains('mecanicien_id', 'voiture_id')
    def _check_mecanicien_and_voiture(self):
        for record in self:
            if not record.mecanicien_id or not record.voiture_id:
                raise ValidationError(
                    'Une réparation doit être liée à un mécanicien et à une voiture.'
                )
            if record.voiture_id.mecanicien_id and record.voiture_id.mecanicien_id != record.mecanicien_id:
                raise ValidationError(
                    'La voiture sélectionnée est affectée à un autre mécanicien.'
                )

    def action_start(self):
        for record in self:
            if record.state == 'draft':
                record.state = 'in_progress'

    def action_done(self):
        for record in self:
            if record.state in ('draft', 'in_progress'):
                record.state = 'done'

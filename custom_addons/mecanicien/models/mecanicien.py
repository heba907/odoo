from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Mecanicien(models.Model):
    _name = 'mecanicien.mecanicien'
    _description = 'Mécanicien'

    name = fields.Char(string='Nom', required=True)
    specialite = fields.Char(string='Spécialité')
    telephone = fields.Char(string='Téléphone')
    reparation_ids = fields.One2many(
        comodel_name='mecanicien.reparation',
        inverse_name='mecanicien_id',
        string='Réparations',
    )


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_mecanicien = fields.Boolean(string='Est mécanicien', default=False)
    specialite = fields.Char(string='Spécialité')

    @api.constrains('is_mecanicien', 'specialite')
    def _check_specialite_for_mecanicien(self):
        for record in self:
            if not record.is_mecanicien and record.specialite:
                raise ValidationError(
                    "La spécialité doit être vide si l'employé n'est pas mécanicien."
                )

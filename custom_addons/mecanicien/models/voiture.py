from odoo import fields, models


class Voiture(models.Model):
    _name = 'mecanicien.voiture'
    _description = 'Voiture'

    name = fields.Char(string='Nom', required=True)
    marque = fields.Char(string='Marque')
    modele = fields.Char(string='Modèle')
    mecanicien_id = fields.Many2one(
        comodel_name='mecanicien.mecanicien',
        string='Mécanicien',
    )
    reparation_ids = fields.One2many(
        comodel_name='mecanicien.reparation',
        inverse_name='voiture_id',
        string='Réparations',
    )

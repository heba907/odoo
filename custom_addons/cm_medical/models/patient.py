from odoo import models, fields, api
from datetime import date


class CmPatient(models.Model):
    _name = 'cm.patient'
    _description = 'Patient'
    _order = "name asc, age desc"

    name = fields.Char('Nom', required=True)
    patient_ref = fields.Char('Référence patient')
    date_of_birth = fields.Date(string="Date de naissance")
    gender = fields.Selection([
        ('male', 'Homme'),
        ('female', 'Femme'),
        ('other', 'Autre')
    ], string='Sexe')
    phone = fields.Char('Téléphone')
    email = fields.Char('Email')
    active = fields.Boolean('Actif', default=True)
    age = fields.Integer(string="Âge", compute="_compute_age", store=True)
    display_name = fields.Char(string="Nom affiché", compute="_compute_display_name", store=True)

    @api.depends('date_of_birth')
    def _compute_age(self):
            today = date.today()
            for rec in self:
                if rec.date_of_birth:
                    rec.age = today.year - rec.date_of_birth.year
                else:
                    rec.age = 0
    @api.depends('name', 'age', 'patient_ref', 'date_of_birth')
    def _compute_display_name(self):
        for rec in self:
            parts = []

            parts.append(rec.name or "")

            if rec.date_of_birth:
                parts.append(f"({rec.age})")

            if rec.patient_ref:
                parts.append(f"- {rec.patient_ref}")

            rec.display_name = " ".join(parts).strip()
            
    def name_get(self):
        result = []
        for rec in self:
            label = rec.display_name or rec.name or ""
            result.append((rec.id, label))
        return result

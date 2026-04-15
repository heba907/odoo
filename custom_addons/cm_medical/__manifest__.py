{
    'name': 'Cabinet Médical',
    'version': '1.0',
    'summary': 'Gestion des patients du cabinet médical',
    'description': 'Module Odoo pour gérer les patients (nom, sexe, contact, etc.)',
    'author': 'Ton Nom',
    'website': 'https://exemple.com',
    'category': 'Healthcare',
    'depends': ['base', 'contacts'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/patient_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}

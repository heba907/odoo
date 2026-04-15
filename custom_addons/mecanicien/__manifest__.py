{
    'name': 'Mécanicien',
    'version': '1.0',
    'summary': 'Gestion des mécaniciens, voitures et réparations',
    'description': 'Module de gestion d atelier pour les mécaniciens, les voitures et les réparations.',
    'author': 'Auto Generated',
    'website': 'https://example.com',
    'category': 'Services',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/mecanicien_views.xml',
        'views/voiture_views.xml',
        'views/reparation_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}

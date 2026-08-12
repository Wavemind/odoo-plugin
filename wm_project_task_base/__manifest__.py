# -*- coding: utf-8 -*-
{
    'name': 'WM Project Task Base',
    'version': '19.0.1.0.0',
    'summary': "Champs métier Wavemind sur les tâches — survit aux montées de version",
    'description': """
Module technique volontairement minimal.

Il ne porte que les champs métier réellement déployés en production :
  * task_type      : typage bug / feature / question
  * priority       : extension de l'échelle standard (0-1) à 0-3

Toute la couche portail (templates QWeb, JS, contrôleurs) a été retirée :
elle est refaite à neuf sur Odoo 19. Garder ces champs dans un module
séparé évite de perdre les données à chaque montée de version.
""",
    'author': 'Wavemind',
    'license': 'LGPL-3',
    'category': 'Project',
    'depends': ['project'],
    'installable': True,
    'application': False,
}

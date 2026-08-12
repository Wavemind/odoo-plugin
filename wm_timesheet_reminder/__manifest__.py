# -*- coding: utf-8 -*-
{
    'name': 'WM Timesheet Reminder',
    'version': '19.0.1.0.0',
    'summary': "Rappel hebdomadaire aux employés qui n'ont pas saisi leurs heures",
    'description': """
Envoie chaque lundi matin un rappel aux employés dont le total d'heures saisies
sur la semaine écoulée est inférieur au seuil attendu.

Le mail liste les tâches ouvertes qui leur sont assignées, pour qu'il soit
directement actionnable plutôt que culpabilisant.

Les congés sont exclus du calcul : ils sont enregistrés automatiquement et ne
doivent pas masquer une absence de saisie.

Paramètres (Configuration > Technique > Paramètres système) :
  * wm_timesheet_reminder.min_hours       seuil hebdomadaire, défaut 20
  * wm_timesheet_reminder.excluded_projects  ids de projets exclus, séparés par des virgules
""",
    'author': 'Wavemind',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': ['hr_timesheet', 'project'],
    'data': [
        'data/mail_template.xml',
        'data/ir_cron.xml',
        'data/ir_config_parameter.xml',
    ],
    'installable': True,
    'application': False,
}

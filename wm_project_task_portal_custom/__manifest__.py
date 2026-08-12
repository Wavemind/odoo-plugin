# -*- coding: utf-8 -*-
{
    'name': 'Project Task Portal Custom',
    'version': '17.0.1.0.0',
    'summary': 'Formulaire portail de création de tâches avec éditeur Odoo',
    'author': 'Toi',
    'license': 'LGPL-3',
    'category': 'Project',
    'depends': [
        'portal',
        'project',
        'sale',
        'account',
        'web',
        'web_editor',
        'base_setup',
        'l10n_din5008',
    ],
    'data': [
        'views/portal_task_templates.xml',   # le formulaire QWeb
        'views/portal_tasks_list_kanban.xml',
        'views/portal_templates.xml',       # bouton/carte sur /my/home
        'views/project_task_views.xml',      # si tu as une vue backend
        'views/portal_my_tasks_kanban_switch.xml',  # switch entre vue liste et kanban
        'views/external_layout_override.xml',  # override du layout DIN5008
        'security/ir.model.access.csv',
        'security/project_task_security.xml',
        'security/wm_portal_rules.xml',
    ],
   'assets': {
        'web.assets_frontend': [
            # Inherit and include Odoo's built-in WYSIWYG editor
            'web_editor.assets_wysiwyg',
            # Optional: Also include editor styling and extra behavior
            'web_editor.assets_editor',
            'wm_project_task_portal_custom/static/src/css/view_switch.css',
            'wm_project_task_portal_custom/static/src/js/task_wysiwyg.js',
            'wm_project_task_portal_custom/static/src/js/kanban_scroll.js',
        ],
    },
    'installable': True,
    'application': False,
}

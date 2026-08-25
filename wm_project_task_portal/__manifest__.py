# -*- coding: utf-8 -*-
{
    'name': 'WM Project Task Portal',
    'version': '19.0.1.0.0',
    'summary': "Couche portail Wavemind : type de tâche, filtre « en cours », groupement",
    'description': """
Couche mince au-dessus du portail standard d'Odoo 19.

Le portail natif et le partage de projet (Project Sharing) couvrent déjà
l'essentiel : le client voit les tâches de ses projets, les crée, les modifie,
commente et dépose des documents. Ce module ne comble que les écarts réels :

  * ``task_type`` (bug / feature / question) est un champ Wavemind : il est
    absent de la liste blanche portail d'Odoo, donc invisible et non modifiable
    côté client. On l'ouvre explicitement, en lecture et en écriture.
  * Le portail ne propose aucun filtre « en cours / terminées » — seulement
    « tout » et un filtre par projet. On les ajoute, et « en cours » devient le
    filtre par défaut.
  * Le type de tâche est ajouté aux vues de partage (formulaire et liste), à la
    fiche portail et aux groupements disponibles.

Aucun contrôleur n'est réécrit, aucun gabarit n'est remplacé : uniquement des
héritages. C'est délibéré — la couche portail de la v17 avait été perdue à la
migration parce qu'elle redéfinissait tout.
""",
    'author': 'Wavemind',
    'license': 'LGPL-3',
    'category': 'Project',
    'depends': ['project', 'wm_project_task_base'],
    'data': [
        'views/project_sharing_views.xml',
        'views/portal_templates.xml',
        'views/project_sharing_portal.xml',
        'views/portal_kanban_templates.xml',
        'views/portal_shell_templates.xml',
    ],
    'assets': {
        # wm_brand.scss vient EN PREMIER dans chaque bundle : il porte les
        # @font-face et les variables (couleurs, rayons, police) que les
        # feuilles suivantes consomment.
        #
        # Bundle servi uniquement par /my/projects/<id>/project_sharing.
        'project.webclient': [
            'wm_project_task_portal/static/src/scss/wm_brand.scss',
            'wm_project_task_portal/static/src/scss/project_sharing_portal.scss',
        ],
        # Bundle du portail : /my/tasks, la connexion et le reste de /my.
        'web.assets_frontend': [
            'wm_project_task_portal/static/src/scss/wm_brand.scss',
            'wm_project_task_portal/static/src/scss/portal_shell.scss',
            'wm_project_task_portal/static/src/scss/portal_kanban.scss',
            'wm_project_task_portal/static/src/js/portal_kanban.js',
        ],
    },
    'installable': True,
    'application': False,
}

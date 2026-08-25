# -*- coding: utf-8 -*-
from odoo import models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # Odoo 19 filtre les champs accessibles au portail par liste blanche
    # (cf. project/models/project_task.py, PROJECT_TASK_READABLE_FIELDS et
    # PROJECT_TASK_WRITABLE_FIELDS). Un champ ajouté par un module tiers en est
    # absent : il est donc invisible ET non modifiable depuis le portail, même
    # avec le partage de projet actif. Odoo expose ces deux listes en propriétés
    # précisément pour qu'on puisse les étendre.
    #
    # `priority` est déjà dans la liste standard : notre échelle étendue 0-3
    # fonctionne sans rien ajouter.

    @property
    def TASK_PORTAL_READABLE_FIELDS(self):
        return super().TASK_PORTAL_READABLE_FIELDS | {'task_type'}

    @property
    def TASK_PORTAL_WRITABLE_FIELDS(self):
        return super().TASK_PORTAL_WRITABLE_FIELDS | {'task_type'}

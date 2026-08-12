# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    task_type = fields.Selection(
        [('bug', 'Bug'), ('feature', 'Feature'), ('question', 'Question')],
        string="Type de tâche", required=True, default='question',
    )

    # Odoo ne connaît que 0 et 1 : on étend l'échelle sans casser l'existant.
    # 117 tâches portaient déjà les valeurs 2 et 3 au moment de la migration.
    priority = fields.Selection(
        selection_add=[
            ('0', 'Faible'),
            ('1', 'Normale'),
            ('2', 'Haute'),
            ('3', 'Très haute'),
        ],
        default='1', required=True,
        ondelete={'0': 'set default', '1': 'set default',
                  '2': 'set default', '3': 'set default'},
    )

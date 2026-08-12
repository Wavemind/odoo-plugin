from odoo import models, fields


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    is_awaiting_validation = fields.Boolean(
        string="Attente validation client",
        default=False,
        help="Si activé, les tâches dans ce stage affichent le bouton de validation côté portail client.",
    )

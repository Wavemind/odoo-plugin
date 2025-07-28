from odoo import api, models, fields

class ProjectTask(models.Model):
    _inherit = 'project.task'

    task_type = fields.Selection(
        [('bug', 'Bug'), ('feature', 'Feature'), ('question', 'Question')],
        string='Type de tâche', required=True, default='question'
    )

    # Le champ priority existe déjà dans Odoo, on ajoute juste des attributs
    priority = fields.Selection(selection_add=[
        ('0', 'Faible'),
        ('1', 'Normale'),
        ('2', 'Haute'),
        ('3', 'Très haute')
    ], default='1', required=True, help="Priorité de la tâche", ondelete={'0': 'set default', '1': 'set default', '2': 'set default', '3': 'set default'})

    @api.model_create_multi
    def create(self, vals_list):
        # On prépare les valeurs pour chaque enregistrement
        if self.env.user.has_group('base.group_portal'):
            for vals in vals_list:
                vals.setdefault('partner_id', self.env.user.partner_id.id)
                # Définir une priorité par défaut pour les utilisateurs portail
                vals.setdefault('priority', '0')

        records = super().create(vals_list)

        # Exemple: auto-subscribe le client après création
        # (facultatif, mais à faire après le super pour avoir les IDs)
        if self.env.user.has_group('base.group_portal'):
            records.message_subscribe(partner_ids=[self.env.user.partner_id.id])

        return records

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

    # Story 1.1 — Liens financiers
    sale_order_line_ids = fields.Many2many(
        'sale.order.line',
        'wm_task_sale_line_rel',
        'task_id', 'sale_line_id',
        string="Lignes de devis",
        ondelete='restrict',
    )

    invoice_line_ids = fields.Many2many(
        'account.move.line',
        'wm_task_invoice_line_rel',
        'task_id', 'invoice_line_id',
        string="Lignes de facture",
        ondelete='restrict',
    )

    financial_status = fields.Selection(
        [
            ('not_quoted', 'Non devisé'),
            ('quoted', 'Devisé'),
            ('invoiced', 'Facturé'),
            ('paid', 'Payé'),
            ('cancelled', 'Facture annulée'),
        ],
        string="Statut financier",
        compute='_compute_financial_status',
        store=False,
    )

    @api.depends(
        'sale_order_line_ids',
        'invoice_line_ids',
        'invoice_line_ids.move_id.payment_state',
        'invoice_line_ids.move_id.state',
    )
    def _compute_financial_status(self):
        for task in self:
            # Only consider posted or cancelled invoice lines; drafts are ignored
            active_inv_lines = task.invoice_line_ids.filtered(
                lambda l: l.move_id.state in ('posted', 'cancel')
            )
            if not active_inv_lines and not task.sale_order_line_ids:
                task.financial_status = 'not_quoted'
            elif not active_inv_lines:
                task.financial_status = 'quoted'
            else:
                moves = active_inv_lines.mapped('move_id')
                if any(m.state == 'cancel' for m in moves):
                    task.financial_status = 'cancelled'
                elif all(m.payment_state == 'paid' for m in moves):
                    task.financial_status = 'paid'
                else:
                    task.financial_status = 'invoiced'

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

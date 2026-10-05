# -*- coding: utf-8 -*-
import re
import secrets

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Ce qui peut figurer dans l'URL : lettres, chiffres, tiret, souligné.
TICKET_SLUG_RE = re.compile(r'^[A-Za-z0-9_-]{4,64}$')


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # Formulaire public de dépôt de ticket : une URL non listée, sans connexion,
    # qui crée la tâche dans CE projet. L'identifiant est le seul secret : le
    # vider coupe l'URL (404), le changer invalide l'ancienne. Il est généré au
    # hasard, mais reste modifiable pour obtenir un lien lisible
    # (/ticket/gesa-alto) — au prix d'une URL plus facile à deviner.
    wm_public_ticket_token = fields.Char(
        string="Identifiant du lien public", copy=False,
        groups='project.group_project_manager',
    )
    wm_public_ticket_url = fields.Char(
        string="Formulaire public de ticket",
        compute='_compute_wm_public_ticket_url',
        groups='project.group_project_manager',
    )

    @api.depends('wm_public_ticket_token')
    def _compute_wm_public_ticket_url(self):
        for project in self:
            token = project.wm_public_ticket_token
            project.wm_public_ticket_url = (
                '%s/ticket/%s' % (project.get_base_url(), token) if token else False)

    @api.constrains('wm_public_ticket_token')
    def _check_wm_public_ticket_token(self):
        for project in self:
            token = project.wm_public_ticket_token
            if not token:
                continue
            if not TICKET_SLUG_RE.match(token):
                raise ValidationError(_(
                    "L'identifiant du lien public doit compter 4 à 64 caractères : "
                    "lettres sans accent, chiffres, tiret ou souligné."))
            # Recherche archives comprises : deux projets ne doivent jamais
            # partager une URL, même si l'un des deux est archivé.
            if self.with_context(active_test=False).search_count([
                ('wm_public_ticket_token', '=', token), ('id', '!=', project.id),
            ]):
                raise ValidationError(_("Cet identifiant de lien public est déjà utilisé par un autre projet."))

    def action_wm_public_ticket_enable(self):
        for project in self:
            project.wm_public_ticket_token = secrets.token_urlsafe(24)

    def action_wm_public_ticket_disable(self):
        self.wm_public_ticket_token = False

# -*- coding: utf-8 -*-
import secrets

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # Formulaire public de dépôt de ticket : une URL non listée, sans connexion,
    # qui crée la tâche dans CE projet. Le jeton est le seul secret : le vider
    # coupe l'URL (404), en générer un nouveau invalide l'ancienne.
    wm_public_ticket_token = fields.Char(
        string="Jeton du formulaire public", copy=False, readonly=True,
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

    def action_wm_public_ticket_enable(self):
        for project in self:
            project.wm_public_ticket_token = secrets.token_urlsafe(24)

    def action_wm_public_ticket_disable(self):
        self.wm_public_ticket_token = False

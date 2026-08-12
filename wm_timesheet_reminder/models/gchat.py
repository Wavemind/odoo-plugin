# -*- coding: utf-8 -*-
"""Envoi du rappel dans un espace Google Chat via webhook entrant.

Le webhook est le moyen le plus simple : une URL par espace, un POST JSON,
aucune authentification OAuth ni application à faire valider.

Pour l'obtenir : ouvrir l'espace Google Chat, menu du nom de l'espace >
Applications et intégrations > Webhooks > Ajouter un webhook. Copier l'URL
dans le paramètre système `wm_timesheet_reminder.gchat_webhook`.

Un message privé à chaque personne exigerait au contraire une application Chat,
un projet Google Cloud, un compte de service et une délégation à l'échelle du
domaine — hors de proportion pour un rappel hebdomadaire.
"""
import json
import logging

import requests

from odoo import api, models

_logger = logging.getLogger(__name__)

PARAM_WEBHOOK = 'wm_timesheet_reminder.gchat_webhook'
TIMEOUT = 10


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def _wm_gchat_webhook(self):
        url = (self.env['ir.config_parameter'].sudo()
               .get_param(PARAM_WEBHOOK, '') or '').strip()
        # garde-fou : on n'envoie que vers un webhook Google Chat
        if url and not url.startswith('https://chat.googleapis.com/'):
            _logger.warning(
                "wm_timesheet_reminder : URL de webhook ignorée, "
                "elle ne pointe pas vers chat.googleapis.com")
            return ''
        return url

    @api.model
    def _wm_gchat_payload(self, retards, start, end, min_hours):
        """Construit le message. Un seul message pour tout le monde :
        plus lisible qu'une rafale de notifications, et la visibilité
        partagée fait plus d'effet qu'un rappel individuel archivable."""
        lignes = []
        for nom, heures in retards:
            manque = round(max(min_hours - heures, 0), 1)
            lignes.append(f"• *{nom}* — {heures:.1f} h saisies, il manque {manque:.1f} h")

        texte = (
            f"*Feuilles de temps — semaine du {start.strftime('%d.%m')} "
            f"au {end.strftime('%d.%m.%Y')}*\n"
            f"_Attendu : {min_hours:.0f} h. Les congés ne sont pas comptés._\n\n"
            + "\n".join(lignes)
            + "\n\n_Objectif : savoir ce que coûtent réellement nos forfaits._"
        )
        return {'text': texte}

    @api.model
    def _wm_gchat_send(self, payload):
        url = self._wm_gchat_webhook()
        if not url:
            return False
        try:
            reponse = requests.post(
                url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json; charset=UTF-8'},
                timeout=TIMEOUT,
            )
            if reponse.status_code != 200:
                _logger.warning(
                    "wm_timesheet_reminder : Google Chat a répondu %s — %s",
                    reponse.status_code, reponse.text[:200])
                return False
            return True
        except requests.RequestException as err:
            # un webhook injoignable ne doit jamais faire échouer le cron
            _logger.warning("wm_timesheet_reminder : envoi Google Chat échoué — %s", err)
            return False

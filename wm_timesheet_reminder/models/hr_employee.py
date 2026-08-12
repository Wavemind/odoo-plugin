# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import _, api, models

PARAM_MIN_HOURS = 'wm_timesheet_reminder.min_hours'
PARAM_EXCLUDED = 'wm_timesheet_reminder.excluded_projects'


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ------------------------------------------------------------------
    # Paramétrage
    # ------------------------------------------------------------------
    @api.model
    def _wm_reminder_settings(self):
        """Seuil hebdomadaire et projets exclus du décompte."""
        params = self.env['ir.config_parameter'].sudo()
        try:
            min_hours = float(params.get_param(PARAM_MIN_HOURS, 20))
        except (TypeError, ValueError):
            min_hours = 20.0
        excluded = []
        for chunk in (params.get_param(PARAM_EXCLUDED, '') or '').split(','):
            chunk = chunk.strip()
            if chunk.isdigit():
                excluded.append(int(chunk))
        return min_hours, excluded

    # ------------------------------------------------------------------
    # Décompte
    # ------------------------------------------------------------------
    @api.model
    def _wm_last_week_bounds(self, today=None):
        """Lundi et dimanche de la semaine écoulée."""
        today = today or date.today()
        monday_this_week = today - timedelta(days=today.weekday())
        start = monday_this_week - timedelta(days=7)
        return start, start + timedelta(days=6)

    def _wm_hours_logged(self, start, end, excluded_projects):
        """Heures saisies sur la période, hors projets exclus (congés)."""
        self.ensure_one()
        domain = [
            ('employee_id', '=', self.id),
            ('date', '>=', start),
            ('date', '<=', end),
            ('project_id', '!=', False),
        ]
        if excluded_projects:
            domain.append(('project_id', 'not in', excluded_projects))
        lines = self.env['account.analytic.line'].sudo().search(domain)
        return sum(lines.mapped('unit_amount'))

    def _wm_open_tasks(self):
        """Tâches ouvertes assignées, pour rendre le rappel actionnable."""
        self.ensure_one()
        if not self.user_id:
            return self.env['project.task']
        return self.env['project.task'].sudo().search([
            ('user_ids', 'in', self.user_id.id),
            ('is_closed', '=', False),
        ], limit=10, order='write_date desc')

    # ------------------------------------------------------------------
    # Point d'entrée du cron
    # ------------------------------------------------------------------
    @api.model
    def _cron_wm_timesheet_reminder(self):
        min_hours, excluded = self._wm_reminder_settings()
        start, end = self._wm_last_week_bounds()

        employees = self.sudo().search([
            ('user_id', '!=', False),
            ('work_email', '!=', False),
        ])

        # qui est en retard, et de combien
        retards = []
        for employee in employees:
            hours = employee._wm_hours_logged(start, end, excluded)
            if hours < min_hours:
                retards.append((employee, hours))

        if not retards:
            return 0

        # Google Chat prioritaire s'il est configuré : un seul message pour
        # l'équipe, plus lisible qu'une rafale de mails individuels.
        if self._wm_gchat_webhook():
            payload = self._wm_gchat_payload(
                [(e.name, h) for e, h in retards], start, end, min_hours)
            if self._wm_gchat_send(payload):
                return len(retards)
            # webhook injoignable : on retombe sur l'e-mail plutôt que
            # de perdre le rappel silencieusement

        template = self.env.ref(
            'wm_timesheet_reminder.mail_template_timesheet_reminder',
            raise_if_not_found=False)
        if not template:
            return 0

        sent = 0
        for employee, hours in retards:
            template.sudo().with_context(
                wm_hours=round(hours, 1),
                wm_min_hours=min_hours,
                wm_missing=round(max(min_hours - hours, 0), 1),
                wm_start=start,
                wm_end=end,
                wm_tasks=employee._wm_open_tasks(),
            ).send_mail(employee.id, force_send=False)
            sent += 1

        if sent:
            self.env['ir.logging'].sudo().create({
                'name': 'wm_timesheet_reminder',
                'type': 'server',
                'level': 'INFO',
                'dbname': self.env.cr.dbname,
                'message': _(
                    'Rappel feuilles de temps : %(sent)s employé(s) relancé(s) '
                    'pour la semaine du %(start)s au %(end)s (seuil %(min)s h).',
                    sent=sent, start=start, end=end, min=min_hours),
                'path': 'wm_timesheet_reminder',
                'func': '_cron_wm_timesheet_reminder',
                'line': '0',
            })
        return sent

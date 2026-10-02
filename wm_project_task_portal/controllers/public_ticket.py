# -*- coding: utf-8 -*-
import base64

from markupsafe import Markup, escape

from odoo import SUPERUSER_ID, _, http
from odoo.http import request
from odoo.tools import email_normalize
from odoo.tools.mail import plaintext2html

# Formulaire ouvert sans connexion : on borne ce qu'un envoi peut déposer.
MAX_ATTACHMENTS = 10
MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024


class WmPublicTicket(http.Controller):
    """Dépôt de ticket sans connexion, par une URL à jeton propre à un projet.

    Le projet n'est JAMAIS lu dans le formulaire : il est déduit du jeton. Une
    personne qui détient le lien ne peut donc écrire que dans ce projet-là, et
    ne peut rien y lire.
    """

    def _wm_project_from_token(self, token):
        # Un jeton vide ne doit jamais correspondre à un projet sans jeton.
        if not token or len(token) < 16:
            raise request.not_found()
        project = request.env['project.project'].sudo().search([
            ('wm_public_ticket_token', '=', token),
            ('active', '=', True),
        ], limit=1)
        if not project:
            raise request.not_found()
        return project

    def _wm_form_values(self, project, token, data=None, error=None):
        Task = request.env['project.task']
        return {
            'token': token,
            'project_name': project.name,
            'task_types': Task._fields['task_type']._description_selection(request.env),
            'priorities': Task._fields['priority']._description_selection(request.env),
            'data': data or {},
            'error': error,
        }

    @http.route('/ticket/<string:token>', type='http', auth='public', website=True,
                methods=['GET'], sitemap=False)
    def wm_public_ticket_form(self, token, **kw):
        project = self._wm_project_from_token(token)
        return request.render(
            'wm_project_task_portal.public_ticket_form',
            self._wm_form_values(project, token))

    @http.route('/ticket/<string:token>', type='http', auth='public', website=True,
                methods=['POST'], sitemap=False)
    def wm_public_ticket_create(self, token, **post):
        project = self._wm_project_from_token(token)
        Task = request.env['project.task']

        def refuser(message):
            return request.render(
                'wm_project_task_portal.public_ticket_form',
                self._wm_form_values(project, token, data=post, error=message))

        # Piège à robots rempli : on répond comme si tout s'était bien passé,
        # sans rien créer.
        if post.get('company_website'):
            return request.redirect('/ticket/%s/merci' % token)

        contact_name = (post.get('contact_name') or '').strip()
        if not contact_name:
            return refuser(_("Votre nom est obligatoire."))
        contact_email = email_normalize(post.get('contact_email') or '')
        if not contact_email:
            return refuser(_("Indiquez une adresse e-mail valide."))
        name = (post.get('name') or '').strip()
        if not name:
            return refuser(_("Le titre est obligatoire."))

        task_type = post.get('task_type') or 'bug'
        if task_type not in dict(Task._fields['task_type']._description_selection(request.env)):
            return refuser(_("Type de tâche inconnu."))
        priority = post.get('priority') or '1'
        if priority not in dict(Task._fields['priority']._description_selection(request.env)):
            return refuser(_("Priorité inconnue."))

        files = [s for s in request.httprequest.files.getlist('attachments')
                 if s and s.filename]
        if len(files) > MAX_ATTACHMENTS:
            return refuser(_("%s pièces jointes au maximum.", MAX_ATTACHMENTS))
        contents = []
        for storage in files:
            content = storage.read(MAX_ATTACHMENT_SIZE + 1)
            if len(content) > MAX_ATTACHMENT_SIZE:
                return refuser(_("« %s » dépasse 25 Mo.", storage.filename))
            contents.append((storage, content))

        # L'origine est écrite dans la description : la tâche est créée par le
        # système, sans cela rien ne dirait qui l'a déposée.
        description = Markup("<p><em>%s</em></p>") % escape(
            _("Déposé par %(name)s <%(email)s> via le formulaire public.",
              name=contact_name, email=contact_email))
        body = (post.get('description') or '').strip()
        if body:
            description += plaintext2html(body)

        # Le visiteur n'a aucun droit sur project.task : la création se fait
        # sous l'identité du système, comme le fait le formulaire du module
        # Site web d'Odoo. Les valeurs sont toutes validées ci-dessus.
        task = Task.with_user(SUPERUSER_ID).with_context(
            mail_create_nosubscribe=True,
            default_project_id=project.id,
        ).create({
            'name': name[:200],
            'task_type': task_type,
            'priority': priority,
            'email_from': '%s <%s>' % (contact_name.replace('<', '').replace('>', ''), contact_email),
            'description': description,
        })

        for storage, content in contents:
            request.env['ir.attachment'].sudo().create({
                'name': storage.filename,
                'datas': base64.b64encode(content),
                'res_model': 'project.task',
                'res_id': task.id,
            })

        return request.redirect('/ticket/%s/merci?ref=%s' % (token, task.id))

    @http.route('/ticket/<string:token>/merci', type='http', auth='public', website=True,
                methods=['GET'], sitemap=False)
    def wm_public_ticket_done(self, token, ref=None, **kw):
        self._wm_project_from_token(token)
        return request.render('wm_project_task_portal.public_ticket_done', {
            'token': token,
            'reference': ref if ref and ref.isdigit() else None,
        })

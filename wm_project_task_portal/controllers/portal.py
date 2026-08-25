# -*- coding: utf-8 -*-
import base64

from odoo import _, http
from odoo.tools.mail import plaintext2html
from odoo.exceptions import AccessError, UserError
from odoo.http import request
from odoo.addons.project.controllers.portal import ProjectCustomerPortal
from odoo.addons.project.models.project_task import CLOSED_STATES

# Le kanban charge toutes les tâches d'un coup (c'est le principe d'un tableau).
# Au-delà de cette borne on tronque et on le dit à l'écran, plutôt que de servir
# une page de plusieurs milliers de cartes.
KANBAN_LIMIT = 500


class WmProjectCustomerPortal(ProjectCustomerPortal):

    # ------------------------------------------------------------------
    # Filtres et groupements
    # ------------------------------------------------------------------

    def _get_my_tasks_searchbar_filters(self, project_domain=None, task_domain=None):
        """Ajoute « En cours » et « Terminées ».

        Le portail standard ne propose que « Tout » et un filtre par projet, ce
        qui oblige le client à faire le tri à l'œil dans les tâches closes.
        """
        filters = super()._get_my_tasks_searchbar_filters(project_domain, task_domain)
        base = [('project_id', '!=', False), ('is_template', '=', False)]
        closed = list(CLOSED_STATES)
        filters['open'] = {
            'label': _('En cours'),
            'domain': base + [('state', 'not in', closed)],
        }
        filters['closed'] = {
            'label': _('Terminées'),
            'domain': base + [('state', 'in', closed)],
        }
        return filters

    def _task_get_searchbar_groupby(self, milestones_allowed, project=False):
        values = super()._task_get_searchbar_groupby(milestones_allowed, project)
        values['task_type'] = {'label': _('Type'), 'sequence': 65}
        return values

    # ------------------------------------------------------------------
    # /my/tasks : kanban par défaut, liste au choix
    # ------------------------------------------------------------------

    @http.route()
    def portal_my_tasks(self, page=1, date_begin=None, date_end=None, sortby=None,
                        filterby=None, search=None, search_in='name', groupby=None,
                        view=None, **kw):
        """Sert le tableau kanban par défaut, la liste standard sur demande.

        Le choix est mémorisé en session : le client retrouve la vue qu'il a
        quittée en revenant sur /my/tasks.
        """
        if filterby is None:
            filterby = 'open'
        if view in ('kanban', 'list'):
            request.session['wm_my_tasks_view'] = view
        else:
            view = request.session.get('wm_my_tasks_view') or 'kanban'

        if view == 'kanban':
            return self._wm_render_my_tasks_kanban(
                date_begin=date_begin, date_end=date_end, filterby=filterby,
                search=search, search_in=search_in,
            )
        response = super().portal_my_tasks(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby,
            filterby=filterby, search=search, search_in=search_in, groupby=groupby, **kw,
        )
        # `request.render` renvoie une réponse dont le rendu est différé : son
        # contexte est encore modifiable. C'est le seul moyen d'ajouter une
        # valeur au gabarit standard sans le réécrire. Le compteur vient du
        # MÊME domaine que la liste affichée, sinon les deux divergeraient.
        qcontext = getattr(response, 'qcontext', None)
        if isinstance(qcontext, dict):
            qcontext['task_count'] = request.env['project.task'].search_count(
                self._wm_tasks_domain(filterby, search, search_in, date_begin, date_end))
            qcontext['current_view'] = 'list'
        return response

    # ------------------------------------------------------------------
    # Création d'une tâche depuis le portail
    # ------------------------------------------------------------------

    def _wm_creatable_projects(self):
        """Projets dans lesquels l'utilisateur a le droit de créer une tâche.

        Pour un utilisateur du portail, c'est la liste de ses collaborations
        NON limitées : c'est exactement la condition de la règle d'écriture
        d'Odoo (project_task_rule_portal_project_sharing).
        """
        user = request.env.user
        if user._is_internal():
            return request.env['project.project'].search([('active', '=', True)])
        collaborations = request.env['project.collaborator'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('limited_access', '=', False),
        ])
        return collaborations.project_id.sudo().filtered('active')

    def _wm_task_new_values(self, projects, data=None, error=None):
        Task = request.env['project.task']
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'task_new',
            'projects': projects,
            'task_types': Task._fields['task_type']._description_selection(request.env),
            'priorities': Task._fields['priority']._description_selection(request.env),
            'data': data or {},
            'error': error,
        })
        return values

    @http.route('/my/tasks/new', type='http', auth='user', website=True, methods=['GET'])
    def wm_portal_task_new(self, **kw):
        projects = self._wm_creatable_projects()
        return request.render(
            'wm_project_task_portal.portal_task_new',
            self._wm_task_new_values(projects, data=kw))

    @http.route('/my/tasks/new', type='http', auth='user', website=True, methods=['POST'])
    def wm_portal_task_create(self, **post):
        Task = request.env['project.task']
        projects = self._wm_creatable_projects()

        def refuser(message):
            return request.render(
                'wm_project_task_portal.portal_task_new',
                self._wm_task_new_values(projects, data=post, error=message))

        try:
            project_id = int(post.get('project_id') or 0)
        except ValueError:
            project_id = 0
        if project_id not in projects.ids:
            return refuser(_("Choisissez un projet dans lequel vous pouvez créer une tâche."))

        name = (post.get('name') or '').strip()
        if not name:
            return refuser(_("Le titre est obligatoire."))

        task_type = post.get('task_type') or 'question'
        if task_type not in dict(Task._fields['task_type']._description_selection(request.env)):
            return refuser(_("Type de tâche inconnu."))
        priority = post.get('priority') or '1'
        if priority not in dict(Task._fields['priority']._description_selection(request.env)):
            return refuser(_("Priorité inconnue."))

        vals = {
            'name': name,
            'task_type': task_type,
            'priority': priority,
        }
        description = (post.get('description') or '').strip()
        if description:
            # Saisie libre : on la convertit en HTML plutôt que de l'injecter
            # telle quelle dans un champ html.
            vals['description'] = plaintext2html(description)

        try:
            # Le projet passe par le CONTEXTE et non par les valeurs : c'est le
            # seul chemin qu'Odoo autorise au portail (`project_id` n'est
            # modifiable que via `default_project_id`, cf. project_task.create).
            task = Task.with_context(default_project_id=project_id).create(vals)
        except (AccessError, UserError) as exc:
            return refuser(str(exc))

        for storage in request.httprequest.files.getlist('attachments'):
            if not storage or not storage.filename:
                continue
            request.env['ir.attachment'].sudo().create({
                'name': storage.filename,
                'datas': base64.b64encode(storage.read()),
                'res_model': 'project.task',
                'res_id': task.id,
                'mimetype': storage.content_type,
            })

        return request.redirect('/my/tasks/%s' % task.id)

    def _wm_tasks_domain(self, filterby='open', search=None, search_in='name',
                         date_begin=None, date_end=None):
        """Domaine commun au tableau kanban et au compteur de la vue liste.

        Écrit une seule fois : deux domaines qui divergent donneraient un
        compteur qui ne correspond pas à ce qui est affiché.
        """
        searchbar_filters = self._get_my_tasks_searchbar_filters([('is_template', '=', False)])
        domain = list(searchbar_filters.get(filterby, searchbar_filters['all'])['domain'])
        domain += [('has_template_ancestor', '=', False)]
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        if search and search_in:
            domain += list(self._task_get_search_domain(search_in, search, True, False))
        return domain

    def _wm_render_my_tasks_kanban(self, date_begin=None, date_end=None, filterby='open',
                                   search=None, search_in='name'):
        Task = request.env['project.task']
        searchbar_filters = self._get_my_tasks_searchbar_filters([('is_template', '=', False)])
        domain = self._wm_tasks_domain(filterby, search, search_in, date_begin, date_end)

        # Lecture avec les droits de l'utilisateur : les règles d'enregistrement
        # d'Odoo s'appliquent d'elles-mêmes. Pas de sudo — c'est précisément ce
        # que faisait l'ancien module v17, et ça contournait toute la sécurité.
        tasks = Task.search(domain, order='priority desc, id desc', limit=KANBAN_LIMIT + 1)
        truncated = len(tasks) > KANBAN_LIMIT
        tasks = tasks[:KANBAN_LIMIT]

        # La recherche ci-dessus s'est faite sous l'identité de l'utilisateur :
        # les règles d'enregistrement ont déjà écarté ce qu'il n'a pas le droit
        # de voir. On peut donc passer en sudo pour l'AFFICHAGE seul, sinon les
        # champs hors liste blanche portail (couleur d'étiquette, nom du projet)
        # lèveraient une erreur d'accès. C'est le motif employé par Odoo
        # lui-même dans _prepare_tasks_values. Les écritures, elles, restent
        # sous l'identité de l'utilisateur (voir wm_portal_task_set_stage).
        tasks = tasks.sudo()

        # Les colonnes reprennent toutes les étapes des projets concernés, y
        # compris celles qui sont vides : sinon on ne peut rien y déposer.
        projects = tasks.project_id
        stages = projects.sudo().type_ids.sorted(lambda s: (s.sequence, s.id))
        columns = [{
            'stage': stage,
            'tasks': tasks.filtered(lambda t: t.stage_id == stage),
        } for stage in stages]
        orphans = tasks.filtered(lambda t: not t.stage_id)
        if orphans:
            columns.append({'stage': Task.env['project.task.type'], 'tasks': orphans})

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'task',
            'default_url': '/my/tasks',
            'columns': columns,
            'task_count': len(tasks),
            'truncated': truncated,
            'kanban_limit': KANBAN_LIMIT,
            'priority_labels': dict(Task._fields['priority']._description_selection(request.env)),
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
            'searchbar_inputs': self._task_get_searchbar_inputs(True),
            'search_in': search_in,
            'search': search,
            'view': 'kanban',
            'can_drag': bool(projects.filtered(lambda p: p.sudo()._check_project_sharing_access())),
        })
        return request.render('wm_project_task_portal.portal_my_tasks_kanban', values)

    # ------------------------------------------------------------------
    # Glisser-déposer : changement d'étape
    # ------------------------------------------------------------------

    @http.route('/my/tasks/<int:task_id>/stage', type='jsonrpc', auth='user', methods=['POST'])
    def wm_portal_task_set_stage(self, task_id, stage_id, **kw):
        """Déplace une tâche d'une colonne à l'autre.

        `stage_id` fait partie des champs modifiables par le portail chez Odoo
        (PROJECT_TASK_WRITABLE_FIELDS) : on écrit donc avec les droits de
        l'utilisateur, sans sudo. Si la personne n'a pas le droit d'écrire, Odoo
        refuse tout seul — c'est le comportement voulu.
        """
        task = request.env['project.task'].browse(int(task_id))
        try:
            task.check_access('write')
        except AccessError:
            return {'error': _("Vous n'avez pas le droit de déplacer cette tâche.")}

        stage = request.env['project.task.type'].sudo().browse(int(stage_id))
        # On n'accepte qu'une étape réellement proposée par le projet de la tâche :
        # sans ce contrôle, un identifiant fabriqué à la main passerait.
        if not stage.exists() or stage not in task.project_id.sudo().type_ids:
            return {'error': _("Cette étape n'appartient pas au projet de la tâche.")}

        try:
            task.write({'stage_id': stage.id})
        except (AccessError, UserError) as exc:
            return {'error': str(exc)}
        return {'stage_id': stage.id, 'stage_name': stage.name}

# -*- coding: utf-8 -*-
import base64
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from collections import OrderedDict, defaultdict

import logging
_logger = logging.getLogger(__name__)

class PortalTaskController(CustomerPortal):
    
    @http.route(['/my/tasks/new'], type='http', auth='user', website=True)
    def portal_task_new(self, **kwargs):
        partner = request.env.user.partner_id.commercial_partner_id
        
        projects = request.env['project.project'].sudo().search([
            ('partner_id', 'child_of', partner.id),
            ('stage_id', 'in', [1, 2])
        ])

        values = {
            'projects': projects,
            'data': kwargs,
            'error': False,
        }
        return request.render('wm_project_task_portal_custom.portal_task_new_form', values)

    @http.route(['/my/tasks/create'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_task_create(self, **post):
        partner = request.env.user.partner_id.commercial_partner_id
        allowed_projects = request.env['project.project'].sudo().search([
            ('partner_id', 'child_of', partner.id)
        ])

        project_id = int(post.get('project_id') or 0)
        if project_id not in allowed_projects.ids:
            return request.redirect('/my/home')
          
        vals = {
            'name': post.get('name'),
            'project_id': project_id,
            'description': post.get('description') or 'COUCOU',
            'partner_id': request.env.user.partner_id.id,
            'task_type': post.get('task_type') or 'question',
        }

        task = request.env['project.task'].sudo().create(vals)

        # Pièces jointes
        attachments = request.httprequest.files.getlist('attachments')
        for file_storage in attachments:
            if file_storage and file_storage.filename:
                request.env['ir.attachment'].sudo().create({
                    'name': file_storage.filename,
                    'datas': base64.b64encode(file_storage.read()),
                    'res_model': 'project.task',
                    'res_id': task.id,
                    'mimetype': file_storage.content_type,
                })

        return request.redirect('/my/tasks')  # adapte si tu as cette page
    
    @http.route()
    def portal_my_tasks(self, page=1, date_begin=None, date_end=None, sortby=None,
                        search=None, search_in='content', groupby='project',
                        filterby=None, view=None, **kwargs):

        partner = request.env.user.partner_id.commercial_partner_id

        allowed_projects = request.env['project.project'].sudo().search([
            ('partner_id', 'child_of', partner.id),
            ('stage_id', 'in', [1, 2])
        ])
        domain = [('project_id', 'in', allowed_projects.ids)]

        if view == 'kanban':
            tasks = request.env['project.task'].sudo().search(domain)

            stages = request.env['project.task.type'].sudo().search([], order='sequence ASC')
            stage_map = defaultdict(list)
            for task in tasks:
                stage_map[task.stage_id].append(task)

            # Utilise un OrderedDict pour garder l’ordre des stages
            tasks_by_stage = OrderedDict()
            for stage in stages:
                if stage_map.get(stage):
                    tasks_by_stage[stage] = stage_map[stage]

            return request.render('wm_project_task_portal_custom.portal_my_tasks_kanban', {
                'tasks_by_stage': tasks_by_stage,
                'grouped_tasks': tasks_by_stage,  # Pour la compatibilité avec le template
                'page_name': 'project_task',
                'view': 'kanban',
            })

        else:
            # Vue Liste (par défaut ou explicitement demandée)
            searchbar_filters = self._get_my_tasks_searchbar_filters()
            if not filterby:
                filterby = 'all'
            domain += searchbar_filters.get(filterby, searchbar_filters.get('all'))['domain']

            values = self._prepare_tasks_values(page, date_begin, date_end, sortby, search, search_in, groupby, domain=domain)

            pager_vals = values['pager']
            pager_vals['url_args'].update(filterby=filterby)
            pager = portal_pager(**pager_vals)

            values.update({
                'grouped_tasks': values['grouped_tasks'](pager['offset']),
                'pager': pager,
                'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
                'filterby': filterby,
                'view': 'list',
            })

            return request.render("wm_project_task_portal_custom.portal_my_tasks_kanban_switch", values)
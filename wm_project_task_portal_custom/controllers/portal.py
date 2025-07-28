from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class CustomPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        _logger.error(">>> CustomPortal._prepare_home_portal_values 1111")
        values = super()._prepare_home_portal_values(counters)
        values['custom_task_creation_count'] = 1
        return values
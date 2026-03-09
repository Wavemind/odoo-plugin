# -*- coding: utf-8 -*-
{
    'name': 'Custom Invoice Logo',
    'version': '17.0.1.0.0',
    'summary': 'Layout de facturation Wavemind — logo statique, robuste aux mises à jour',
    'author': 'Wavemind',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'depends': ['base', 'account', 'web', 'l10n_din5008'],
    'data': [
        'views/report_invoice_logo.xml',
        'data/report_layout.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

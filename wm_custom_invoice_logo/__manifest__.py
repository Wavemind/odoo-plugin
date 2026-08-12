# -*- coding: utf-8 -*-
{
    'name': 'WM Custom Invoice Logo',
    'version': '17.0.2.0.0',
    'summary': 'Layout de facturation Wavemind — logo statique, gabarit A4 standard',
    'description': """
Mise en page des documents Wavemind (factures, devis, …).

Calqué sur web.external_layout_standard, avec un logo servi par le module
plutôt que par le champ logo de la société. Ne dépend de l10n_din5008 que
pour le tableau de métadonnées du document (n° de pièce, dates, référence) —
aucune classe de mise en page DIN n'est utilisée.

Format papier attendu : « A4 » (marge haute 40 mm, header_spacing 35 mm).
""",
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

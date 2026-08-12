# -*- coding: utf-8 -*-
{
    'name': 'WM Custom Invoice Logo',
    'version': '19.0.1.0.0',
    'summary': "Layout de facturation Wavemind — logo statique, pied de page fixe",
    'description': """
Mise en page de facturation Wavemind, construite par **héritage primaire** du
layout DIN 5008 d'Odoo.

Seules deux zones sont redéfinies : l'en-tête (logo statique) et le pied de page
(coordonnées Wavemind). Tout le reste — bloc adresse, métadonnées du document,
pagination — est hérité et suit donc automatiquement les évolutions d'Odoo.

La version 17 était une copie intégrale du layout : elle aurait affiché des
factures sans numéro ni date en version 19, les champs `l10n_din5008_*` ayant
disparu du standard.
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

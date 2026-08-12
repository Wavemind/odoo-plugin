# -*- coding: utf-8 -*-
{
    'name': 'WM Branding',
    'version': '19.0.1.0.0',
    'summary': "Icônes d'applications aux couleurs Wavemind",
    'description': """
Remplace les icônes des applications du menu principal.

Le champ `web_icon` de `ir.ui.menu` ne contient qu'un pointeur texte de la forme
`module,chemin/vers/fichier.png`. Il suffit donc d'embarquer ses propres images
ici et d'y faire pointer les menus : rien n'est modifié dans les modules d'Odoo,
et les icônes survivent aux montées de version.

Pour ajouter ou changer une icône :
  1. déposer le PNG dans static/src/img/ (carré, 140x140 px, fond transparent)
  2. ajouter la ligne correspondante dans data/menu_icons.xml
  3. mettre à jour le module
""",
    'author': 'Wavemind',
    'license': 'LGPL-3',
    'category': 'Technical',
    'depends': ['base'],
    'data': ['data/menu_icons.xml'],
    'installable': True,
    'application': False,
}

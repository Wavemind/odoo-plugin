# Correctifs sur des modules tiers

Ces correctifs portent sur des dépôts que nous ne contrôlons pas (OCA). Ils
sont conservés ici parce que c'est le seul endroit durable : les répertoires
d'addons du serveur ne sont pas des dépôts git, et une mise à jour du dépôt
d'origine les effacerait sans bruit.

**À réappliquer après chaque mise à jour du dépôt concerné.**

## project_timeline_no_precompute_portal_create.patch

**Dépôt** : OCA/project, branche 19.0 — module `project_timeline`
**Requis par** : `wm_project_task_portal`

`project_timeline` déclare `planned_date_start` et `planned_date_end` en
`precompute=True`. Un champ précalculé force l'ORM à instancier un
enregistrement transitoire pendant le `create`, ce qui lit les colonnes
magiques `create_uid` et `write_uid`. Ces colonnes sont hors de la liste
blanche portail d'Odoo 19 : **toute création de tâche par un utilisateur du
portail échoue en `AccessError`**.

Le correctif retire `precompute` des deux champs. Ils restent `store=True` :
ils sont simplement calculés après l'insertion, ce qui ne change rien au
fonctionnement du module.

Vérifié par isolation : avec le precompute, la création échoue ; sans lui,
elle passe.

### Application

    cd <addons>/project
    patch -p1 < project_timeline_no_precompute_portal_create.patch

### Vérification

    grep -n precompute project_timeline/models/project_task.py
    # ne doit plus rien renvoyer

À remonter à l'OCA : le precompute n'apporte rien ici et casse le portail.

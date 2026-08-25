# Polices — à lire avant tout déploiement

Le module habille le portail avec **PP Neue Montreal** (graisses 400, 500, 600),
la police de wavemind.ch.

## Les fichiers ne sont pas dans ce dépôt

C'est délibéré. PP Neue Montreal est une **fonte commerciale** (Pangram
Pangram) et `Wavemind/odoo-plugin` est un dépôt **public** : versionner les
fichiers reviendrait à les redistribuer, ce qu'aucune licence web ordinaire
n'autorise.

Ils sont donc exclus par le `.gitignore` et déployés à la main.

## Conséquence

Un déploiement fait **uniquement** depuis ce dépôt n'aura pas les polices.
Le portail reste correct — la pile de repli (Arial) prend le relais — mais
l'habillage n'est plus celui de la marque.

## Déployer les polices

Les trois fichiers attendus, dans `static/src/fonts/` :

    pp-neue-montreal-400.woff2
    pp-neue-montreal-500.woff2
    pp-neue-montreal-600.woff2

Ils proviennent de wavemind.ch (`/_next/static/media/*.otf`), convertis en
WOFF2 (168 Ko au total contre 359 Ko en OTF).

Sur le serveur :

    scp pp-neue-montreal-*.woff2 root@<serveur>:/var/lib/docker/volumes/\
    dzw465htks0pnof1al7idmzd-odoo-addons/_data/wavemind/\
    wm_project_task_portal/static/src/fonts/

Puis redémarrer le conteneur Odoo pour régénérer les bundles.

## Si le dépôt passe un jour en privé

Retirer les deux lignes correspondantes du `.gitignore` et versionner les
fichiers : le déploiement redevient alors autonome.

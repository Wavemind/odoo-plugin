/**
 * Tableau kanban du portail : repliage des colonnes et glisser-déposer.
 *
 * Deux comportements distincts, volontairement séparés :
 *
 *  - Le REPLIAGE est purement visuel et toujours disponible, même pour un
 *    client qui n'a que le droit de lecture. L'état initial vient du champ
 *    `fold` de l'étape dans Odoo ; un choix manuel prend ensuite le dessus et
 *    est mémorisé dans le navigateur.
 *
 *  - Le GLISSER-DÉPOSER écrit `stage_id`, un des champs qu'Odoo autorise le
 *    portail à modifier. Il n'est actif que si le serveur a posé
 *    data-can-drag="1", et l'écriture passe par /my/tasks/<id>/stage qui
 *    revérifie les droits. Ce fichier ne fait que l'interface : il n'accorde
 *    aucun accès par lui-même.
 */
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

const STORAGE_KEY = "wm_portal_kanban_folded";

publicWidget.registry.WmPortalKanban = publicWidget.Widget.extend({
    selector: ".wm_kanban",

    start() {
        this._dragged = null;
        this._canDrag = this.el.dataset.canDrag === "1";

        this._onFoldClick = this._onFoldClick.bind(this);
        this.el.addEventListener("click", this._onFoldClick);

        if (this._canDrag) {
            this._onDragStart = this._onDragStart.bind(this);
            this._onDragEnd = this._onDragEnd.bind(this);
            this._onDragOver = this._onDragOver.bind(this);
            this._onDragLeave = this._onDragLeave.bind(this);
            this._onDrop = this._onDrop.bind(this);
            this.el.addEventListener("dragstart", this._onDragStart);
            this.el.addEventListener("dragend", this._onDragEnd);
            this.el.addEventListener("dragover", this._onDragOver);
            this.el.addEventListener("dragleave", this._onDragLeave);
            this.el.addEventListener("drop", this._onDrop);
        }

        this._restoreFoldState();
        this._setupScrollControls();
        return this._super(...arguments);
    },

    // --- Défilement horizontal -------------------------------------------

    /**
     * Flèches et fondus de bord.
     *
     * La barre de défilement native se place SOUS le contenu : dès que les
     * colonnes sont hautes, elle tombe en bas de page et devient introuvable.
     * On ne la retire pas — on ajoute deux repères qui, eux, restent visibles.
     * Tout est masqué s'il n'y a rien à faire défiler.
     */
    _setupScrollControls() {
        this.wrap = this.el.closest(".wm_kanban_wrap");
        if (!this.wrap) {
            return;
        }
        this.navPrev = this.wrap.querySelector(".wm_kanban_nav_prev");
        this.navNext = this.wrap.querySelector(".wm_kanban_nav_next");

        this._onBoardScroll = this._refreshScrollControls.bind(this);
        this._onWindowResize = this._refreshScrollControls.bind(this);
        this._onNavClick = this._onNavClick.bind(this);

        this.el.addEventListener("scroll", this._onBoardScroll, { passive: true });
        window.addEventListener("resize", this._onWindowResize);
        this.navPrev?.addEventListener("click", this._onNavClick);
        this.navNext?.addEventListener("click", this._onNavClick);

        this._refreshScrollControls();
    },

    _refreshScrollControls() {
        if (!this.wrap) {
            return;
        }
        // 2 px de marge : les navigateurs rendent des largeurs fractionnaires,
        // sans quoi la flèche « suivant » resterait allumée en bout de course.
        const marge = 2;
        const max = this.el.scrollWidth - this.el.clientWidth;
        const debordement = max > marge;
        const peutReculer = debordement && this.el.scrollLeft > marge;
        const peutAvancer = debordement && this.el.scrollLeft < max - marge;

        this.wrap.classList.toggle("wm_can_prev", peutReculer);
        this.wrap.classList.toggle("wm_can_next", peutAvancer);
        this.navPrev?.classList.toggle("wm_visible", peutReculer);
        this.navNext?.classList.toggle("wm_visible", peutAvancer);
    },

    _onNavClick(ev) {
        const suivant = !!ev.currentTarget.closest(".wm_kanban_nav_next");
        const colonne = this.el.querySelector(".wm_kanban_column");
        // Un cran = une colonne, pour retomber sur un alignement propre.
        const pas = colonne ? colonne.getBoundingClientRect().width + 16 : 300;
        this.el.scrollBy({ left: suivant ? pas : -pas, behavior: "smooth" });
    },

    destroy() {
        this.el.removeEventListener("click", this._onFoldClick);
        if (this.wrap) {
            this.el.removeEventListener("scroll", this._onBoardScroll);
            window.removeEventListener("resize", this._onWindowResize);
            this.navPrev?.removeEventListener("click", this._onNavClick);
            this.navNext?.removeEventListener("click", this._onNavClick);
        }
        if (this._canDrag) {
            this.el.removeEventListener("dragstart", this._onDragStart);
            this.el.removeEventListener("dragend", this._onDragEnd);
            this.el.removeEventListener("dragover", this._onDragOver);
            this.el.removeEventListener("dragleave", this._onDragLeave);
            this.el.removeEventListener("drop", this._onDrop);
        }
        return this._super(...arguments);
    },

    // --- Repliage ---------------------------------------------------------

    /**
     * Choix manuels de l'utilisateur, par identifiant d'étape.
     * Une étape absente de la table garde l'état décidé par Odoo (champ `fold`).
     * Le stockage peut être indisponible (navigation privée, cookies bloqués) :
     * dans ce cas on se rabat silencieusement sur les valeurs du serveur.
     */
    _readFoldState() {
        try {
            return JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}");
        } catch {
            return {};
        }
    },

    _writeFoldState(state) {
        try {
            window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch {
            // Sans stockage, le repliage reste valable pour la page en cours.
        }
    },

    _restoreFoldState() {
        const state = this._readFoldState();
        this.el.querySelectorAll(".wm_kanban_column").forEach((column) => {
            const key = column.dataset.stageId;
            if (Object.prototype.hasOwnProperty.call(state, key)) {
                column.classList.toggle("wm_kanban_folded", !!state[key]);
            }
        });
    },

    _onFoldClick(ev) {
        const column = ev.target.closest(".wm_kanban_column");
        if (!column) {
            return;
        }
        // On replie depuis le bouton ; on déplie aussi en cliquant n'importe où
        // sur la bande repliée, qui est trop étroite pour viser le chevron.
        const isFolded = column.classList.contains("wm_kanban_folded");
        const onButton = !!ev.target.closest(".wm_kanban_fold");
        if (!onButton && !isFolded) {
            return;
        }
        ev.preventDefault();

        const folded = !isFolded;
        column.classList.toggle("wm_kanban_folded", folded);

        const state = this._readFoldState();
        state[column.dataset.stageId] = folded;
        this._writeFoldState(state);

        // Replier une colonne change la largeur totale du tableau : sans ça,
        // les flèches resteraient affichées alors qu'il n'y a plus rien à
        // faire défiler.
        this._refreshScrollControls();
    },

    // --- Glisser-déposer --------------------------------------------------

    /**
     * Zone de dépôt correspondant à la cible du pointeur.
     * Une colonne repliée n'expose plus sa liste de cartes sous le curseur :
     * on remonte alors à la colonne pour retrouver sa zone.
     */
    _zoneOf(target) {
        if (!target || !target.closest) {
            return null;
        }
        const zone = target.closest(".wm_kanban_cards");
        if (zone) {
            return zone;
        }
        const column = target.closest(".wm_kanban_column");
        return column ? column.querySelector(".wm_kanban_cards") : null;
    },

    _refreshCounts() {
        this.el.querySelectorAll(".wm_kanban_column").forEach((column) => {
            const count = column.querySelectorAll(".wm_kanban_card").length;
            const badge = column.querySelector(".wm_kanban_column_count");
            if (badge) {
                badge.textContent = count;
            }
        });
    },

    _clearDropzones() {
        this.el
            .querySelectorAll(".wm_kanban_dropzone")
            .forEach((zone) => zone.classList.remove("wm_kanban_dropzone"));
    },

    _onDragStart(ev) {
        const card = ev.target.closest(".wm_kanban_card");
        if (!card) {
            return;
        }
        this._dragged = card;
        this._origin = card.parentElement;
        this._originNext = card.nextElementSibling;
        card.classList.add("wm_kanban_dragging");
        // Nécessaire pour que Firefox déclenche le dépôt.
        ev.dataTransfer.effectAllowed = "move";
        ev.dataTransfer.setData("text/plain", card.dataset.taskId || "");
    },

    _onDragEnd() {
        if (this._dragged) {
            this._dragged.classList.remove("wm_kanban_dragging");
        }
        this._clearDropzones();
        this._dragged = null;
    },

    _onDragOver(ev) {
        if (!this._dragged) {
            return;
        }
        const zone = this._zoneOf(ev.target);
        if (!zone) {
            return;
        }
        // Sans preventDefault, le navigateur refuse le dépôt.
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";
        this._clearDropzones();
        zone.classList.add("wm_kanban_dropzone");
        zone.closest(".wm_kanban_column").classList.add("wm_kanban_dropzone_column");
    },

    _onDragLeave(ev) {
        const zone = this._zoneOf(ev.target);
        if (zone && !zone.contains(ev.relatedTarget)) {
            zone.classList.remove("wm_kanban_dropzone");
            const column = zone.closest(".wm_kanban_column");
            if (column && !column.contains(ev.relatedTarget)) {
                column.classList.remove("wm_kanban_dropzone_column");
            }
        }
    },

    async _onDrop(ev) {
        const zone = this._zoneOf(ev.target);
        const card = this._dragged;
        if (!zone || !card) {
            return;
        }
        ev.preventDefault();
        this._clearDropzones();
        this.el
            .querySelectorAll(".wm_kanban_dropzone_column")
            .forEach((c) => c.classList.remove("wm_kanban_dropzone_column"));

        const column = zone.closest(".wm_kanban_column");
        const stageId = parseInt(column.dataset.stageId, 10);
        const taskId = parseInt(card.dataset.taskId, 10);
        if (!stageId || !taskId || zone === this._origin) {
            return;
        }

        // Déplacement optimiste : la carte bouge tout de suite, elle revient à
        // sa place si le serveur refuse.
        zone.appendChild(card);
        card.classList.add("wm_kanban_saving");
        this._refreshCounts();

        let result;
        try {
            result = await rpc(`/my/tasks/${taskId}/stage`, { stage_id: stageId });
        } catch {
            result = { error: "Le déplacement n'a pas pu être enregistré." };
        }
        card.classList.remove("wm_kanban_saving");

        if (result && result.error) {
            if (this._origin) {
                this._origin.insertBefore(card, this._originNext || null);
            }
            this._refreshCounts();
            window.alert(result.error);
        }
    },
});

/* @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";

    publicWidget.registry.KanbanScroll = publicWidget.Widget.extend({
        selector: '.kanban-scroll-container',
        events: {
            'mousedown': '_onMouseDown',
            'mousemove': '_onMouseMove',
            'mouseup': '_onMouseUp',
            'mouseleave': '_onMouseUp',
        },

        /**
         * @override
         */
        start: function () {
            try {
                this.isDragging = false;
                this.startX = 0;
                this.scrollLeft = 0;
                this._checkScrollable();
                return this._super.apply(this, arguments);
            } catch (error) {
                console.warn('KanbanScroll widget initialization error:', error);
                return this._super.apply(this, arguments);
            }
        },

        /**
         * Handle mouse down event to start dragging
         * @param {Event} ev
         * @private
         */
        _onMouseDown: function (ev) {
            // Only start dragging if clicking on the container itself, not on interactive elements
            if (ev.target.closest('a, button, input, .btn')) {
                return;
            }
            
            this.isDragging = true;
            this.startX = ev.pageX - this.el.offsetLeft;
            this.scrollLeft = this.el.scrollLeft;
            this.el.style.cursor = 'grabbing';
            ev.preventDefault();
        },

        /**
         * Handle mouse move event to scroll while dragging
         * @param {Event} ev
         * @private
         */
        _onMouseMove: function (ev) {
            if (!this.isDragging) return;
            
            ev.preventDefault();
            var x = ev.pageX - this.el.offsetLeft;
            var walk = (x - this.startX) * 2;
            this.el.scrollLeft = this.scrollLeft - walk;
        },

        /**
         * Handle mouse up event to stop dragging
         * @param {Event} ev
         * @private
         */
        _onMouseUp: function (ev) {
            this.isDragging = false;
            this._checkScrollable();
        },

        /**
         * Check if the container is scrollable and update cursor accordingly
         * @private
         */
        _checkScrollable: function () {
            var isScrollable = this.el.scrollWidth > this.el.clientWidth;
            if (isScrollable) {
                this.el.style.cursor = 'grab';
            } else {
                this.el.style.cursor = 'default';
            }
        },
    }); 
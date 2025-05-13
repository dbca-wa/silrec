<template lang="html">
    <div>
        <div class="toggle_filters_wrapper rounded">
            <div
                :id="button_elem_id"
                data-bs-toggle="collapse"
                :data-bs-target="'#' + target_elem_id"
                class="toggle_filters_button d-flex align-items-center"
                @click="toggle_filters_button_clicked"
            >
                <div class="me-auto ps-1 title">{{ component_title }}</div>
                <div class="me-2">
                    <i
                        :id="warning_icon_id"
                        :title="warning_icon_title"
                        class="fa-solid fa-exclamation-circle fa-2x filter_warning_icon"
                    ></i>
                </div>
                <div class="me-2">
                    <i
                        :id="chevron_elem_id"
                        class="rotate_icon fa-solid fa-chevron-right"
                    ></i>
                </div>
            </div>

            <div
                :id="target_elem_id"
                class="border-top body mt-1"
                :class="collapsed ? 'collapse' : 'collapse show'"
                :aria-expanded="collapsed ? 'false' : 'true'"
            >
                <slot></slot>
            </div>
        </div>
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';

export default {
    name: 'CollapsibleComponent',
    props: {
        component_title: {
            type: String,
            required: false,
            default: '',
        },
        collapsed: {
            type: Boolean,
            default: true,
        },
    },
    emits: ['created'],
    data: function () {
        return {
            target_elem_id: 'target_elem_' + uuid(),
            button_elem_id: 'button_elem_' + uuid(),
            chevron_elem_id: 'chevron_elem_' + uuid(),
            warning_icon_id: 'warning_elem_' + uuid(),
            warning_icon_title: '',
            display_icon: false,
            filters_expanded: null,
        };
    },
    watch: {
        filters_expanded: function () {
            let chevron_icon = $('#' + this.chevron_elem_id);
            if (this.filters_expanded) {
                chevron_icon.addClass('chev_rotated');
            } else {
                chevron_icon.removeClass('chev_rotated');
            }
        },
    },
    mounted: function () {
        this.$nextTick(function () {
            this.$emit('created');
        });
    },
    methods: {
        toggle_filters_button_clicked: function () {
            // Bootstrap add a 'collapsed' class name to the element
            let filters_expanded_when_clicked = $(
                '#' + this.button_elem_id
            ).hasClass('collapsed');
            this.filters_expanded = !filters_expanded_when_clicked;
        },
        show_warning_icon: function (show) {
            let warning_icon = $('#' + this.warning_icon_id);
            if (show) {
                warning_icon.css('opacity', 1);
                this.warning_icon_title = 'filter(s) applied';
            } else {
                warning_icon.css('opacity', 0);
                this.warning_icon_title = '';
            }
        },
    },
};
</script>

<style scoped>
.toggle_filters_wrapper {
    background: #efefee;
    padding: 0.5em;
    display: grid;
}

.toggle_filters_button {
    cursor: pointer;
}

.filter_warning_icon {
    color: #ffc107;
    transition: 0.5s;
}

.rotate_icon {
    transition: 0.5s;
}

.title {
    color: #505050;
}
</style>

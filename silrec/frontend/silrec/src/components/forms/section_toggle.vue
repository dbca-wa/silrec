<template lang="html">
    <div :id="custom_id" class="card mb-3 section-toggle">
        <div class="card-header fw-bold h4 p-4">
            <div
                :id="'show_hide_switch_' + section_body_id"
                class="row"
                aria-expanded="true"
                :aria-controls="section_body_id"
                @click="toggle_show_hide($event)"
            >
                <div class="col-11 label" :style="'color:' + customColor">
                    {{ label }}
                    <small v-if="subtitle" class="text-muted">{{
                        subtitle
                    }}</small>
                </div>
                <div class="col-1 text-end">
                    <i
                        :id="chevron_elem_id"
                        class="bi fw-bold chevron-toggle cursor-pointer"
                        role="button"
                        :data-bs-target="'#' + section_body_id"
                    >
                    </i>
                </div>
            </div>
        </div>
        <div
            :id="section_body_id"
            ref="section_body"
            :class="detailsClass"
            :style="'color:' + customColor"
        >
            <slot></slot>
        </div>
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';

export default {
    name: 'FormSection',
    props: {
        label: {
            type: String,
            required: true,
        },
        subtitle: {
            type: String,
            default: '',
        },
        index: {
            type: String,
            required: true,
        },
        hideHeader: {
            type: Boolean,
            default: false,
        },
        customColor: {
            type: String,
            default: '',
        },
        formCollapse: {
            type: Boolean,
            default: false,
        },
    },
    data: function () {
        return {
            custom_id: uuid(),
            chevron_elem_id: 'chevron_elem_' + uuid(),
        };
    },
    computed: {
        detailsClass: function () {
            return this.formCollapse ? 'card-body collapse' : 'card-body';
        },
        section_header_id: function () {
            return 'section_header_' + this.index;
        },
        section_body_id: function () {
            return 'section_body_' + this.index;
        },
    },
    mounted: function () {
        // eslint-disable-next-line no-undef
        chevron_toggle.init();
    },
    methods: {
        toggle_show_hide: function (evt) {
            if (!evt.target.classList.contains('down-chevron-open')) {
                // Only redraw the datatable if the section is being opened
                return;
            }

            // $(this.$refs.section_body)[0].__vnode.children[0].children[0].component.ctx.$refs.organisation_contacts_datatable.vmDataTable.draw()

            // Get a list of all the nodes in the slot section
            let formSection_vnode = $(
                this.$refs.section_body
            )[0].__vnode.children.reduce((objs, obj) => {
                if (obj.__v_isVNode) {
                    objs.push(obj);
                }
                return objs;
            }, []);
            formSection_vnode.forEach((vnode) => {
                // Store child elements within each node to a list
                let refs = Array();
                if (vnode.children) {
                    vnode.children.map((child) => {
                        if (child.component) {
                            refs.push(child.component.ctx.$refs);
                        }
                    });
                }
                if (vnode.dynamicChildren) {
                    vnode.dynamicChildren.map((child) => {
                        if (child.component) {
                            refs.push([child.component.ctx]);
                        }
                    });
                }

                refs.forEach((ref) => {
                    // Redraw (without updating ordering and search) the element if it is a datatable
                    // See: https://datatables.net/reference/api/draw()
                    Object.keys(ref).forEach((key) => {
                        if (ref[key].vmDataTable) {
                            ref[key].vmDataTable.draw('page');
                        }
                    });
                });
            });
        },
    },
};
</script>

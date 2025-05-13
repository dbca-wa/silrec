<template>
    <div v-show="show" :transition="transition">
        <div
            :id="id"
            class="modal"
            data-bs-backdrop="static"
            data-bs-keyboard="false"
            tabindex="-1"
            role="dialog"
            aria-hidden="true"
            @click.self="clickMask"
        >
            <div class="modal-dialog" :class="modalClass" role="document">
                <div class="modal-content">
                    <slot name="header">
                        <div class="modal-header">
                            <h4 class="modal-title">
                                <slot name="title">{{ title }}</slot>
                            </h4>
                            <button
                                type="button"
                                class="btn-close btn-close-white"
                                data-bs-dismiss="modal"
                                aria-label="Close"
                                @click="cancel"
                            ></button>
                        </div>
                    </slot>
                    <div class="modal-body">
                        <slot></slot>
                    </div>
                    <div class="modal-footer">
                        <slot name="footer">
                            <button
                                type="button"
                                :class="cancelClass"
                                class="licensing-btn mb-1"
                                @click="cancel"
                            >
                                {{ cancelText }}
                            </button>
                            <button
                                v-if="okText"
                                id="okBtn"
                                type="button"
                                class="btn-primary mb-1"
                                :class="okClass"
                                :disabled="okDisabled"
                                @click="ok"
                            >
                                {{ okText }}
                            </button>
                        </slot>
                    </div>
                </div>
            </div>
        </div>
        <div class="modal-backdrop show"></div>
    </div>
</template>

<script>
/**
 * Bootstrap Style Modal Component for Vue
 * Depend on Bootstrap.css
 */
import { v4 as uuid } from 'uuid';

export default {
    props: {
        title: {
            type: String,
            default: 'Modal',
        },
        small: {
            type: Boolean,
            default: false,
        },
        large: {
            type: Boolean,
            default: false,
        },
        extraLarge: {
            type: Boolean,
            default: false,
        },
        full: {
            type: Boolean,
            default: false,
        },
        force: {
            type: Boolean,
            default: false,
        },
        transition: {
            type: String,
            default: 'modal',
        },
        okText: {
            type: String,
            default: 'Confirm',
        },
        cancelText: {
            type: String,
            default: 'Cancel',
        },
        okClass: {
            type: String,
            default: 'btn btn-primary',
        },
        cancelClass: {
            type: String,
            default: 'btn btn-secondary',
        },
        closeWhenOK: {
            type: Boolean,
            default: false,
        },
        okDisabled: {
            type: Boolean,
            default: false,
        },
        scrollable: {
            type: Boolean,
            default: false,
        },
    },
    emits: ['created', 'mounted', 'ok', 'cancel'],
    data() {
        return {
            duration: null,
            id: uuid(),
        };
    },
    computed: {
        modalClass() {
            return {
                'modal-xl': this.extraLarge,
                'modal-lg': this.large,
                'modal-sm': this.small,
                'modal-full': this.full,
                'modal-dialog-scrollable': this.scrollable,
            };
        },
        show: function () {
            return this.$parent.isModalOpen;
        },
    },
    watch: {
        show(value) {
            if (value) {
                document.body.className += ' modal-open';
            } else {
                window.setTimeout(() => {
                    document.body.className = document.body.className.replace(
                        /\s?modal-open/,
                        ''
                    );
                }, this.duration || 0);
            }
        },
    },
    created: function () {
        if (this.show) {
            document.body.className += ' modal-open';
        }
        this.$emit('created');
    },
    mounted: function () {
        this.$emit('mounted');
    },
    beforeUnmount() {
        document.body.className = document.body.className.replace(
            /\s?modal-open/,
            ''
        );
    },
    methods: {
        ok() {
            this.$emit('ok');
            if (this.closeWhenOK) {
                this.show = false;
            }
        },
        cancel() {
            this.$emit('cancel');
            this.$parent.close();
        },
        clickMask() {
            if (!this.force) {
                this.cancel();
            }
        },
    },
};
</script>

<style scoped>
.modal {
    display: block;
}

.modal .btn {
    margin-bottom: 0px;
}

.modal-header {
    border-top-left-radius: 0.3rem;
    border-top-right-radius: 0.3rem;
    background-color: #226fbb;
    color: #fff;
    background: #3580ca
        url('/static/silrec_vue/src/assets/parks-bg-banner.gif')
        repeat-x center bottom;
}

.btn-close {
    color: #eee;
}

.modal-footer {
    border-bottom-left-radius: 0.3rem;
    border-bottom-right-radius: 0.3rem;
}

.modal-body {
    background-color: #fff;
    color: #333333;
}

.modal-footer {
    /*background-color: #F5F5F5;
        color: #333333;*/
    background-color: #efefef;
    color: #333333;
}

.modal-transition {
    transition: all 0.6s ease;
}

.modal-leave {
    border-radius: 1px !important;
}

.modal-transition .modal-dialog,
.modal-transition .modal-backdrop {
    transition: all 0.5s ease;
}

.modal-enter .modal-dialog,
.modal-leave .modal-dialog {
    opacity: 0;
    transform: translateY(-30%);
}

.modal-enter .modal-backdrop,
.modal-leave .modal-backdrop {
    opacity: 0;
}

.close {
    font-size: 2.5rem;
    opacity: 0.3;
}

.close:hover {
    opacity: 0.7;
}

#okBtn {
    margin-bottom: 0px;
}
</style>

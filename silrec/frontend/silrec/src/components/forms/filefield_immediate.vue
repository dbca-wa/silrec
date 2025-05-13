<template lang="html">
    <div :class="headerCSS">
        <ul v-if="numDocuments > 0" class="list-group mb-3">
            <li v-for="v in documents" :key="v.id" class="list-group-item">
                <div>
                    <span v-if="v.name.endsWith('.pdf')" class="fa fa-file-pdf">
                        &nbsp;
                    </span>
                    <span v-else class="fa fa-file"> &nbsp; </span>
                    <a
                        :href="
                            Object.hasOwn(v, 'secure_url')
                                ? v.secure_url
                                : v.file
                        "
                        target="_blank"
                    >
                        {{ v.name }}
                    </a>
                    <span v-if="!readonly">
                        &nbsp;<a
                            class="bi bi-trash3"
                            title="Remove file"
                            :filename="v.name"
                            style="cursor: pointer; color: red"
                            @click="delete_document(v)"
                        ></a>
                    </span>
                </div>
            </li>
        </ul>
        <div v-if="show_spinner">
            <BootstrapSpinner
                class="text-primary"
                :center-of-screen="false"
                :small="true"
            />
        </div>
        <div
            v-if="
                (isRepeatable || (!isRepeatable && numDocuments === 0)) &&
                !show_spinner
            "
        >
            <input
                type="file"
                :id="name"
                :key="name"
                :name="name"
                :multiple="multiple"
                :accept="fileTypes"
                :class="ffu_input_element_classname"
                @change="handleChangeWrapper"
            />
            <div v-if="replace_button_by_text">
                <button
                    :id="'button-' + name"
                    class="btn btn-primary ffu-input-text"
                    @click.prevent="button_clicked(name)"
                    :disabled="readonly"
                >
                    <i class="fa fa-upload" aria-hidden="true"></i>&nbsp;
                    {{ text_string }}
                </button>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints, helpers } from '@/utils/hooks';
export default {
    name: 'FileField',
    props: {
        headerCSS: {
            type: String,
            default: '',
        },
        name: {
            type: String,
            default: '',
        },
        label: {
            type: String,
            default: '',
        },
        id: {
            type: String,
            default: '',
        },
        fileTypes: {
            type: String,
            default: function () {
                var file_types =
                    'image/*,' +
                    'video/*,' +
                    'audio/*,' +
                    'application/pdf,text/csv,application/msword,application/vnd.ms-excel,application/x-msaccess,' +
                    'application/x-7z-compressed,application/x-bzip,application/x-bzip2,application/zip,' +
                    '.dbf,.gdb,.gpx,.prj,.shp,.shx,' +
                    '.json,.kml,.gpx';
                return file_types;
            },
        },
        isRepeatable: {
            type: Boolean,
            default: false,
        },
        readonly: {
            type: Boolean,
            default: false,
        },
        documentActionUrl: {
            type: String,
            required: true,
        },
        temporaryDocumentCollectionId: {
            type: Number,
            default: 0,
        },

        // For optional text button
        replace_button_by_text: {
            type: Boolean,
            default: false,
        },
        text_string: {
            type: String,
            default: 'Attach Document',
        },
        approval_type: {
            type: Number,
            required: false,
        },
        approval_type_document_type: {
            type: Number,
            required: false,
        },
        /** Whether to allow for multiple selection from file input field */
        multiple: {
            type: Boolean,
            default: false,
        },
    },
    emits: ['update-parent', 'update-temp-doc-coll-id'],
    data: function () {
        return {
            show_spinner: false,
            documents: [],
            filename: null,
            help_text_url: '',
            commsLogId: null,
            temporary_document_collection_id: null,
        };
    },
    computed: {
        numDocuments: function () {
            if (this.documents) {
                return this.documents.length;
            } else {
                return 0;
            }
        },
        ffu_input_element_classname: function () {
            if (this.replace_button_by_text) {
                return 'ffu-input-elem';
            }
            return '';
        },
        csrf_token: function () {
            return helpers.getCookie('csrftoken');
        },
        document_action_url: function () {
            let url = '';
            if (this.documentActionUrl == 'temporary_document') {
                if (!this.temporary_document_collection_id) {
                    url = api_endpoints.temporary_document;
                } else {
                    url =
                        api_endpoints.temporary_document +
                        this.temporary_document_collection_id +
                        '/process_temp_document/';
                }
            } else {
                url = this.documentActionUrl;
            }
            return url;
        },
    },
    watch: {
        documents: {
            handler: async function () {
                await this.$emit('update-parent');
            },
            deep: true,
        },
        temporaryDocumentCollectionId: function () {
            // read in prop value
            if (this.temporaryDocumentCollectionId) {
                this.temporary_document_collection_id =
                    this.temporaryDocumentCollectionId;
                this.get_documents();
            }
        },
    },
    mounted: function () {
        this.$nextTick(() => {
            if (
                this.documentActionUrl === 'temporary_document' &&
                !this.temporary_document_collection_id
            ) {
                // pass
            } else {
                this.get_documents();
            }
        });
    },
    methods: {
        button_clicked: function (value) {
            if (this.replace_button_by_text) {
                // Input field id contains the document name which may contain
                // special characters (e.g. !"#$%&'()*+,./:;<=>?@[]^`{|}~)
                // Exact match treats values as strings.
                $(`input[id='${value}']`).trigger('click');
            }
        },
        handleChange: async function (e) {
            console.log('Change', e.target.files);
            if (e.target.files.length > 0) {
                await this.save_document(e);
            }
        },
        get_documents: function () {
            var formData = new FormData();

            if (this.document_action_url) {
                this.show_spinner = true;

                formData.append('action', 'list');
                if (this.commsLogId) {
                    formData.append('comms_log_id', this.commsLogId);
                }
                formData.append('input_name', this.name);
                fetch(this.document_action_url, {
                    body: formData,
                    method: 'POST',
                })
                    .then(async (response) => {
                        const resData = await response.json();
                        if (!response.ok) {
                            throw new Error(resData);
                        }
                        this.documents = resData.filedata;
                        this.commsLogId = resData.comms_instance_id;
                    })
                    .catch((resData) => {
                        swal.fire({
                            title: 'File Error',
                            text: JSON.stringify(resData),
                            icon: 'error',
                        });
                    })
                    .finally(() => {
                        this.show_spinner = false;
                    });
            }
        },
        delete_all_documents: function () {
            for (let item of this.documents) {
                this.delete_document(item);
            }
        },
        delete_document: async function (file) {
            var formData = new FormData();
            this.show_spinner = true;

            formData.append('action', 'delete');
            formData.append('input_name', this.name);
            if (this.commsLogId) {
                formData.append('comms_log_id', this.commsLogId);
            }
            formData.append('document_id', file.id);

            if (this.document_action_url) {
                const res = await fetch(this.document_action_url, {
                    body: formData,
                    method: 'POST',
                });
                const resData = await res.json();
                this.documents = resData.filedata;
                this.commsLogId = resData.comms_instance_id;
            }
            this.show_spinner = false;
        },
        cancel: async function () {
            this.show_spinner = true;

            let formData = new FormData();
            formData.append('action', 'cancel');
            formData.append('input_name', this.name);
            if (this.commsLogId) {
                formData.append('comms_log_id', this.commsLogId);
            }

            if (this.document_action_url) {
                await fetch(this.document_action_url, {
                    body: formData,
                    method: 'POST',
                });
            }
            this.show_spinner = false;
        },
        uploadFile(file) {
            let _file = null;

            // if (e.target.files && e.target.files[0]) {
            if (file) {
                let reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = function (e) {
                    _file = e.target.result;
                };
                _file = file;
            }
            return _file;
        },
        handleChangeWrapper: async function (e) {
            this.show_spinner = true;
            if (
                this.documentActionUrl === 'temporary_document' &&
                !this.temporary_document_collection_id
            ) {
                // If temporary_document, create TemporaryDocumentCollection object and allow document_action_url to update
                const res = await fetch(this.document_action_url, {
                    method: 'POST',
                });
                const resData = await res.json();
                this.temporary_document_collection_id = resData.id;
                await this.handleChange(e);
                await this.$emit(
                    'update-temp-doc-coll-id',
                    this.temporary_document_collection_id
                );
            } else {
                await this.handleChange(e);
            }
            this.show_spinner = false;
        },

        save_document: function (e) {
            var formData = new FormData();
            if (!this.document_action_url) {
                console.error('No document_action_url provided');
                return;
            }

            for (let file of e.target.files) {
                formData.append('action', 'save');
                if (this.commsLogId) {
                    formData.append('comms_log_id', this.commsLogId);
                }
                if (this.temporary_document_collection_id) {
                    formData.append(
                        'temporary_document_collection_id',
                        this.temporary_document_collection_id
                    );
                }
                formData.append('input_name', this.name);
                formData.append('approval_type', this.approval_type);
                formData.append(
                    'approval_type_document_type',
                    this.approval_type_document_type
                );
                formData.append('filename', file.name);
                formData.append('_file', this.uploadFile(file));

                fetch(this.document_action_url, {
                    body: formData,
                    method: 'POST',
                })
                    .then(async (response) => {
                        const data = await response.json();
                        if (!response.ok) {
                            swal.fire({
                                title: 'File Error',
                                text: JSON.stringify(data),
                                icon: 'error',
                            });
                        }
                        this.documents = data.filedata;
                        this.commsLogId = data.comms_instance_id;
                    })
                    .catch((error) => {
                        swal.fire({
                            title: 'File Error',
                            text: JSON.stringify(error),
                            icon: 'error',
                        });
                    });
            }
        },
    },
};
</script>

<style scoped lang="css">
input {
    box-shadow: none;
}

.ffu-input-elem {
    display: none !important;
}
.ffu-input-text {
    color: #337ab7;
    cursor: pointer;
}

.list-group {
    display: inline-block;
}
</style>

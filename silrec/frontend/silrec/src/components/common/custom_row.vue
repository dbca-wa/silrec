<template>
    <table class="table table-sm party_detail_table">
        <tbody class="py-3">
            <tr class="mb-3">
                <th>Invited to Competitive Process</th>
                <td>
                    <input
                        v-model="party_invited_at"
                        type="date"
                        class="form-control w-auto"
                        placeholder="DD/MM/YYYY"
                        disabled
                    />
                </td>
            </tr>
            <tr>
                <th>Removed from Competitive Process</th>
                <td>
                    <input
                        v-model="partyFullDataComputed.removed_at"
                        type="date"
                        class="form-control w-auto"
                        placeholder="DD/MM/YYYY"
                        :disabled="elementDisabled"
                        @change="partyDateChanged($event, 'removed_at')"
                    />
                </td>
            </tr>
            <tr>
                <th class="align-top">Details</th>
                <td class="text-wrap">
                    <div
                        v-if="partyFullData.party_details.length > 0"
                        class="details_box p-2"
                    >
                        <template
                            v-for="party_detail in partyFullData.party_details"
                            :key="party_detail.key"
                        >
                            <div class="card mb-2 py-2">
                                <div class="card-body">
                                    <div class="card-header border rounded">
                                        <template
                                            v-if="
                                                party_detail.id ||
                                                elementDisabled
                                            "
                                        >
                                            <!-- This is an entry already saved in the database -->
                                            <div class="card-title">
                                                <span class="fw-bold"
                                                    >Added by</span
                                                >
                                                {{
                                                    party_detail.created_by
                                                        .full_name
                                                        ? party_detail
                                                              .created_by
                                                              .full_name
                                                        : party_detail
                                                              .created_by
                                                              .fullname
                                                }}
                                                <span class="fw-bold">on</span>
                                                {{
                                                    formatDatetime(
                                                        party_detail.created_at
                                                    )
                                                }}
                                            </div>
                                        </template>
                                        <template v-else>
                                            <!-- This entry is the one added just now, and not saved into the database yet -->
                                            <div class="card-title">
                                                Added by:
                                                {{
                                                    party_detail.accessing_user
                                                        .full_name
                                                }}
                                                on
                                                {{
                                                    formatDatetime(
                                                        party_detail.created_at
                                                    )
                                                }}
                                                <span
                                                    class="card-tools text-danger float-end"
                                                    role="button"
                                                    @click="
                                                        remove_party_detail(
                                                            party_detail,
                                                            $event
                                                        )
                                                    "
                                                >
                                                    <i
                                                        class="bi bi-x-circle-fill"
                                                    ></i>
                                                </span>
                                            </div>
                                        </template>
                                    </div>
                                    <div
                                        class="card-body m-0 p-1 pt-3 text-secondary fst-italic"
                                    >
                                        {{ party_detail.detail }}
                                    </div>
                                    <div>
                                        <div class="list-group mt-2">
                                            <a
                                                v-for="document in party_detail.party_detail_documents"
                                                :key="document.id"
                                                class="list-group-item text-truncate"
                                                style="width: 90%"
                                                :href="document.secure_url"
                                                target="_blank"
                                                ><i
                                                    :class="
                                                        getFileIconClass(
                                                            document.file,
                                                            ['bi', 'fa-lg']
                                                        )
                                                    "
                                                ></i>
                                                {{ document.name }}</a
                                            >
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </div>
                    <div class="new_detail_div p-2 my-2">
                        <table class="table table-sm">
                            <tbody>
                                <tr>
                                    <th>New Detail</th>
                                    <td>
                                        <input
                                            v-model="new_detail_text"
                                            type="text"
                                            class="form-control detail_text"
                                            :disabled="
                                                removed_from_cp ||
                                                elementDisabled
                                            "
                                        />
                                    </td>
                                </tr>
                                <tr class="mb-3">
                                    <th>Documents</th>
                                    <td>
                                        <div
                                            v-if="
                                                removed_from_cp ||
                                                elementDisabled
                                            "
                                        >
                                            Attach document
                                        </div>
                                        <div v-else>
                                            <FileField
                                                ref="temp_document"
                                                :key="filefield_id"
                                                :readonly="readonly"
                                                name="temp_document"
                                                :is-repeatable="true"
                                                :document-action-url="
                                                    detailDocumentUrl
                                                "
                                                :replace_button_by_text="true"
                                                :temporary-document-collection-id="
                                                    temporary_document_collection_id
                                                "
                                                @update-temp-doc-coll-id="
                                                    addToTemporaryDocumentCollectionList
                                                "
                                            ></FileField>
                                        </div>
                                    </td>
                                </tr>
                                <tr>
                                    <th></th>
                                    <td class="text-end">
                                        <button
                                            class="btn btn-primary"
                                            :disabled="
                                                removed_from_cp ||
                                                elementDisabled
                                            "
                                            @click="addDetailClicked"
                                        >
                                            <i
                                                class="fa-solid fa-circle-plus"
                                            ></i>
                                            Add
                                        </button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </td>
            </tr>
        </tbody>
    </table>
</template>

<script>
import { helpers } from '@/utils/hooks';
import FileField from '@/components/forms/filefield_immediate.vue';
import { v4 as uuid } from 'uuid';

export default {
    name: 'CustomRow',
    components: {
        FileField,
    },
    props: {
        partyFullData: {
            type: Object,
            default: () => {
                return null;
            },
        },
        competitiveProcessId: {
            type: Number,
            required: true,
        },
        accessingUser: {
            type: Object,
            default: () => {
                return null;
            },
        },
        processing: {
            type: Boolean,
            default: false,
        },
        discarded: {
            type: Boolean,
            default: false,
        },
        declined: {
            type: Boolean,
            default: false,
        },
        completed: {
            type: Boolean,
            default: false,
        },
    },
    emits: ['add-detail', 'update-party-date'],
    data() {
        return {
            temporary_document_collection_id: 0,
            new_detail_text: '',
            datetimeFormat: 'DD/MM/YYYY HH:mm:ss',
            filefield_id: uuid(),
        };
    },
    computed: {
        partyFullDataComputed: function () {
            return this.partyFullData;
        },
        readonly: function () {
            return false;
        },
        existingDetail: function () {
            return false;
        },
        detailDocumentUrl: function () {
            let url = '';
            if (this.existingDetail) {
                // url = helpers.add_endpoint_join(
                //     api_endpoints.vesselownership,
                //     this.vessel.vessel_ownership.id + '/process_vessel_registration_document/'
                // )
            } else {
                url = 'temporary_document';
            }
            return url;
        },
        party_invited_at: function () {
            // For now use field `created_at` instead at `invited_at` for invitation date
            // Date of invitation is supposed to be read-only, so no point in utilizing a
            // writable field
            return this.formatDatetime(
                this.partyFullData.created_at,
                'YYYY-MM-DD'
            );
        },
        removed_from_cp: function () {
            // Returns whether this party has been removed from the Competitive Process
            return moment(this.partyFullData.removed_at).isValid()
                ? true
                : false;
        },
        elementDisabled: function () {
            // Returns whether an element is disabled
            // True while processing (saving), when discarded, declined, or completed
            return (
                this.processing ||
                this.discarded ||
                this.declined ||
                this.completed
            );
        },
    },
    created: function () {},
    methods: {
        remove_party_detail: function (item, e) {
            let vm = this;
            let $elem = $(e.target);

            $elem
                .closest('.card')
                .hide(0, function () {
                    const index = vm.partyFullData.party_details.indexOf(item);
                    if (index > -1) {
                        vm.partyFullData.party_details.splice(index, 1);
                    }
                })
                .prev('hr')
                .hide(0);
        },
        getFileIconClass: function (filepath, additional_class_names) {
            return helpers.getFileIconClass(filepath, additional_class_names);
        },
        formatDatetime: function (dt, format) {
            if (format == null) {
                format = this.datetimeFormat;
            }
            return moment(dt).format(format);
        },
        addDetailClicked: function () {
            /** On adding new party details emit an event to the
             * `competitive_process` vue component, containing
             *  the party's ID and a dictionary of the new details
             */

            let now = new Date();
            let new_party_data = {};
            let new_detail = {
                id: 0, // Should be 0, which is used to determine this as a new entry at the backend
                key: uuid(), // This is used only for vue for-loop
                created_at: now,
                detail: this.new_detail_text,
                temporary_document_collection_id:
                    this.temporary_document_collection_id,
                created_by_id: this.accessingUser.id,
                created_by: this.accessingUser, // added to prevent vue renderer crash
                accessing_user: this.accessingUser,
                party_detail_documents: this.$refs.temp_document.documents,
            };
            new_party_data[this.partyFullData.id] = new_detail;
            this.$emit('add-detail', new_party_data);
        },
        addToTemporaryDocumentCollectionList(temp_doc_id) {
            this.temporary_document_collection_id = temp_doc_id;
        },
        partyDateChanged: function (e, date_field) {
            if (!(date_field in this.partyFullData)) {
                return;
            }
            let new_date = e.target.value;
            if (new_date === '') {
                // Set date to `null` if form field has been cleared
                new_date = null;
            } else if (date_field === 'removed_at') {
                // Clear detail text box when `removed_at` is set
                this.new_detail_text = '';
            }

            this.$emit('update-party-date', {
                party_id: this.partyFullData.id,
                date_field: date_field,
                new_date: new_date,
            });
        },
    },
};
</script>
<style scoped>
.party_detail_table th,
td {
    border: none;
}

.new_detail_div {
    border: 1px solid lightgray;
    border-radius: 0.25em;
    background-color: white;
}

.details_box {
    /* border: 1px solid lightgray; */
    border-radius: 0.25em;
    background-color: whitesmoke;
}

.detail_wrapper {
    position: relative;
}
</style>

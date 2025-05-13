<template>
    <div class="">
        <div class="card card-default">
            <div class="card-header">Submission</div>
            <div class="card-body card-collapse">
                <div class="row">
                    <div class="col-sm-12">
                        <strong>Submitted by</strong><br />
                        {{ submitter_first_name }}
                        {{ submitter_last_name }}
                    </div>
                    <div class="col-sm-12 top-buffer-s">
                        <strong>Lodged on</strong><br />
                        {{ formatDate(lodgement_date) }}
                    </div>
                    <div v-if="showingProposal" class="col-sm-12 top-buffer-s">
                        <div class="row">
                            <div class="panel-body panel-collapse">
                                <div class="scrollable-div">
                                    <div style="float: left; width: 80%">
                                        <table class="small text-xsmall">
                                            <thead>
                                                <tr>
                                                    <th>Lodgement</th>
                                                    <th>
                                                        <span class="ml-2 mr-2"
                                                            >Date</span
                                                        >
                                                    </th>
                                                    <th>
                                                        <span class="ml-2"
                                                            >Action</span
                                                        >
                                                    </th>
                                                </tr>
                                            </thead>
                                            <tr
                                                v-for="(
                                                    p, i
                                                ) in lodgement_versions()"
                                                :key="versionKey(p.revision_id)"
                                            >
                                                <td
                                                    :class="
                                                        p.revision_comment ==
                                                            '' && i > 0
                                                            ? 'text-secondary'
                                                            : ''
                                                    "
                                                    class="w-50"
                                                >
                                                    <span class="mr-2"
                                                        >{{
                                                            p.lodgement_number
                                                        }}-{{
                                                            p.lodgement_sequence
                                                        }}</span
                                                    >
                                                </td>
                                                <td
                                                    :class="
                                                        p.revision_comment ==
                                                            '' && i > 0
                                                            ? 'text-secondary'
                                                            : ''
                                                    "
                                                    class="w-25"
                                                >
                                                    <span class="ml-2 mr-2">{{
                                                        formatDate(
                                                            p.lodgement_date,
                                                            (format = 'DD/MM')
                                                        )
                                                    }}</span>
                                                </td>
                                                <td class="w-25">
                                                    <div
                                                        v-if="
                                                            p.revision_id !=
                                                            current_lodgement_version.revision_id
                                                        "
                                                        class="py-0"
                                                    >
                                                        <!-- Note: Full django reversion UI support has been pushed back to phase 2..
                                                             Add compare and/or view button links to submission versions (see: internal/018) -->
                                                        <span class="ml-2">
                                                            <a
                                                                v-if="debug()"
                                                                :class="
                                                                    p.revision_comment ==
                                                                        '' &&
                                                                    i > 0
                                                                        ? 'text-secondary'
                                                                        : ''
                                                                "
                                                                class="actionBtn pull-right text-decoration-none"
                                                                style="
                                                                    cursor: pointer;
                                                                "
                                                                @click.prevent="
                                                                    compareRevision(
                                                                        p
                                                                    )
                                                                "
                                                            >
                                                                Compare
                                                            </a>
                                                            <span
                                                                v-else
                                                                :class="
                                                                    p.revision_comment ==
                                                                        '' &&
                                                                    i > 0
                                                                        ? 'text-secondary'
                                                                        : ''
                                                                "
                                                            >
                                                                (to do)
                                                            </span>
                                                        </span>
                                                    </div>
                                                    <div v-else class="py-0">
                                                        <span class="ml-2"
                                                            >Viewing</span
                                                        >
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'SubmissionComponent',
    props: {
        submitter_first_name: {
            type: String,
            default: '',
        },
        submitter_last_name: {
            type: String,
            default: '',
        },
        lodgement_date: {
            type: String,
            default: null,
        },
        showingProposal: {
            type: Boolean,
        },
        canSeeSubmission: {
            type: Boolean,
        },
        proposal: {},
    },
    emits: ['revision-to-display'],
    data: function () {
        return {};
    },
    computed: {
        /** Writable computed lodgement version revision object */
        lodgementVersion: {
            get() {
                return this.current_lodgement_version;
            },
            set(version) {
                this.current_lodgement_version = version;
                this.$emit('revision-to-display', version);
            },
        },
    },
    created: function () {
        this.current_lodgement_version = this.proposal.lodgement_versions[0];
        this.proposal;
        this.showingProposal;
        this.canSeeSubmission;
    },
    methods: {
        formatDate: function (data, format = 'DD/MM/YYYY HH:mm:ss') {
            return data ? moment(data).format(format) : '';
        },
        compareRevision: function (revision) {
            this.lodgementVersion = revision;
        },
        versionKey: function (revision_id) {
            /** Create dynamic viewing-aware table keys for submissions */

            // A key in the form `1732-0` or `1732-1`
            let key = `${revision_id}-${
                revision_id == this.current_lodgement_version.revision_id
                    ? 0
                    : 1
            }`;
            return key;
        },
        debug: function () {
            if (this.$route.query.debug) {
                return this.$route.query.debug === 'true';
            }
            return false;
        },
        lodgement_versions: function () {
            let versions = this.debug()
                ? this.proposal.all_lodgement_versions
                : this.proposal.lodgement_versions;
            // The version at position 0 is the current one.
            // Increment its sequence number in the frontend if identical to the prior version
            if (
                versions.length > 1 &&
                versions[0].lodgement_sequence == versions[1].lodgement_sequence
            ) {
                versions[0].lodgement_sequence++;
            }

            return versions;
        },
    },
};
</script>
<style scoped>
.scrollable-div {
    height: 100px;
    white-space: nowrap;
    overflow-y: scroll;
    /* font-size:13px; */
}
.scrollable-div::-webkit-scrollbar {
    width: 12px;
}
.scrollable-div::-webkit-scrollbar-track {
    -webkit-box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.3);
    border-radius: 10px;
}
.scrollable-div::-webkit-scrollbar-thumb {
    border-radius: 10px;
    -webkit-box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.5);
}
</style>

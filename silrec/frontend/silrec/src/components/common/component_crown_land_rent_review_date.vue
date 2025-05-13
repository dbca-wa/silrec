<template>
    <div class="row">
        <div class="col-sm-4">
            <button
                class="btn btn-primary btn-sm"
                @click.prevent="addAnotherDateClicked"
            >
                <i class="fa fa-add"></i> Add Crown Land Rent Review Date
            </button>
        </div>
        <div class="col-sm-8">
            <template v-for="item in reviewDatesComputed" :key="item.key">
                <div class="review-date mb-2 d-flex">
                    <div class="pe-3">
                        <input
                            v-model="item.review_date"
                            type="date"
                            class="form-control form-control-sm w-auto"
                            placeholder="DD/MM/YYYY"
                            :disabled="item.readonly"
                            required
                        />
                    </div>
                    <div v-if="deletable(item)" class="">
                        <span
                            class="text-danger"
                            role="button"
                            @click="removeARow(item, $event)"
                        >
                            <i class="bi bi-x-circle-fill"></i
                        ></span>
                    </div>
                </div>
            </template>
        </div>
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';

export default {
    name: 'CrownLandRentReviewDate',
    props: {
        reviewDates: {
            type: Array,
            required: true,
        },
    },
    emits: ['updateReviewDates'],
    data: function () {
        return {
            temp_date: null,
        };
    },
    computed: {
        reviewDatesComputed: {
            get() {
                return this.reviewDates;
            },
            set(value) {
                this.$emit('updateReviewDates', value);
            },
        },
    },
    methods: {
        deletable: function (item) {
            if (item.id === 0 || !item.readonly)
                // If the date is a newly added one, or not readonly, it is deletable.
                return true;
            return false;
        },
        addAnotherDateClicked: function () {
            this.reviewDatesComputed.push({
                id: 0,
                key: uuid(),
                review_date: null,
                readonly: false,
            });
        },
        removeARow: function (item, e) {
            let vm = this;
            let $elem = $(e.target);

            // Fade out a row
            $elem.closest('.review-date').remove();
            if (item.id === 0) {
                vm.reviewDatesComputed = vm.reviewDatesComputed.filter(
                    (i) => i.key !== item.key
                );
            } else {
                // When a row is the one already stored in the database, flag it to be deleted.
                item.to_be_deleted = true;
            }
        },
    },
};
</script>

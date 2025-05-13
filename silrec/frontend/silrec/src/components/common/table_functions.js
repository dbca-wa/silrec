import { createApp, h, reactive, toRefs } from 'vue';
import CustomRow from '@/components/common/custom_row.vue';

/**
 * Returns table row and cell jQuery objects for a clicked data table expander
 * @param {Proxy} vm
 * @param {Object} obj Expander HTML element
 * @returns jQuery objects for table row and first cell, or an empty list if not expandable
 */
function tr_first_td(vm, obj) {
    let td_link = $(obj);
    if (
        !(
            td_link.hasClass(vm.td_expand_class_name) ||
            td_link.hasClass(vm.td_collapse_class_name)
        )
    ) {
        // This row is not configured as expandable row (at the rowCallback)
        return [];
    }
    // Get <tr> element as jQuery object
    let tr = td_link.closest('tr');
    let first_td = tr.children().first();

    return [tr, first_td];
}

/**
 * Collapses an expanded table row
 * @param {Proxy} vm
 * @param {Object} tr Table row
 * @param {Object} first_td First cell in row
 */
function collapse_row(vm, tr, first_td) {
    let nextElem = tr.next();
    // Collapse
    if (nextElem.is('tr') & nextElem.hasClass(vm.expandable_row_class_name)) {
        // Details row is already shown.  Remove it.
        nextElem.hide(0, function () {
            nextElem.remove();
        });
    }
    // Change icon class name to vm.td_expand_class_name
    first_td
        .removeClass(vm.td_collapse_class_name)
        .addClass(vm.td_expand_class_name);
}

function getGroupsHtml(groups) {
    let groups_html = 'N/A';
    if (groups && groups.length > 0) {
        groups_html = '';
        for (let i = 0; i < groups.length; i++) {
            groups_html +=
                '<span class="badge bg-primary">' + groups[i] + '</span>&nbsp;';
        }
    }
    return groups_html;
}

export function expandToggle(vm, obj) {
    let [tr, first_td] = tr_first_td(vm, obj);
    if (typeof tr === 'undefined' || typeof first_td === 'undefined') {
        return;
    }

    if (first_td.hasClass(vm.td_expand_class_name)) {
        // Expand
        // Get group names from the row data
        let $row = vm.$refs.application_datatable.vmDataTable.row(tr);
        let full_data = $row.data();
        let site_name = full_data.site_name;
        let groups = full_data.groups.map(({ name }) => name);

        if (!site_name) {
            site_name = 'N/A';
        }

        let groups_html = getGroupsHtml(groups);

        // If we don't need to retrieve the data from the server, follow the code below
        let contents = `<div><strong>Site Name: </strong>${site_name}</div><div><strong>Groups: </strong>${groups_html}</div>`;
        let details_elem = $(
            '<tr class="' +
                vm.expandable_row_class_name +
                '"><td colspan="' +
                vm.number_of_columns +
                '">' +
                contents +
                '</td></tr>'
        );
        details_elem.hide(0);
        details_elem.insertAfter(tr);
        details_elem.show();

        // Change icon class name to vm.td_collapse_class_name
        first_td
            .removeClass(vm.td_expand_class_name)
            .addClass(vm.td_collapse_class_name);
    } else {
        collapse_row(vm, tr, first_td);
    }
}

// used by competitive process
export function expandToggleCP(vm, obj) {
    let [tr, first_td] = tr_first_td(vm, obj);
    if (typeof tr === 'undefined' || typeof first_td === 'undefined') {
        return;
    }

    let $row = vm.$refs.competitive_process_datatable.vmDataTable.row(tr);
    let full_data = $row.data();
    let site_name = full_data.site_name;
    let groups = full_data.groups.map(({ name }) => name);

    if (first_td.hasClass(vm.td_expand_class_name)) {
        if (!site_name) {
            site_name = 'N/A';
        }

        let groups_html = getGroupsHtml(groups);

        // Expand
        // If we don't need to retrieve the data from the server, follow the code below
        let elem_site = '<div>Site name: ' + site_name + '</div>';
        let elem_group = `<div>Groups: ${groups_html}</div>`;
        let elem_applicant = '';
        if (full_data.registration_of_interest) {
            elem_applicant =
                '<div>Applicant: ' +
                full_data.registration_of_interest.relevant_applicant_name +
                '</div>';
        }
        let contents = elem_site + elem_group + elem_applicant;
        let details_elem = $(
            '<tr class="' +
                vm.expandable_row_class_name +
                '"><td colspan="' +
                vm.number_of_columns +
                '">' +
                contents +
                '</td></tr>'
        );
        details_elem.hide(0);
        details_elem.insertAfter(tr);
        details_elem.show();

        // Change icon class name to vm.td_collapse_class_name
        first_td
            .removeClass(vm.td_expand_class_name)
            .addClass(vm.td_collapse_class_name);
    } else {
        collapse_row(vm, tr, first_td);
    }
}

// used by `table_parties.vue`
export function expandToggleParties(vm, obj) {
    let tr = $(obj).parents('tr').first();
    if (!tr.hasClass('odd') && !tr.hasClass('even')) {
        return;
    }

    // Get full data of this row
    let $row = vm.$refs.parties_datatable.vmDataTable.row(tr);
    let full_data = $row.data();

    if (full_data.expanded) {
        tr.find('button').html('Show Details');
        // Collapse
        let siblings = tr.next('tr.' + vm.expandable_row_class_name);
        siblings.hide(0, function () {
            siblings.remove();

            // Hide child row, where hidden columns are
            $row.child.hide(0);
            // Toggle flag
            full_data.expanded = false;

            if (full_data.id in vm.custom_row_apps) {
                vm.custom_row_apps[full_data.id].unmount();
                vm.custom_row_apps[full_data.id] = undefined;
            }
        });
    } else {
        tr.find('button').html('Hide Details');
        // Expand
        let details_elem = $(
            '<tr class="' +
                vm.expandable_row_class_name +
                '"><td id="custom_row_' +
                full_data.id +
                '"></td></tr>'
        );
        details_elem.hide(0);
        details_elem.insertAfter(tr);
        vm.updateCustomRowColSpan();

        // -----------------------
        // Add vue component dynamically
        // -----------------------
        // Configure event listener (Ref: https://stackoverflow.com/questions/67516974/vue3-listen-to-event-from-dynamically-created-child-component-on-replacement)
        // Whoever did this made a mistake, but I guess we have to live with our mistakes.
        const props = {
            partyFullData: full_data,
            competitiveProcessId: vm.competitiveProcessId,
            accessingUser: vm.accessingUser,
            processing: vm.processing,
            discarded: vm.discarded,
            declined: vm.declined,
            completed: vm.completed,
        };
        // Make the props reactive
        const react = reactive(props);
        // Keep an instance of this custom row
        let instance;
        let custom_row_app = createApp({
            setup() {
                return {
                    ...toRefs(react),
                };
            },
            created() {
                // Get a reference to this custom row instance
                instance = this;
            },
            // Render the dynamically added custom row and catch
            // events of newly added details and emit them to the
            // `competitive_process` vue files
            render: () =>
                h(CustomRow, {
                    ...react,
                    onAddDetail: (e) => vm.$emit('add-detail', e),
                    onUpdatePartyDate: (e) => vm.$emit('update-party-date', e),
                }),
        });
        custom_row_app.mount('#custom_row_' + full_data.id);
        // -----------------------

        // Store custom_row_app in order to unmount when being hidden
        // full_data.custom_row_app = custom_row_app
        custom_row_app['instance'] = instance;
        vm.custom_row_apps[full_data.id] = custom_row_app;

        details_elem.show();

        // Show child row, where hidden columns are
        $row.child.show();
        // Toggle flag
        full_data.expanded = true;
    }
}

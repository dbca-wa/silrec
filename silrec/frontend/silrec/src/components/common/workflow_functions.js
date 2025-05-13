import { api_endpoints, helpers, utils } from '@/utils/hooks';
import '../../../../../static/silrec/css/workflow.css';

/**
 * Sends a referral reminder to the referrer
 * @param {number} _id The referral ID
 * * @param {string} user The referrer's username
 */
export async function remindReferral(api_endpoint, _id, user) {
    fetch(helpers.add_endpoint_json(api_endpoint, _id + '/remind'))
        .then(async (response) => {
            if (!response.ok) {
                return response.json().then((json) => {
                    throw new Error(json);
                });
            } else {
                return response.json();
            }
        })
        .then(() => {
            swal.fire({
                title: 'Referral Reminder',
                text: 'A reminder has been sent to ' + user,
                icon: 'success',
                // Have swal2 popovers placed above bootstrap popovers
                customClass: {
                    container: 'swal2-popover',
                },
            });
        })
        .catch((error) => {
            swal.fire({
                title: 'Proposal Error',
                text: error['message'],
                icon: 'error',
                customClass: {
                    container: 'swal2-popover',
                },
            });
        });
}

/**
 * Recalls a referral from the referrer
 * @param {number} _id The referral ID
 * * @param {string} user The referrer's username
 */
export async function recallReferral(api_endpoint, _id, user) {
    let vm = this;

    const _loading = swal.fire({
        icon: 'info',
        title: 'Loading...',
        showConfirmButton: false,
        allowOutsideClick: false,
        allowEscapeKey: false,
        didOpen: async () => {
            swal.showLoading();
        },
        customClass: {
            container: 'swal2-popover',
        },
    });

    await fetch(helpers.add_endpoint_json(api_endpoint, _id + '/recall'))
        .then(async (response) => {
            if (!response.ok) {
                return await response.json().then((json) => {
                    throw new Error(json);
                });
            } else {
                return response.json();
            }
        })
        .then(async (response) => {
            vm.switchStatus(response.processing_status_id); // 'with_assessor'
            if (typeof vm['table'] !== 'undefined') {
                // Reload the Show Referrals Popover table if exists
                vm.table.ajax.reload();
            }
            _loading.hideLoading();
            _loading.update({
                showConfirmButton: true,
                title: 'Referral Recall',
                text: 'The referral has been recalled from ' + user,
                icon: 'success',
            });
        })
        .catch((error) => {
            _loading.hideLoading();
            _loading.update({
                showConfirmButton: true,
                title: 'Proposal Error',
                text: error['message'],
                icon: 'error',
            });
        })
        .finally(() => {
            // _loading.close();
        });
}

/**
 * Resends a referral reminder to the referrer
 * @param {number} _id The referral ID
 * * @param {string} user The referrer's username
 */
export async function resendReferral(api_endpoint, _id, user) {
    let vm = this;
    await fetch(helpers.add_endpoint_json(api_endpoint, _id + '/resend'))
        .then(async (response) => {
            if (!response.ok) {
                return await response.json().then((json) => {
                    throw new Error(json);
                });
            } else {
                return response.json();
            }
        })
        .then(async (response) => {
            vm.switchStatus(response.processing_status_id); // 'with_referral'
            if (typeof vm['table'] !== 'undefined') {
                // Reload the Show Referrals popover table if exists
                vm.table.ajax.reload();
            }

            swal.fire({
                title: 'Referral Resent',
                text: 'The referral has been resent to ' + user,
                icon: 'success',
                customClass: {
                    container: 'swal2-popover',
                },
            });
        })
        .catch((error) => {
            swal.fire({
                title: 'Proposal Error',
                text: error['message'],
                icon: 'error',
                customClass: {
                    container: 'swal2-popover',
                },
            });
        });
}

/**
 * Updates a list of, e.g. selected items, with `id` .
 * @param {int} id The id of the item to add or remove from the list.
 * @param {Array} list The list to add to.
 * @param {Array} available_items A list of available items of which `id` is a member.
 * @param {Boolean} remove Whether to remove the item from the list. Default false.
 */
export function updateIdListFromAvailable(id, list, available_items, remove) {
    if (!remove) {
        remove = false;
    }

    let found = list.find((element) => element.id === parseInt(id));

    if (!found) {
        let item = available_items.find(
            (element) => element.id === parseInt(id)
        );
        if (!item) {
            console.warn(
                `Selected item with id ${id} not found in available items.`
            );
            return false;
        }
        list.push(item);
        return list;
    }

    if (found && remove) {
        list = list.filter((element) => element.id !== parseInt(id));
        return list;
    }
    return false;
}

/**
 * Declines a proposal.
 * @param {object} proposal A proposal object
 * @returns an api query Promise
 */
export async function declineProposal(proposal) {
    let proposal_id = proposal.id;

    return swal
        .fire({
            title: `Confirm Decline of Proposal ${proposal.lodgement_number}`,
            text: 'Are you sure you want to decline this proposal?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Decline Proposal',
            confirmButtonColor: '#dc3545',
            reverseButtons: true,
        })
        .then(async (result) => {
            if (result.isConfirmed) {
                const requestOptions = {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                };
                // // Queries the discard proposal endpoint
                return utils.fetchUrl(
                    api_endpoints.decline_proposal(proposal_id),
                    requestOptions
                );
            } else {
                return null;
            }
        });
}

/**
 * Discard a proposal.
 * @param {object} proposal A proposal object
 * @returns an api query Promise
 */
export async function discardProposal(proposal_id, lodgement_number) {
    return swal
        .fire({
            title: `Confirm Discard of Proposal ${lodgement_number}`,
            text: 'Are you sure you want to discard this proposal?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Discard Proposal',
            confirmButtonColor: '#dc3545',
        })
        .then(async (result) => {
            if (result.isConfirmed) {
                const requestOptions = {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                };
                // // Queries the discard proposal endpoint
                return utils.fetchUrl(
                    api_endpoints.discard_proposal(proposal_id),
                    requestOptions
                );
            } else {
                return null;
            }
        });
}

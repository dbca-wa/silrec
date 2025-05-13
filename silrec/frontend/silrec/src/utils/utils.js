import { constants, api_endpoints, helpers } from '@/utils/hooks';

export default {
    fetchCountries: function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.countries)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchRequestUserID: function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.request_user_id)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchAccount: function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.users_api + 'request_user_account/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchLedgerAccount: function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.account_details)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchOrganisations: function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.organisations)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchOrganisation: function (id) {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.organisations + id + '/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchOrganisationAddress: function (id) {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.organisations + id + '/get_org_address/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    let formatted_data = {};
                    formatted_data = {
                        postal_address: {
                            postal_line1: data.postal_address.line1,
                            postal_locality: data.postal_address.locality,
                            postal_state: data.postal_address.state,
                            postal_postcode: data.postal_address.postcode,
                            postal_country: data.postal_address.country,
                        },
                        billing_address: {
                            billing_line1: data.billing_address.line1,
                            billing_locality: data.billing_address.locality,
                            billing_state: data.billing_address.state,
                            billing_postcode: data.billing_address.postcode,
                            billing_country: data.billing_address.country,
                        },
                    };
                    resolve(formatted_data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchOrganisationRequests: function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.organisation_requests + 'no-pagination/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchOrganisationPermissions: function (id) {
        return new Promise((resolve, reject) => {
            fetch(helpers.add_endpoint_join(api_endpoints.my_organisations, id))
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchLGAsKeyValueList: function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.lgas + 'key-value-list/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchDistricts: function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.districts + 'no-pagination/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchGroupsKeyValueList: function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.groups + 'key-value-list/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchApprovalTypes: async function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.approval_types_dict)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchKeyValueLookup: function (endpoint, query) {
        return new Promise((resolve, reject) => {
            fetch(endpoint + 'key-value-list/?term=' + query)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchActsKeyValueList: function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.acts + 'key-value-list/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchVestingsKeyValueList: function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.vestings + 'key-value-list/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    fetchInvoiceTransactions: function (invoice_id) {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.invoices + `${invoice_id}/transactions/`)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        reject(error);
                    }
                    resolve(data);
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    reject(error);
                });
        });
    },
    /**
     * Generic function to fetch data from an endpoint
     * @param {String} url The url endpoint to fetch data from
     * @param {Object} options The options to pass to the fetch function (optional)
     * @returns a Promise
     * @todo Items for future:
     * 1) Best practice way to deal with the resolve and reject from calling code.
     * 2) Does our !response.ok block act appropriately for all possible error response formats that django and drf can respond with.
     * 3) Doesn't handle the fact that 500 errors from django often aren't formatted as json. Therefor is falling
     *      into the network error catch block for 500 errors that don't send a valid response.
     */
    fetchUrl: async function (url, options) {
        return new Promise((resolve, reject) => {
            let f = options === undefined ? fetch(url) : fetch(url, options);
            f.then(async (response) => {
                const data = await response.json();
                if (!response.ok) {
                    let error =
                        (data.constructor.name === 'Array' && data) ||
                        (data && data.message) ||
                        (data && data.errors[0]?.detail) || // This is for DRF validation errors
                        response.statusText;
                    console.error(error);
                    reject(error);
                }
                resolve(data);
            }).catch((error) => {
                console.error(`There was an error fetching from ${url}`, error);
                error = new Error(constants.ERRORS.NETWORK_ERROR);
                reject(error);
            });
        });
    },
};

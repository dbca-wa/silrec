import { api_endpoints } from '@/utils/hooks';

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
    fetchProfile: function () {
        return new Promise((resolve, reject) => {
            fetch(api_endpoints.profile)
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
};

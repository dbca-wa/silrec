import { api_endpoints } from '@/utils/hooks';

export default {
    data() {
        return {
            currentUser: null,
            permissionsLoaded: false,
        };
    },
    computed: {
        isReadOnlyUser() {
            return this.currentUser && this.currentUser.is_readonly_user;
        },
    },
    methods: {
        async fetchCurrentUser() {
            try {
                const response = await fetch(api_endpoints.users + 'current/');
                const data = await response.json();
                this.currentUser = data;
                this.permissionsLoaded = true;
                return data;
            } catch (error) {
                console.error('Failed to fetch current user:', error);
                this.permissionsLoaded = true;
                return null;
            }
        },
    },
};

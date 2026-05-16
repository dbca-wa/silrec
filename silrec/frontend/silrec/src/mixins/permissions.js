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
        isAssessorUser() {
            return (
                this.currentUser &&
                this.currentUser.groups &&
                this.currentUser.groups.includes('Assessor')
            );
        },
        isReviewerUser() {
            return (
                this.currentUser &&
                this.currentUser.groups &&
                this.currentUser.groups.includes('Reviewer')
            );
        },
    },
    methods: {
        canEditForStatus(processingStatus) {
            if (this.isReadOnlyUser) return false;
            if (this.isReviewerUser) {
                return processingStatus === 'with_reviewer';
            }
            return true;
        },
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

import { api_endpoints } from '@/utils/hooks';

export default {
    data() {
        return {
            validationRules: [],
            validationErrors: [],
            validationLoaded: false,
        };
    },
    methods: {
        async fetchValidationRules(modelName) {
            try {
                const url = `${api_endpoints.form_validation_rules}?model=${encodeURIComponent(modelName)}`;
                const response = await fetch(url);
                if (response.ok) {
                    this.validationRules = await response.json();
                }
                this.validationLoaded = true;
            } catch (error) {
                console.error('Failed to fetch validation rules:', error);
                this.validationLoaded = true;
            }
        },

        validateFormData(formData) {
            this.validationErrors = [];

            for (const rule of this.validationRules) {
                if (!rule.is_active) continue;

                if (rule.status_field && rule.status_values) {
                    const statusValue = formData[rule.status_field];
                    const allowedStatuses = rule.status_values
                        .split(',')
                        .map((s) => s.trim());
                    if (
                        statusValue &&
                        !allowedStatuses.includes(String(statusValue))
                    ) {
                        continue;
                    }
                }

                if (rule.is_required) {
                    const value = formData[rule.field_name];
                    if (
                        value === null ||
                        value === undefined ||
                        value === '' ||
                        (typeof value === 'string' && value.trim() === '') ||
                        (Array.isArray(value) && value.length === 0)
                    ) {
                        const label = rule.field_label || rule.field_name;
                        this.validationErrors.push({
                            field: rule.field_name,
                            message: `${label} is required`,
                            rule: rule,
                        });
                    }
                }
            }

            return this.validationErrors.length === 0;
        },

        clearValidationErrors() {
            this.validationErrors = [];
        },
    },
};

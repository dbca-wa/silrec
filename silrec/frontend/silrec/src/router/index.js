import { createRouter, createWebHistory } from 'vue-router';
import Account from '@/components/user/account.vue';
import external_routes from '@/components/external/routes';
import internal_routes from '@/components/internal/routes';

var NotFoundComponent = null;

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/:pathMatch(.*)',
            component: NotFoundComponent,
        },
        {
            path: '/firsttime',
            name: 'first-time',
            component: Account,
        },
        {
            path: '/ledger-ui/accounts',
            name: 'account',
            component: Account,
        },
        external_routes,
        internal_routes,
    ],
});

export default router;

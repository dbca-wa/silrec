import { createRouter, createWebHistory } from 'vue-router';
import internal_routes from '@/components/internal/routes';

var NotFoundComponent = null;

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/:pathMatch(.*)',
            component: NotFoundComponent,
        },
        internal_routes,
    ],
});

export default router;

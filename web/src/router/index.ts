import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../pages/Home.vue'),
    },
    {
      path: '/optimize',
      name: 'optimize',
      component: () => import('../pages/Optimize.vue'),
    },
    {
      path: '/result',
      name: 'result',
      component: () => import('../pages/Result.vue'),
    },
  ],
})

export default router

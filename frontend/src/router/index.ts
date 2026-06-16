import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/pages/HomePage.vue'
import HistoryPage from '@/pages/HistoryPage.vue'
import CorrectionsPage from '@/pages/CorrectionsPage.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomePage,
  },
  {
    path: '/history',
    name: 'history',
    component: HistoryPage,
  },
  {
    path: '/corrections',
    name: 'corrections',
    component: CorrectionsPage,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

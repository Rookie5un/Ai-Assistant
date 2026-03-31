import { createRouter, createWebHistory } from 'vue-router'

import AppShell from '../components/AppShell.vue'
import { useAuthStore } from '../stores/auth'
import AssistantsView from '../views/AssistantsView.vue'
import ChatView from '../views/ChatView.vue'
import KnowledgeView from '../views/KnowledgeView.vue'
import LoginView from '../views/LoginView.vue'
import OverviewView from '../views/OverviewView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/app/overview',
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: {
        title: 'Sign in',
      },
    },
    {
      path: '/app',
      component: AppShell,
      meta: {
        requiresAuth: true,
      },
      children: [
        {
          path: 'overview',
          name: 'overview',
          component: OverviewView,
          meta: {
            title: 'Workspace overview',
            eyebrow: 'System posture',
          },
        },
        {
          path: 'chat',
          name: 'chat',
          component: ChatView,
          meta: {
            title: 'Live conversation',
            eyebrow: 'Primary workspace',
          },
        },
        {
          path: 'assistants',
          name: 'assistants',
          component: AssistantsView,
          meta: {
            title: 'Assistants',
            eyebrow: 'Prompt and model setup',
          },
        },
        {
          path: 'knowledge',
          name: 'knowledge',
          component: KnowledgeView,
          meta: {
            title: 'Knowledge bases',
            eyebrow: 'Files and ingestion',
          },
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login' }
  }

  if (to.name === 'login' && authStore.isAuthenticated) {
    return { name: 'overview' }
  }

  return true
})

export default router

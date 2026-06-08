import { createRouter, createWebHistory } from 'vue-router'
import { storage } from '@/utils/storage'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { title: '登录', guest: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/users/UserView.vue'),
        meta: { title: '用户管理', icon: 'User' }
      },
      {
        path: 'algo',
        name: 'Algo',
        component: () => import('@/views/quiz/QuizView.vue'),
        meta: { title: '算法管理', icon: 'EditPen' }
      },
      {
        path: 'forum',
        name: 'Forum',
        component: () => import('@/views/forum/ForumView.vue'),
        meta: { title: '论坛管理', icon: 'ChatDotRound' }
      },
      {
        path: 'ai-chat',
        name: 'AiChat',
        component: () => import('@/views/ai/AiChatView.vue'),
        meta: { title: 'AI 助手', icon: 'MagicStick' }
      },
      {
        path: 'enrollment',
        redirect: '/enrollment/application'
      },
      {
        path: 'enrollment/application',
        name: 'EnrollmentApplication',
        component: () => import('@/views/enrollment/EnrollmentView.vue'),
        meta: { title: '报名管理', icon: 'DocumentChecked' }
      },
      {
        path: 'enrollment/interview',
        name: 'EnrollmentInterview',
        component: () => import('@/views/enrollment/InterviewView.vue'),
        meta: { title: '面试管理', icon: 'ChatLineRound' }
      },
      {
        path: 'enrollment/direction',
        name: 'EnrollmentDirection',
        component: () => import('@/views/enrollment/DirectionView.vue'),
        meta: { title: '方向选择', icon: 'Compass' }
      }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.path === '/algo') {
    window.open('http://localhost:8066/algo/admin', '_blank')
    return next(false)
  }

  const token = storage.get('token')
  const user = storage.get('user')

  if (to.meta.title) {
    document.title = `${to.meta.title} - Open436 Admin`
  }

  if (to.meta.guest) {
    if (token && user) return next('/dashboard')
    return next()
  }

  if (!token || !user) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  if (!user || user.role !== 'admin') {
    storage.clear()
    return next('/login')
  }

  next()
})

export default router

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
        path: 'homepage',
        redirect: '/homepage/about'
      },
      ...['about', 'experiences', 'technologies', 'works', 'honors', 'feedbacks'].map(module => ({
        path: `homepage/${module}`,
        name: `Homepage${module}`,
        component: () => import('@/views/dashboard/HomepageView.vue'),
        props: { module },
        meta: { title: '首页管理', icon: 'Monitor' }
      })),
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/users/UserView.vue'),
        meta: { title: '用户管理', icon: 'User' }
      },
      // Quiz 习题管理：dev 构建（mock 后端）有效；生产构建路由被
      // beforeEach 直接跳到 /dashboard，避免展示必然 404 的界面。
      {
        path: 'quiz',
        name: 'Quiz',
        component: () => import('@/views/quiz/QuizView.vue'),
        meta: { title: '习题管理', icon: 'EditPen', devOnly: true }
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
        path: 'enrollment/interview/edit/:enrollmentId',
        name: 'InterviewEdit',
        component: () => import('@/views/enrollment/InterviewEditView.vue'),
        meta: { title: '编辑面试信息', hidden: true }
      },
      {
        path: 'enrollment/assignment',
        name: 'EnrollmentAssignment',
        component: () => import('@/views/enrollment/AssignmentView.vue'),
        meta: { title: '作业分发', icon: 'Promotion' }
      },
      {
        path: 'enrollment/collection',
        name: 'EnrollmentCollection',
        component: () => import('@/views/enrollment/CollectionView.vue'),
        meta: { title: '作业收集', icon: 'FolderChecked' }
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
    // 同源 /algo 路径：开发由 Vite 代理到 :8066，生产由 Admin nginx 代理到 hoj-vue
    window.open('/algo/admin', '_blank')
    return next(false)
  }

  // 生产构建：devOnly 路由（Quiz 算法管理）直接跳到 dashboard，
  // 不暴露必然 404 的界面。dev 构建保留路由以便 mock 调试。
  if (to.meta.devOnly && import.meta.env.PROD) {
    return next('/dashboard')
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

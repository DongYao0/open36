import { createRouter, createWebHistory } from 'vue-router'
import { storage } from '@/utils/storage'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/Home.vue'), meta: { title: '首页' } },
  {
    path: '/forum',
    component: () => import('@/views/forum/ForumLayout.vue'),
    children: [
      { path: '', name: 'Forum', component: () => import('@/views/forum/Forum.vue'), meta: { title: '论坛' } },
      { path: 'post/new', name: 'PostNew', component: () => import('@/views/forum/PostNew.vue'), meta: { title: '发布新帖', auth: true, write: true } },
      { path: 'post/:id', name: 'PostDetail', component: () => import('@/views/forum/PostDetail.vue'), meta: { title: '帖子详情' } },
      { path: 'search', name: 'Search', component: () => import('@/views/forum/Search.vue'), meta: { title: '搜索' } },
      { path: 'favorites', name: 'Favorites', component: () => import('@/views/forum/Favorites.vue'), meta: { title: '我的收藏', auth: true, write: true } },
    ]
  },
  {
    path: '/resources',
    component: () => import('@/views/resources/ResourcesLayout.vue'),
    children: [
      { path: '', name: 'Resources', component: () => import('@/views/resources/Resources.vue'), meta: { title: '资源分享' } },
      { path: 'new', name: 'ResourceNew', component: () => import('@/views/resources/ResourceNew.vue'), meta: { title: '分享资源', auth: true, write: true } },
      { path: ':id', name: 'ResourceDetail', component: () => import('@/views/resources/ResourceDetail.vue'), meta: { title: '资源详情' } },
    ]
  },
  {
    path: '/announcements',
    component: () => import('@/views/announcements/AnnouncementsLayout.vue'),
    children: [
      { path: '', name: 'Announcements', component: () => import('@/views/announcements/Announcements.vue'), meta: { title: '公告通知' } },
      { path: ':id', name: 'AnnouncementDetail', component: () => import('@/views/announcements/AnnouncementDetail.vue'), meta: { title: '公告详情' } },
    ]
  },
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { title: '登录' } },
  { path: '/register', name: 'Register', component: () => import('@/views/Register.vue'), meta: { title: '注册' } },
  { path: '/quiz', name: 'Quiz', component: () => import('@/views/Quiz.vue'), meta: { title: '算法' } },
  { path: '/enroll', name: 'Enroll', component: () => import('@/views/Enroll.vue'), meta: { title: '报名加入' } },
  { path: '/mine', name: 'Mine', component: () => import('@/views/Mine.vue'), meta: { title: '我的', auth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - Open436`
  }

  const user = storage.get('user')
  const guestMode = storage.get('guest_mode', false)
  const isLoggedIn = !!user || guestMode

  if (to.meta.auth && !isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.write && (user?.status === 'pending' || guestMode)) {
    next({ name: 'Home' })
    return
  }

  if (to.name === 'Login' && isLoggedIn) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router

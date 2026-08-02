import { createRouter, createWebHistory } from 'vue-router'
import { storage } from '@/utils/storage'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/Home.vue'), meta: { title: '首页' } },
  {
    path: '/forum',
    component: () => import('@/views/forum/ForumLayout.vue'),
    children: [
      { path: '', redirect: '/forum/tech' },
      { path: 'tech', name: 'ForumTech', component: () => import('@/views/forum/TechForum.vue'), meta: { title: '技术交流', forumSection: 'tech' } },
      { path: 'share', name: 'ForumShare', component: () => import('@/views/forum/ShareForum.vue'), meta: { title: '资源分享', forumSection: 'share' } },
      { path: 'post/new', name: 'PostNew', component: () => import('@/views/forum/PostNew.vue'), meta: { title: '发布新帖', auth: true, write: true } },
      { path: 'post/:id', name: 'PostDetail', component: () => import('@/views/forum/PostDetail.vue'), meta: { title: '帖子详情' } },
      { path: 'search', name: 'Search', component: () => import('@/views/forum/Search.vue'), meta: { title: '搜索' } },
      { path: 'favorites', name: 'Favorites', component: () => import('@/views/forum/Favorites.vue'), meta: { title: '我的收藏', auth: true, write: true } },
    ]
  },
  { path: '/resources', redirect: '/forum/share' },
  { path: '/resources/:id', redirect: to => ({ path: `/forum/post/${to.params.id}` }) },
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
  { path: '/contests', name: 'Contests', component: () => import('@/views/contests/Contests.vue'), meta: { title: '赛事日历' } },
  { path: '/contests/:id', redirect: '/contests' },
  { path: '/quiz', name: 'Quiz', component: () => import('@/views/Quiz.vue'), meta: { title: '算法' } },
  { path: '/enroll', name: 'Enroll', component: () => import('@/views/Enroll.vue'), meta: { title: '报名加入' } },
  { path: '/mine', name: 'Mine', component: () => import('@/views/Mine.vue'), meta: { title: '我的', auth: true } },
  { path: '/mine/edit', name: 'MineEdit', component: () => import('@/views/MineEdit.vue'), meta: { title: '编辑资料', auth: true } },
  { path: '/assignment/:id', name: 'AssignmentSubmit', component: () => import('@/views/AssignmentSubmit.vue'), meta: { title: '作业提交', auth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach((to, from, next) => {
  // 首页已迁移至 3D Landing（React，由网关根路径 / 提供）
  // Vue 应用内任何跳转到根('/')的行为，统一重定向到 Landing
  // 这样 Login 登录成功、导航"首页"tab、品牌链接、catch-all 等全部回到 Landing
  if (to.path === '/') {
    window.location.href = '/'
    return
  }

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

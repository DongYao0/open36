<template>
  <!-- Hero Banner -->
  <div class="res-hero">
    <div class="res-hero-grid"></div>
    <div class="res-hero-content">
      <div class="res-hero-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="28" height="28">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
      <h1 class="res-hero-title">资源分享</h1>
      <p class="res-hero-desc">发现优质工具、框架与技术资源，与社区共享知识财富</p>
      <div class="res-hero-stats">
        <div class="res-stat">
          <span class="res-stat-num">{{ totalCount }}</span>
          <span class="res-stat-label">资源</span>
        </div>
        <div class="res-stat-divider"></div>
        <div class="res-stat">
          <span class="res-stat-num">{{ contributorCount }}</span>
          <span class="res-stat-label">贡献者</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Content -->
  <div class="res-content">
    <!-- Pinned Resources -->
    <template v-if="pinnedPosts.length > 0">
      <div class="res-section-label">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
        </svg>
        精选资源
      </div>
      <div class="res-grid res-grid-featured">
        <div
          v-for="(post, i) in pinnedPosts"
          :key="post.id"
          class="res-card res-card-featured"
          :style="{ animationDelay: `${i * 80}ms` }"
          @click="goPost(post)"
        >
          <div class="res-card-pin">
            <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>
          </div>
          <div class="res-card-body">
            <h3 class="res-card-title">{{ post.title }}</h3>
            <p class="res-card-preview">{{ post.content }}</p>
          </div>
          <div class="res-card-footer">
            <div class="res-card-author">
              <img :src="`https://ui-avatars.com/api/?name=${post.author}&background=F59E0B&color=fff&size=28`" class="res-card-avatar" />
              <span>{{ post.author }}</span>
            </div>
            <div class="res-card-meta">
              <span class="res-card-votes">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
                {{ post.votes }}
              </span>
              <span class="res-card-replies">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                {{ post.replyCount }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- All Resources -->
    <div class="res-section-label">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
      </svg>
      全部资源
    </div>
    <div class="res-list">
      <div
        v-for="(post, i) in regularPosts"
        :key="post.id"
        class="res-list-item"
        :style="{ animationDelay: `${i * 50}ms` }"
        @click="goPost(post)"
      >
        <div class="res-list-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="20" height="20">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
        </div>
        <div class="res-list-body">
          <h4 class="res-list-title">{{ post.title }}</h4>
          <p class="res-list-preview">{{ post.content }}</p>
          <div class="res-list-meta">
            <img :src="`https://ui-avatars.com/api/?name=${post.author}&background=F59E0B&color=fff&size=24`" class="res-list-avatar" />
            <span class="res-list-author">{{ post.author }}</span>
            <span class="res-list-dot">·</span>
            <span class="res-list-time">{{ formatDate(post.createdAt) }}</span>
            <span class="res-list-dot">·</span>
            <span class="res-list-votes">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
              {{ post.votes }}
            </span>
          </div>
        </div>
        <div class="res-list-arrow">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="9 18 15 12 9 6"/></svg>
        </div>
      </div>
    </div>

    <div v-if="loading" class="res-loading"><span class="spinner"></span></div>
    <div v-if="!loading && posts.length === 0" class="res-empty">
      <div class="res-empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
      <p>{{ fetchError || '暂无资源，成为第一个分享者吧' }}</p>
    </div>
    <div ref="sentinel" class="scroll-sentinel"></div>
  </div>

  <!-- FAB -->
  <router-link v-if="auth.canPost" to="/resources/new" class="res-fab" title="分享资源">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="24" height="24">
      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
  </router-link>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSectionStore } from '@/stores/section'
import { useAuthStore } from '@/stores/auth'
import { getPosts } from '@/api/post'
import { formatDate } from '@/utils/format'

const router = useRouter()
const sectionStore = useSectionStore()
const auth = useAuthStore()
const fetchError = ref('')
const loading = ref(false)
const posts = ref([])
const currentPage = ref(1)
const totalCount = ref(0)
const sentinel = ref(null)
let observer = null
const PAGE_SIZE = 10

const hasMore = computed(() => posts.value.length < totalCount.value)
const pinnedPosts = computed(() => posts.value.filter(p => p.pinned))
const regularPosts = computed(() => posts.value.filter(p => !p.pinned))
const contributorCount = computed(() => {
  const authors = new Set(posts.value.map(p => p.author))
  return authors.size
})

async function fetchResources(page = 1) {
  loading.value = true
  try {
    const sectionId = sectionStore.getSectionId('share')
    if (!sectionId) { loading.value = false; return }
    const res = await getPosts({ section_id: sectionId, page, page_size: PAGE_SIZE })
    const data = res?.data || {}
    totalCount.value = data.count || 0
    const results = (data.results || []).map(p => ({
      id: p.id,
      title: p.title,
      content: p.content_preview || p.content || '',
      author: p.author?.nickname || `用户${p.author?.user_id || ''}`,
      votes: p.likes_count || 0,
      replyCount: p.replies_count || 0,
      pinned: p.is_pinned,
      createdAt: p.created_at
    }))
    if (page === 1) posts.value = results
    else posts.value.push(...results)
    currentPage.value = page
  } catch (e) {
    fetchError.value = e?.response?.data?.message || e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (loading.value || !hasMore.value) return
  fetchResources(currentPage.value + 1)
}

function goPost(post) { router.push(`/resources/${post.id}`) }

onMounted(async () => {
  await sectionStore.fetchSections()
  fetchResources(1)
  observer = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) loadMore() }, { rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
})
onUnmounted(() => { observer?.disconnect() })
</script>

<style scoped>
/* ---- Hero ---- */
.res-hero {
  position: relative; padding: 48px 32px 40px;
  background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 40%, #FDE68A 100%);
  border-radius: var(--r-lg); margin-bottom: var(--s-xl); overflow: hidden;
}
.res-hero-grid {
  position: absolute; inset: 0;
  background-image: radial-gradient(circle, rgba(245,158,11,0.12) 1px, transparent 1px);
  background-size: 24px 24px; opacity: 0.6;
}
.res-hero-content { position: relative; z-index: 1; }
.res-hero-icon {
  width: 52px; height: 52px; border-radius: var(--r-md);
  background: rgba(245,158,11,0.15); color: #D97706;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: var(--s-base); border: 1px solid rgba(245,158,11,0.25);
}
.res-hero-title {
  font-size: 28px; font-weight: 700; color: #92400E; letter-spacing: -0.5px;
  margin-bottom: var(--s-sm);
}
.res-hero-desc {
  font-size: 15px; color: #A16207; max-width: 480px; line-height: 1.6;
  margin-bottom: var(--s-lg);
}
.res-hero-stats { display: flex; align-items: center; gap: var(--s-lg); }
.res-stat { display: flex; align-items: baseline; gap: var(--s-xs); }
.res-stat-num { font-size: 24px; font-weight: 700; color: #92400E; font-variant-numeric: tabular-nums; }
.res-stat-label { font-size: 13px; color: #A16207; }
.res-stat-divider { width: 1px; height: 28px; background: rgba(245,158,11,0.25); }

/* ---- Section Label ---- */
.res-section-label {
  display: flex; align-items: center; gap: var(--s-sm);
  font-size: 13px; font-weight: 600; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 0.5px;
  margin-bottom: var(--s-base);
}

/* ---- Featured Grid ---- */
.res-grid { display: grid; gap: var(--s-base); margin-bottom: var(--s-xl); }
.res-grid-featured { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }

.res-card-featured {
  background: var(--bg); border: 1px solid var(--divider); border-radius: var(--r-md);
  padding: var(--s-lg); cursor: pointer; position: relative;
  transition: all var(--t-fast); overflow: hidden;
  animation: resFadeUp 400ms ease-out both;
}
.res-card-featured::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, #F59E0B, #F97316);
}
.res-card-featured:hover {
  border-color: #F59E0B; box-shadow: 0 8px 24px rgba(245,158,11,0.12);
  transform: translateY(-2px);
}
.res-card-pin {
  position: absolute; top: var(--s-base); right: var(--s-base);
  color: #F59E0B; opacity: 0.6;
}
.res-card-body { margin-bottom: var(--s-base); }
.res-card-title { font-size: 16px; font-weight: 600; margin-bottom: var(--s-sm); line-height: 1.4; }
.res-card-preview {
  font-size: 13px; color: var(--text-secondary); line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.res-card-footer { display: flex; align-items: center; justify-content: space-between; }
.res-card-author { display: flex; align-items: center; gap: var(--s-sm); font-size: 13px; color: var(--text-secondary); }
.res-card-avatar { width: 28px; height: 28px; border-radius: 50%; }
.res-card-meta { display: flex; gap: var(--s-md); }
.res-card-votes, .res-card-replies {
  display: flex; align-items: center; gap: 3px;
  font-size: 12px; color: var(--text-disabled);
}

/* ---- List ---- */
.res-list { display: flex; flex-direction: column; margin-bottom: var(--s-xl); }
.res-list-item {
  display: flex; align-items: center; gap: var(--s-base);
  padding: var(--s-base) var(--s-lg); border-bottom: 1px solid var(--divider);
  cursor: pointer; transition: all var(--t-fast);
  animation: resFadeUp 400ms ease-out both;
}
.res-list-item:first-child { border-top: 1px solid var(--divider); }
.res-list-item:hover { background: #FFFBEB; }
.res-list-icon {
  width: 40px; height: 40px; border-radius: var(--r-sm); flex-shrink: 0;
  background: rgba(245,158,11,0.08); color: #D97706;
  display: flex; align-items: center; justify-content: center;
}
.res-list-body { flex: 1; min-width: 0; }
.res-list-title { font-size: 15px; font-weight: 500; margin-bottom: 2px; line-height: 1.4; }
.res-list-preview {
  font-size: 13px; color: var(--text-secondary); line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: var(--s-xs);
}
.res-list-meta { display: flex; align-items: center; gap: var(--s-xs); font-size: 12px; color: var(--text-disabled); }
.res-list-avatar { width: 24px; height: 24px; border-radius: 50%; }
.res-list-author { color: var(--text-secondary); }
.res-list-dot { color: var(--text-disabled); }
.res-list-votes { display: flex; align-items: center; gap: 2px; }
.res-list-arrow { color: var(--text-disabled); transition: transform var(--t-fast); flex-shrink: 0; }
.res-list-item:hover .res-list-arrow { transform: translateX(4px); color: #D97706; }

/* ---- States ---- */
.res-loading { display: flex; justify-content: center; padding: var(--s-xl); }
.res-empty { text-align: center; padding: var(--s-3xl) var(--s-lg); color: var(--text-secondary); }
.res-empty-icon { color: var(--text-disabled); margin-bottom: var(--s-base); opacity: 0.4; }
.scroll-sentinel { height: 1px; }

/* ---- FAB ---- */
.res-fab {
  position: fixed; bottom: var(--s-xl); right: var(--s-xl);
  width: 56px; height: 56px; border-radius: 50%;
  background: linear-gradient(135deg, #F59E0B, #F97316);
  color: #fff; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 8px 24px rgba(245,158,11,0.35);
  transition: all var(--t-fast); z-index: 40;
}
.res-fab:hover { transform: scale(1.1) rotate(90deg); box-shadow: 0 12px 32px rgba(245,158,11,0.45); }
@media (max-width: 959px) { .res-fab { bottom: var(--s-lg); right: var(--s-lg); } }

/* ---- Animation ---- */
@keyframes resFadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ---- Responsive ---- */
@media (max-width: 599px) {
  .res-hero { padding: 32px 20px 28px; }
  .res-hero-title { font-size: 22px; }
  .res-grid-featured { grid-template-columns: 1fr; }
  .res-list-item { padding: var(--s-base) var(--s-sm); }
}
</style>

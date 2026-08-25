<template>
  <section class="resource-landing">
    <div class="resource-hero">
      <div class="hero-copy">
        <p>OPEN436 / RESOURCE HUB</p>
        <h1>发现、收藏、分享<br>真正有价值的资源</h1>
        <span>把好工具、好项目与好想法，放进同一片资源宇宙。</span>
        <a href="#resource-list">开始探索</a>
      </div>
      <div class="hero-art">
        <img src="@/assets/resource-universe.png" alt="资源分享宇宙插画">
        <button v-for="post in featuredPosts" :key="post.id" class="hero-card" @click="$emit('open', post)">
          <small>{{ post.pinned ? '精选资源' : '社区推荐' }}</small>
          <b>{{ post.title }}</b>
          <span>{{ post.votes }} 收藏 · {{ post.author }}</span>
        </button>
      </div>
    </div>

    <div class="resource-intro">
      <p>资源分享，不止于链接</p>
      <h2>让每一次发现<br>都通往新的可能</h2>
      <span>{{ totalCount }} 个资源正在等待被发现</span>
    </div>

    <section id="resource-list" class="resource-stage">
      <div class="stage-heading"><p>本周资源库</p><h2>小卡片，大灵感</h2></div>
      <div v-if="posts.length" class="resource-grid">
        <button v-for="post in posts" :key="post.id" class="resource-card" @click="$emit('open', post)">
          <span class="card-type">{{ post.pinned ? '置顶推荐' : '资源分享' }}</span>
          <strong>{{ post.title }}</strong>
          <em>{{ post.summary || post.preview }}</em>
          <footer><span>{{ post.author }}</span><span>{{ post.votes }} 收藏</span></footer>
        </button>
      </div>
      <div v-else-if="!loading" class="resource-empty">{{ error || '还没有资源，来分享第一份吧。' }}</div>
      <div v-if="loading" class="resource-loading">正在加载资源…</div>
    </section>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ posts: { type: Array, default: () => [] }, totalCount: { type: Number, default: 0 }, loading: Boolean, error: String })
defineEmits(['open'])
const featuredPosts = computed(() => props.posts.slice(0, 4))
</script>

<style scoped>
.resource-landing{margin:-24px -24px -80px;background:linear-gradient(125deg,#1d0d6b,#4938c3 55%,#6d61e8);color:#fff;overflow:hidden}.resource-hero{min-height:620px;max-width:1320px;margin:auto;padding:80px 56px;display:grid;grid-template-columns:.9fr 1.1fr;align-items:center;gap:48px}.hero-copy>p,.resource-intro>p,.stage-heading>p{margin:0 0 14px;color:#d7d2ff;font-size:12px;font-weight:800;letter-spacing:1.4px}.hero-copy h1,.resource-intro h2,.stage-heading h2{margin:0;font-family:var(--font-display);font-size:clamp(42px,5vw,70px);line-height:1.06;letter-spacing:-2px}.hero-copy>span{display:block;max-width:430px;margin:24px 0;color:rgba(255,255,255,.87);font-size:17px;line-height:1.7}.hero-copy>a{display:inline-block;padding:13px 22px;border-radius:11px;background:#fff;color:#302176;text-decoration:none;font-weight:800}.hero-art{position:relative;min-height:410px;border-radius:42px;overflow:hidden;box-shadow:0 24px 70px rgba(14,6,62,.38)}.hero-art>img{position:absolute;width:100%;height:100%;object-fit:cover}.hero-card{position:relative;z-index:1;float:left;width:calc(50% - 18px);min-height:96px;margin:calc(100% - 388px) 9px 0;padding:14px;text-align:left;color:#fff;background:rgba(24,14,72,.88);border:1px solid rgba(255,255,255,.2);border-radius:14px;backdrop-filter:blur(10px);transition:transform .2s}.hero-card:nth-of-type(3),.hero-card:nth-of-type(4){margin-top:10px}.hero-card:hover,.resource-card:hover{transform:translateY(-4px)}.hero-card small,.hero-card span{display:block;color:#b9d9ff;font-size:11px}.hero-card b{display:block;margin:7px 0;font-size:14px;line-height:1.3}.resource-intro{padding:88px 24px 108px;text-align:center}.resource-intro h2{font-size:clamp(38px,4.6vw,64px)}.resource-intro>span{display:block;margin-top:22px;color:rgba(255,255,255,.8)}.resource-stage{max-width:1420px;margin:0 auto 100px;padding:68px 52px;border-radius:72px 72px 0 0;background:rgba(181,175,255,.27)}.stage-heading h2{font-size:clamp(34px,4vw,54px)}.resource-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:38px}.resource-card{min-height:220px;padding:20px;text-align:left;display:flex;flex-direction:column;color:#fff;background:rgba(22,14,71,.83);border:1px solid rgba(255,255,255,.2);border-radius:20px;transition:transform .2s,background .2s}.resource-card:hover{background:rgba(49,31,121,.92)}.card-type{color:#a7d9ff;font-size:11px;font-weight:700}.resource-card strong{margin:12px 0 10px;font-size:18px;line-height:1.35}.resource-card em{display:-webkit-box;overflow:hidden;color:rgba(255,255,255,.72);font-size:13px;font-style:normal;line-height:1.55;-webkit-line-clamp:3;-webkit-box-orient:vertical}.resource-card footer{display:flex;justify-content:space-between;gap:8px;margin-top:auto;padding-top:15px;color:#c3c0f4;font-size:11px;border-top:1px solid rgba(255,255,255,.13)}.resource-empty,.resource-loading{padding:70px 24px;text-align:center;color:rgba(255,255,255,.8)}
@media(max-width:800px){.resource-landing{margin:-16px -16px -80px}.resource-hero{min-height:0;padding:60px 24px;grid-template-columns:1fr}.hero-art{min-height:330px}.resource-stage{margin:0 18px 70px;padding:42px 20px;border-radius:38px}.resource-grid{grid-template-columns:1fr}.hero-card{margin-top:calc(100% - 305px)}.resource-intro{padding:65px 24px}.hero-copy h1{font-size:46px}}
</style>

<template>
  <section class="resource-landing" :style="{ '--resource-universe': `url(${resourceUniverse})` }">
    <div class="resource-hero">
      <div class="hero-copy">
        <h1>发现、收藏、分享<br>真正有价值的资源</h1>
      </div>
    </div>

    <section id="resource-list" class="resource-stage">
      <div v-if="posts.length" class="resource-grid">
        <button v-for="post in posts" :key="post.id" class="resource-card" @click="$emit('open', post)">
          <div class="resource-visual" aria-hidden="true"><img :src="resourceUniverse" alt=""></div>
          <div class="resource-copy">
            <span class="card-type">{{ post.pinned ? '置顶推荐' : '资源分享' }}</span>
            <strong>{{ post.title }}</strong>
            <footer><span>{{ post.author }}</span><span>{{ post.votes }} 收藏</span></footer>
          </div>
        </button>
      </div>
      <div v-else-if="!loading" class="resource-empty">{{ error || '还没有资源，来分享第一份吧。' }}</div>
      <div v-if="loading" class="resource-loading">正在加载资源…</div>
    </section>
  </section>
</template>

<script setup>
import resourceUniverse from '@/assets/resource-universe.png'

const props = defineProps({ posts: { type: Array, default: () => [] }, totalCount: { type: Number, default: 0 }, loading: Boolean, error: String })
defineEmits(['open'])
</script>

<style scoped>
.resource-landing{--base-blue:#1f1d5d;position:relative;min-height:100vh;margin:0 0 -80px;overflow:hidden;color:#fff;background:linear-gradient(180deg,#171b66 0%,#242c88 52%,#4658d4 100%)}
.resource-hero{position:relative;z-index:0;display:grid;min-height:100vh;padding:clamp(110px,15vh,190px) clamp(28px,9vw,150px) 150px;align-items:center;isolation:isolate}.resource-hero::before{position:absolute;z-index:-1;inset:0;background:linear-gradient(180deg,rgba(13,31,135,.22) 0%,rgba(27,49,167,.22) 54%,rgba(24,31,112,.54) 82%,transparent 100%),var(--resource-universe) center/cover no-repeat;content:""}.hero-copy{max-width:800px}.hero-copy h1{margin:0;font-family:var(--font-display);font-size:clamp(48px,7vw,108px);line-height:1.03;letter-spacing:-.06em;text-wrap:balance;text-shadow:0 16px 44px rgba(6,14,78,.56)}
.resource-stage{position:relative;min-height:100vh;width:100%;margin:0;padding:78px clamp(28px,8vw,130px) 120px;background:transparent}.resource-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.resource-card{min-height:168px;padding:21px;text-align:left;display:flex;flex-direction:column;color:#fff;border:1px solid rgba(229,237,255,.33);border-radius:12px;background:linear-gradient(130deg,rgba(53,68,122,.88),rgba(77,87,151,.77));box-shadow:0 14px 30px rgba(26,35,88,.25);backdrop-filter:blur(14px);transition:transform .25s ease,background .25s ease,border-color .25s ease}.resource-card:hover{border-color:rgba(246,238,255,.76);background:linear-gradient(130deg,rgba(66,79,146,.95),rgba(112,84,175,.88));transform:translateY(-7px)}.card-type{color:#bac8ff;font-size:11px;font-weight:800;letter-spacing:.08em}.resource-card strong{margin:12px 0;font-size:18px;line-height:1.4}.resource-card footer{display:flex;justify-content:space-between;gap:8px;margin-top:auto;padding-top:13px;color:#d8dfff;font-size:11px;border-top:1px solid rgba(255,255,255,.16)}.resource-empty,.resource-loading{padding:70px 24px;text-align:center;color:rgba(255,255,255,.86)}
@media(max-width:800px){.resource-landing{margin:0 0 -80px;background-size:auto 100%}.resource-hero{min-height:78vh;padding:120px 24px 94px}.resource-hero::before{background-position:62% center}.hero-copy h1{font-size:clamp(44px,13vw,68px)}.resource-stage{padding:50px 20px 80px}.resource-grid{grid-template-columns:1fr;gap:13px}}

/* 缩小版赛事卡片：图片 60%，信息 40%。 */
.resource-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;max-width:1160px;margin-inline:auto}
.resource-card{display:grid;grid-template-columns:6fr 4fr;min-height:190px;padding:0;overflow:hidden;border-radius:18px;cursor:pointer}
.resource-visual{position:relative;min-height:190px;overflow:hidden;background:#262a78}.resource-visual::after{position:absolute;inset:0;background:linear-gradient(90deg,rgba(12,13,55,.1),rgba(18,19,84,.42));content:""}.resource-visual img{width:100%;height:100%;object-fit:cover;object-position:33% center;transform:scale(1.04);transition:transform .35s ease}.resource-card:hover .resource-visual img{transform:scale(1.1)}
.resource-copy{display:flex;flex-direction:column;min-width:0;padding:22px 20px;text-align:left;background:linear-gradient(130deg,rgba(13,14,48,.88),rgba(34,31,106,.82))}.resource-copy strong{margin:11px 0;font-size:clamp(1rem,1.6vw,1.18rem);line-height:1.35}.resource-copy footer{display:flex}
@media(max-width:680px){.resource-card{grid-template-columns:1fr;min-height:0}.resource-visual{min-height:170px}.resource-copy{min-height:145px;padding:19px}.resource-copy strong{font-size:1rem}}
@media(max-width:850px){.resource-grid{grid-template-columns:1fr;max-width:680px}}
</style>

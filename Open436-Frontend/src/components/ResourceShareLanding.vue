<template>
  <section class="resource-landing" :style="{ '--resource-universe': `url(${resourceUniverse})` }">
    <div class="resource-hero">
      <div class="hero-copy">
        <h1>发现、收藏、分享<br>真正有价值的资源</h1>
      </div>
    </div>

    <section id="resource-list" class="resource-stage">
      <div v-if="posts.length" class="resource-grid">
        <button v-for="(post, index) in posts" :key="post.id" class="resource-card" @click="$emit('open', post)">
          <div class="resource-visual" aria-hidden="true"><span>{{ post.pinned ? '★' : '↗' }}</span><i></i><i></i></div>
          <div class="resource-copy">
            <span class="card-type">{{ post.pinned ? '精选资源' : `资源目录 · ${String(index + 1).padStart(2, '0')}` }}</span>
            <strong>{{ post.title }}</strong>
            <p>{{ post.preview }}</p>
            <footer><span>{{ post.author }} · {{ post.votes }} 收藏</span><b>查看资源 ↗</b></footer>
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
.resource-landing{--base-blue:#1f1d5d;position:relative;min-height:100vh;margin:0 0 -80px;overflow:hidden;color:#fff;background-color:#151650;background-image:linear-gradient(180deg,rgba(15,20,100,.06),rgba(20,17,77,.42) 58%,#12142f 100%),var(--resource-universe);background-position:center top,center top;background-size:auto,100% auto;background-repeat:no-repeat}
.resource-hero{position:relative;z-index:0;min-height:68vh;isolation:isolate}.resource-hero::before{position:absolute;z-index:-1;inset:0;background:linear-gradient(180deg,rgba(13,31,135,.08) 0%,rgba(27,49,167,.12) 54%,rgba(24,31,112,.32) 100%);content:""}.hero-copy{position:absolute;top:clamp(104px,11vh,150px);right:clamp(28px,8vw,130px);max-width:min(560px,42vw);margin:0;padding:0;border:0;background:none;box-shadow:none;text-align:right}.hero-copy h1{margin:0;font-family:var(--font-display);font-size:clamp(42px,5.3vw,84px);line-height:1.03;letter-spacing:-.06em;text-wrap:balance;text-shadow:0 5px 26px rgba(6,14,78,.4)}
.resource-stage{position:relative;min-height:100vh;width:100%;margin:0;padding:78px clamp(28px,8vw,130px) 120px;background:transparent}.resource-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.resource-card{min-height:168px;padding:21px;text-align:left;display:flex;flex-direction:column;color:#fff;border:1px solid rgba(229,237,255,.33);border-radius:12px;background:linear-gradient(130deg,rgba(53,68,122,.88),rgba(77,87,151,.77));box-shadow:0 14px 30px rgba(26,35,88,.25);backdrop-filter:blur(14px);transition:transform .25s ease,background .25s ease,border-color .25s ease}.resource-card:hover{border-color:rgba(246,238,255,.76);background:linear-gradient(130deg,rgba(66,79,146,.95),rgba(112,84,175,.88));transform:translateY(-7px)}.card-type{color:#bac8ff;font-size:11px;font-weight:800;letter-spacing:.08em}.resource-card strong{margin:12px 0;font-size:18px;line-height:1.4}.resource-card footer{display:flex;justify-content:space-between;gap:8px;margin-top:auto;padding-top:13px;color:#d8dfff;font-size:11px;border-top:1px solid rgba(255,255,255,.16)}.resource-empty,.resource-loading{padding:70px 24px;text-align:center;color:rgba(255,255,255,.86)}
@media(max-width:800px){.resource-landing{margin:0 0 -80px;background-size:auto 100%}.resource-hero{min-height:78vh}.resource-hero::before{background-position:62% center}.hero-copy{top:104px;right:24px;max-width:calc(100vw - 48px)}.hero-copy h1{font-size:clamp(44px,13vw,68px)}.resource-stage{padding:50px 20px 80px}.resource-grid{grid-template-columns:1fr;gap:13px}}

/* 缩小版赛事卡片：图片 60%，信息 40%。 */
.resource-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;max-width:1160px;margin-inline:auto}
.resource-card{display:grid;grid-template-columns:6fr 4fr;min-height:190px;padding:0;overflow:hidden;border-radius:18px;cursor:pointer}
.resource-visual{position:relative;min-height:190px;overflow:hidden;background:#262a78}.resource-visual::after{position:absolute;inset:0;background:linear-gradient(90deg,rgba(12,13,55,.1),rgba(18,19,84,.42));content:""}.resource-visual img{width:100%;height:100%;object-fit:cover;object-position:33% center;transform:scale(1.04);transition:transform .35s ease}.resource-card:hover .resource-visual img{transform:scale(1.1)}
.resource-copy{display:flex;flex-direction:column;min-width:0;padding:22px 20px;text-align:left;background:linear-gradient(130deg,rgba(13,14,48,.88),rgba(34,31,106,.82))}.resource-copy strong{margin:11px 0;font-size:clamp(1rem,1.6vw,1.18rem);line-height:1.35}.resource-copy footer{display:flex}
@media(max-width:680px){.resource-card{grid-template-columns:1fr;min-height:0}.resource-visual{min-height:170px}.resource-copy{min-height:145px;padding:19px}.resource-copy strong{font-size:1rem}}
@media(max-width:850px){.resource-grid{grid-template-columns:1fr;max-width:680px}}

.resource-stage{min-height:calc(100vh - 360px);margin-top:0;padding-top:clamp(42px,8vh,88px);background:linear-gradient(180deg,rgba(25,27,103,0) 0%,rgba(22,24,80,.34) 40%,#12142f 100%)}.resource-grid{position:relative;z-index:1;gap:20px;margin-top:clamp(220px,24vh,320px)}.resource-card{min-height:214px;border-color:rgba(246,230,188,.42);background:#111941;box-shadow:0 22px 45px rgba(10,14,60,.32)}
.resource-visual{display:grid;place-items:center;min-height:214px;background:radial-gradient(circle at 25% 22%,#f7c86b 0 3%,transparent 3.5%),radial-gradient(circle at 67% 58%,rgba(102,227,230,.8) 0 4%,transparent 4.5%),linear-gradient(135deg,#fa9e47,#de5837 51%,#713273);isolation:isolate}.resource-visual:before{position:absolute;inset:12%;border:1px solid rgba(255,242,211,.52);border-radius:50%;content:""}.resource-visual span{position:relative;z-index:2;color:#fff7e7;font:700 62px/1 Georgia,serif;text-shadow:0 8px 17px rgba(75,15,41,.35)}.resource-visual i{position:absolute;width:12px;height:12px;border:2px solid rgba(255,245,220,.72);transform:rotate(45deg)}.resource-visual i:first-of-type{top:23px;right:29px}.resource-visual i:last-of-type{bottom:28px;left:30px;width:20px;height:20px}
.resource-copy{background:linear-gradient(145deg,#101a43,#22205c)}.resource-copy p{display:-webkit-box;overflow:hidden;margin:0;color:#bac6e8;font-size:13px;line-height:1.65;-webkit-line-clamp:3;-webkit-box-orient:vertical}.resource-copy footer{align-items:center}.resource-copy footer b{color:#f7c86b;font-size:11px;white-space:nowrap}.resource-card:hover{border-color:#f7c86b;background:#111941;box-shadow:0 25px 52px rgba(24,16,82,.48)}
@media(max-width:680px){.resource-stage{margin-top:0;padding-top:42px}.resource-grid{margin-top:140px}.resource-visual{min-height:150px}}
</style>

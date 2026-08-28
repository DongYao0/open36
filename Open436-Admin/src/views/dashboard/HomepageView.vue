<template>
  <div class="homepage-view">
    <div class="page-header">
      <h2>首页管理</h2>
      <p class="sub">维护 3D 首页（:5173）全部展示内容，保存后前台刷新即生效</p>
    </div>

    <el-tabs v-model="activeTab" v-loading="loading">
      <!-- ══════════ 1. 实验室介绍 ══════════ -->
      <el-tab-pane label="实验室介绍" name="about">
        <el-card shadow="never" v-if="about">
          <el-form label-width="90px">
            <el-form-item label="小标题"><el-input v-model="about.subText" placeholder="如：实验室介绍" /></el-form-item>
            <el-form-item label="主标题"><el-input v-model="about.headText" placeholder="如：关于0436." /></el-form-item>
            <el-form-item label="描述正文">
              <el-input v-model="about.description" type="textarea" :rows="8" placeholder="实验室介绍正文，换行会原样显示在前台" />
            </el-form-item>
          </el-form>
          <el-divider content-position="left">四个功能小卡片</el-divider>
          <div v-for="(s, i) in aboutServices" :key="i" class="row-item">
            <el-input v-model="s.title" placeholder="卡片标题（如：在线判题）" class="flex-1" />
            <ImageBox v-model="s.icon" tip="Logo（可空）" />
            <el-button circle size="small" :disabled="i === 0" @click="moveItem(aboutServices, i, -1)">↑</el-button>
            <el-button circle size="small" :disabled="i === aboutServices.length - 1" @click="moveItem(aboutServices, i, 1)">↓</el-button>
            <el-button circle size="small" type="danger" @click="confirmRemove(aboutServices, i, '卡片')">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          <el-button class="mt8" @click="aboutServices.push({ title: '', icon: '' })">+ 新增卡片</el-button>
        </el-card>
      </el-tab-pane>

      <!-- ══════════ 2. 功能卡片（四大优势） ══════════ -->
      <el-tab-pane label="实验室功能" name="experiences">
        <div v-if="experiences.length">
          <el-card v-for="(exp, i) in experiences" :key="i" shadow="never" class="mb12">
            <div class="card-toolbar">
              <b>卡片 {{ i + 1 }}</b>
              <span>
                <el-button circle size="small" :disabled="i === 0" @click="moveItem(experiences, i, -1)">↑</el-button>
                <el-button circle size="small" :disabled="i === experiences.length - 1" @click="moveItem(experiences, i, 1)">↓</el-button>
                <el-button size="small" type="danger" @click="confirmRemove(experiences, i, '卡片')">
                  <el-icon><Delete /></el-icon>删除
                </el-button>
              </span>
            </div>
            <el-form label-width="90px">
              <el-form-item label="标题"><el-input v-model="exp.title" placeholder="如：竞赛升学优势" /></el-form-item>
              <el-form-item label="副标题"><el-input v-model="exp.company_name" placeholder="如：Advantages in Competition" /></el-form-item>
              <el-form-item label="圆形Logo">
                <ImageBox v-model="exp.icon" tip="左侧圆形图标" />
              </el-form-item>
              <el-form-item label="要点列表">
                <el-input v-model="exp._points" type="textarea" :rows="4" placeholder="每行一个要点，前台按列表展示" />
              </el-form-item>
            </el-form>
          </el-card>
          <el-button @click="experiences.push({ title: '', company_name: '', icon: '', iconBg: '#ffffff', points: [], _points: '' })">+ 新增功能卡片</el-button>
        </div>
      </el-tab-pane>

      <!-- ══════════ 3. 技术栈小球 ══════════ -->
      <el-tab-pane label="技术栈小球" name="technologies">
        <el-alert type="info" :closable="false" class="mb12"
          title="小球按列表顺序网格排列（大屏每行7个），新增/删除后前台自动适配数量" />
        <div v-if="technologies.length" class="tech-grid">
          <div v-for="(t, i) in technologies" :key="i" class="tech-item">
            <ImageBox v-model="t.icon" tip="小球图标" />
            <el-input v-model="t.name" placeholder="名称" size="small" class="mt4" />
            <div class="tech-ops">
              <el-button circle size="small" :disabled="i === 0" @click="moveItem(technologies, i, -1)">↑</el-button>
              <el-button circle size="small" :disabled="i === technologies.length - 1" @click="moveItem(technologies, i, 1)">↓</el-button>
              <el-button circle size="small" type="danger" @click="confirmRemove(technologies, i, '小球')">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
        <el-button class="mt8" @click="technologies.push({ name: '', icon: '' })">+ 新增小球</el-button>
      </el-tab-pane>

      <!-- ══════════ 4. 获奖荣誉 ══════════ -->
      <el-tab-pane label="获奖荣誉" name="works">
        <el-card shadow="never" class="mb12" v-if="works">
          <el-form label-width="90px">
            <el-form-item label="小标题"><el-input v-model="works.subText" placeholder="如：实验室荣誉" /></el-form-item>
            <el-form-item label="主标题"><el-input v-model="works.headText" placeholder="如：竞赛奖项." /></el-form-item>
            <el-form-item label="描述正文">
              <el-input v-model="works.description" type="textarea" :rows="4" placeholder="荣誉区块说明文字" />
            </el-form-item>
          </el-form>
        </el-card>
        <el-card v-for="(p, i) in worksItems" :key="i" shadow="never" class="mb12">
          <div class="card-toolbar">
            <b>奖项卡片 {{ i + 1 }}</b>
            <span>
              <el-button circle size="small" :disabled="i === 0" @click="moveItem(worksItems, i, -1)">↑</el-button>
              <el-button circle size="small" :disabled="i === worksItems.length - 1" @click="moveItem(worksItems, i, 1)">↓</el-button>
              <el-button size="small" type="danger" @click="confirmRemove(worksItems, i, '奖项卡片')">
                <el-icon><Delete /></el-icon>删除
              </el-button>
            </span>
          </div>
          <el-form label-width="90px">
            <el-form-item label="标题"><el-input v-model="p.name" placeholder="如：蓝桥杯大赛" /></el-form-item>
            <el-form-item label="描述"><el-input v-model="p.description" type="textarea" :rows="3" /></el-form-item>
            <el-form-item label="图片"><ImageBox v-model="p.image" tip="卡片配图" /></el-form-item>
            <el-form-item label="链接"><el-input v-model="p.source_code_link" placeholder="https://...（可空）" /></el-form-item>
            <el-form-item label="标签">
              <div>
                <el-tag v-for="(tag, ti) in p.tags" :key="ti" closable class="mr4"
                  :type="['', 'success', 'danger'][ti % 3]"
                  @close="p.tags.splice(ti, 1)">#{{ tag.name }} · {{ tag.color }}</el-tag>
                <el-button size="small" @click="openTagDialog(p)">+ 添加标签</el-button>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
        <el-button @click="worksItems.push({ name: '', description: '', image: '', tags: [], source_code_link: '' })">+ 新增奖项卡片</el-button>
      </el-tab-pane>

      <!-- ══════════ 5. 社区声音 ══════════ -->
      <el-tab-pane label="社区声音" name="feedbacks">
        <el-card shadow="never" class="mb12" v-if="feedbacks">
          <el-form label-width="90px" inline>
            <el-form-item label="小标题"><el-input v-model="feedbacks.subText" placeholder="如：社区声音" /></el-form-item>
            <el-form-item label="主标题"><el-input v-model="feedbacks.headText" placeholder="如：学长学姐寄语." /></el-form-item>
          </el-form>
        </el-card>
        <el-card v-for="(f, i) in feedbackItems" :key="i" shadow="never" class="mb12">
          <div class="card-toolbar">
            <b>寄语 {{ i + 1 }}</b>
            <span>
              <el-button circle size="small" :disabled="i === 0" @click="moveItem(feedbackItems, i, -1)">↑</el-button>
              <el-button circle size="small" :disabled="i === feedbackItems.length - 1" @click="moveItem(feedbackItems, i, 1)">↓</el-button>
              <el-button size="small" type="danger" @click="confirmRemove(feedbackItems, i, '寄语')">
                <el-icon><Delete /></el-icon>删除
              </el-button>
            </span>
          </div>
          <el-form label-width="90px">
            <el-form-item label="寄语正文">
              <el-input v-model="f.testimonial" type="textarea" :rows="3" placeholder="换行会原样显示" />
            </el-form-item>
            <el-form-item label="署名"><el-input v-model="f.name" placeholder="如：往届学长" style="width:220px" /></el-form-item>
            <el-form-item label="身份/方向"><el-input v-model="f.designation" placeholder="如：后端开发方向" style="width:220px" /></el-form-item>
            <el-form-item label="头像"><ImageBox v-model="f.image" tip="圆形头像" /></el-form-item>
          </el-form>
        </el-card>
        <el-button @click="feedbackItems.push({ testimonial: '', name: '', designation: '', company: '', image: '' })">+ 新增寄语</el-button>
      </el-tab-pane>
    </el-tabs>

    <!-- 底部操作条 -->
    <div class="action-bar" v-if="!loading">
      <el-button type="primary" :loading="saving" @click="save">保存当前模块</el-button>
      <el-button @click="reset" type="warning" plain>重置为默认</el-button>
      <span class="hint">「保存」提交当前 tab；「重置」删除该模块数据，前台回退为代码内置默认内容</span>
    </div>

    <!-- 添加标签弹窗 -->
    <el-dialog v-model="tagDialog.visible" title="添加标签" width="360px">
      <el-form label-width="70px">
        <el-form-item label="标签名"><el-input v-model="tagDialog.name" placeholder="如：算法竞赛" /></el-form-item>
        <el-form-item label="配色">
          <el-select v-model="tagDialog.color">
            <el-option label="蓝（默认）" value="blue-text-gradient" />
            <el-option label="绿" value="green-text-gradient" />
            <el-option label="粉" value="pink-text-gradient" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tagDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="addTag">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineComponent, h } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { getHomepageModule, saveHomepageModule, resetHomepageModule } from '@/api/homepage'
import { uploadFile } from '@/api/files'

/* ─────────── 图片上传框（内部小组件） ─────────── */
const ImageBox = defineComponent({
  props: ['modelValue', 'tip'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const uploading = ref(false)
    const onFile = async (opt) => {
      const file = opt.file
      if (!/image\/(png|jpe?g|webp|svg\+xml)/.test(file.type)) {
        ElMessage.error('仅支持 png / jpg / webp / svg 图片')
        return
      }
      uploading.value = true
      try {
        const fd = new FormData()
        fd.append('file', file)
        fd.append('file_type', 'section_icon')
        const res = await uploadFile(fd)
        emit('update:modelValue', res.data.url)
        ElMessage.success('上传成功')
      } catch (e) {
        ElMessage.error(e?.response?.data?.message || '上传失败')
      } finally {
        uploading.value = false
      }
    }
    return () => h('div', { class: 'img-box' }, [
      props.modelValue
        ? h('img', { src: props.modelValue, class: 'img-preview' })
        : h('div', { class: 'img-empty' }, props.tip || '未设置'),
      h('div', { class: 'img-ops' }, [
        h('label', { class: 'el-button el-button--small' }, [
          uploading.value ? '上传中…' : (props.modelValue ? '替换' : '上传'),
          h('input', {
            type: 'file', accept: 'image/png,image/jpeg,image/webp,image/svg+xml',
            style: 'display:none',
            onChange: (e) => { const f = e.target.files[0]; if (f) onFile({ file: f }); e.target.value = '' }
          })
        ]),
        props.modelValue
          ? h('button', {
              class: 'el-button el-button--small el-button--danger is-plain',
              onClick: () => emit('update:modelValue', '')
            }, () => '清除')
          : null
      ])
    ])
  }
})

/* ─────────── 模块数据 ─────────── */
const loading = ref(false)
const saving = ref(false)
const activeTab = ref('about')

const about = ref(null)
const experiences = ref([])
const technologies = ref([])
const works = ref(null)
const feedbacks = ref(null)

const aboutServices = computed(() => about.value?.services || [])
const worksItems = computed(() => works.value?.items || [])
const feedbackItems = computed(() => feedbacks.value?.items || [])

const tagDialog = ref({ visible: false, target: null, name: '', color: 'blue-text-gradient' })
function openTagDialog(project) {
  tagDialog.value = { visible: true, target: project, name: '', color: 'blue-text-gradient' }
}
function addTag() {
  const { target, name, color } = tagDialog.value
  if (!name.trim()) { ElMessage.warning('标签名不能为空'); return }
  if (!Array.isArray(target.tags)) target.tags = []
  target.tags.push({ name: name.trim(), color })
  tagDialog.value.visible = false
}

/* ─────────── 通用操作 ─────────── */
function moveItem(list, i, dir) {
  const j = i + dir
  if (j < 0 || j >= list.length) return
  ;[list[i], list[j]] = [list[j], list[i]]
}
function confirmRemove(list, i, label) {
  ElMessageBox.confirm(`确定删除该${label}吗？`, '提示', { type: 'warning' })
    .then(() => list.splice(i, 1))
    .catch(() => {})
}

/* points[] <-> 多行文本 */
const pointsToText = (pts) => (pts || []).join('\n')
const textToPoints = (text) => String(text || '').split('\n').map(s => s.trim()).filter(Boolean)

/* ─────────── 加载 ─────────── */
async function loadAll() {
  loading.value = true
  try {
    const [aboutRes, expRes, techRes, worksRes, fbRes] = await Promise.all([
      getHomepageModule('about'),
      getHomepageModule('experiences'),
      getHomepageModule('technologies'),
      getHomepageModule('works'),
      getHomepageModule('feedbacks')
    ])
    about.value = aboutRes.data || { subText: '', headText: '', description: '', services: [] }
    if (!Array.isArray(about.value.services)) about.value.services = []
    experiences.value = (expRes.data || []).map(e => ({ ...e, _points: pointsToText(e.points) }))
    technologies.value = techRes.data || []
    works.value = worksRes.data || { subText: '', headText: '', description: '', items: [] }
    if (!Array.isArray(works.value.items)) works.value.items = []
    feedbacks.value = fbRes.data || { subText: '', headText: '', items: [] }
    if (!Array.isArray(feedbacks.value.items)) feedbacks.value.items = []
  } catch (e) {
    ElMessage.error('加载首页内容失败')
  } finally {
    loading.value = false
  }
}

/* ─────────── 保存 / 重置 ─────────── */
async function save() {
  saving.value = true
  try {
    if (activeTab.value === 'about') {
      await saveHomepageModule('about', about.value)
    } else if (activeTab.value === 'experiences') {
      const payload = experiences.value.map(({ _points, ...rest }) => ({ ...rest, points: textToPoints(_points) }))
      await saveHomepageModule('experiences', payload)
    } else if (activeTab.value === 'technologies') {
      await saveHomepageModule('technologies', technologies.value)
    } else if (activeTab.value === 'works') {
      await saveHomepageModule('works', { ...works.value, items: worksItems.value })
    } else if (activeTab.value === 'feedbacks') {
      await saveHomepageModule('feedbacks', { ...feedbacks.value, items: feedbackItems.value })
    }
    ElMessage.success('保存成功，前台刷新即生效')
    await loadAll()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function reset() {
  const module = activeTab.value
  try {
    await ElMessageBox.confirm(
      '重置后该模块数据将被删除，前台回退为代码内置默认内容，确定继续吗？',
      '重置确认', { type: 'warning' }
    )
  } catch { return }
  try {
    await resetHomepageModule(module)
    ElMessage.success('已重置')
    await loadAll()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '重置失败')
  }
}

onMounted(loadAll)
</script>

<style scoped>
.homepage-view { padding: 20px; max-width: 1100px; margin: 0 auto; }
.page-header { margin-bottom: 16px; }
.page-header h2 { margin: 0 0 4px; }
.page-header .sub { color: #909399; font-size: 13px; margin: 0; }
.row-item { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.flex-1 { flex: 1; }
.mt8 { margin-top: 8px; }
.mt4 { margin-top: 4px; }
.mb12 { margin-bottom: 12px; }
.mr4 { margin-right: 4px; }
.card-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.tech-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.tech-item { display: flex; flex-direction: column; gap: 6px; padding: 10px; border: 1px solid #ebeef5; border-radius: 6px; }
.tech-ops { display: flex; gap: 6px; }
.action-bar { position: sticky; bottom: 0; background: #fff; padding: 12px 0; border-top: 1px solid #ebeef5; display: flex; align-items: center; gap: 8px; }
.action-bar .hint { color: #909399; font-size: 12px; }
</style>

<style>
/* ImageUploadBox 全局样式（render 函数组件） */
.img-box { display: flex; align-items: center; gap: 10px; }
.img-preview { width: 72px; height: 72px; object-fit: cover; border-radius: 6px; border: 1px solid #dcdfe6; }
.img-empty { width: 72px; height: 72px; border: 1px dashed #dcdfe6; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 11px; color: #c0c4cc; text-align: center; padding: 4px; box-sizing: border-box; }
.img-ops { display: flex; gap: 6px; }
</style>

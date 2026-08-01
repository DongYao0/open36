<template>
  <div class="interview-view">
    <div class="page-header"><h2>面试管理</h2></div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom:20px">
      <el-col :span="6">
        <StatCard label="待面试总人数" :value="stats.total" icon="User" icon-bg="#e3f2fd" icon-color="#1976D2" />
      </el-col>
      <el-col :span="6">
        <StatCard label="待面试" :value="stats.pending" icon="Clock" icon-bg="#fff3e0" icon-color="#ff9800" />
      </el-col>
      <el-col :span="6">
        <StatCard label="已通过" :value="stats.passed" icon="CircleCheck" icon-bg="#e8f5e9" icon-color="#4caf50" />
      </el-col>
      <el-col :span="6">
        <StatCard label="通过率" :value="stats.passRate + '%'" icon="TrendCharts" icon-bg="#f3e5f5" icon-color="#9c27b0" />
      </el-col>
    </el-row>

    <!-- 筛选与操作 -->
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索姓名/学号/专业" clearable style="width:240px" prefix-icon="Search" @input="loadList" />
      <el-radio-group v-model="statusFilter" @change="loadList">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="pending">待面试</el-radio-button>
        <el-radio-button value="passed">已通过</el-radio-button>
        <el-radio-button value="failed">未通过</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 数据表格 -->
    <el-table :data="list" stripe v-loading="loading">
      <el-table-column prop="enrollmentId" label="报名ID" width="80" />
      <el-table-column prop="realName" label="姓名" width="100" />
      <el-table-column prop="username" label="用户名" width="130" />
      <el-table-column prop="studentId" label="学号" width="140" />
      <el-table-column prop="major" label="专业" width="150" />
      <el-table-column label="面试记录" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span v-if="row.summary">{{ row.summary }}</span>
          <span v-else style="color:#c0c4cc">-</span>
        </template>
      </el-table-column>
      <el-table-column label="意向" width="100">
        <template #default="{ row }">
          <span v-if="row.direction">{{ row.direction }}</span>
          <span v-else style="color:#c0c4cc">-</span>
        </template>
      </el-table-column>
      <el-table-column label="评分" width="90" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.score != null" :type="scoreTagType(row.score)" size="small">{{ row.score }}</el-tag>
          <span v-else style="color:#c0c4cc">-</span>
        </template>
      </el-table-column>
      <el-table-column label="面试状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType[row.status]" size="small">{{ statusLabels[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="goEdit(row.enrollmentId)">
            <el-icon><Edit /></el-icon>编辑
          </el-button>
          <el-dropdown v-if="row.status === 'pending'" trigger="click" @command="(cmd) => handleStatusUpdate(row, cmd)">
            <el-button size="small" link>
              更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="passed">
                  <el-icon color="#67c23a"><CircleCheck /></el-icon>面试通过
                </el-dropdown-item>
                <el-dropdown-item command="failed" divided>
                  <el-icon color="#f56c6c"><CircleClose /></el-icon>面试未通过
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:16px">
      <el-pagination v-model:current-page="page" :page-size="10" :total="total" layout="total, prev, pager, next" @current-change="loadList" />
    </div>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" :title="`面试详情 - ${currentItem?.realName || ''}`" size="560px">
      <template v-if="currentItem">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="姓名">{{ currentItem.realName }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ currentItem.username }}</el-descriptions-item>
          <el-descriptions-item label="学号">{{ currentItem.studentId }}</el-descriptions-item>
          <el-descriptions-item label="专业">{{ currentItem.major }}</el-descriptions-item>
          <el-descriptions-item label="意向">{{ currentItem.direction || '-' }}</el-descriptions-item>
          <el-descriptions-item label="评分">
            <el-tag v-if="currentItem.score != null" :type="scoreTagType(currentItem.score)" size="small">{{ currentItem.score }}/10</el-tag>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="面试状态">
            <el-tag :type="statusTagType[currentItem.status]" size="small">{{ statusLabels[currentItem.status] }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div style="margin-top:16px">
          <h4 style="margin-bottom:8px">自我介绍</h4>
          <p style="color:#666;line-height:1.6">{{ currentItem.selfIntro || '暂无' }}</p>
        </div>
        <div style="margin-top:12px">
          <h4 style="margin-bottom:8px">技能标签</h4>
          <div>
            <el-tag v-for="skill in currentItem.skills?.split(',')" :key="skill" style="margin:2px 4px">{{ skill.trim() }}</el-tag>
            <span v-if="!currentItem.skills" style="color:#c0c4cc">暂无</span>
          </div>
        </div>

        <div v-if="currentItem.summary" style="margin-top:16px">
          <h4 style="margin-bottom:8px">面试记录</h4>
          <p style="color:#666;line-height:1.8;white-space:pre-wrap">{{ currentItem.summary }}</p>
        </div>

        <div v-if="currentItem.status === 'pending'" style="margin-top:24px;display:flex;gap:12px">
          <el-button type="primary" size="large" @click="drawerVisible = false; goEdit(currentItem.enrollmentId)">
            <el-icon><Edit /></el-icon>编辑面试信息
          </el-button>
          <el-button type="success" @click="handleStatusUpdate(currentItem, 'passed'); drawerVisible = false">通过</el-button>
          <el-button type="danger" @click="handleStatusUpdate(currentItem, 'failed'); drawerVisible = false">未通过</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import StatCard from '@/components/StatCard.vue'
import { getInterviewList, getInterviewDetail, updateInterviewStatus, getInterviewStatistics } from '@/api/interview'

const router = useRouter()

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const keyword = ref('')
const statusFilter = ref('')
const stats = ref({ total: 0, pending: 0, passed: 0, failed: 0, passRate: 0 })

const drawerVisible = ref(false)
const currentItem = ref(null)

const statusLabels = { pending: '待面试', passed: '已通过', failed: '未通过' }
const statusTagType = { pending: 'warning', passed: 'success', failed: 'danger' }

function scoreTagType(score) {
  if (score >= 8) return 'success'
  if (score >= 5) return 'warning'
  return 'danger'
}

async function loadStats() {
  try {
    const res = await getInterviewStatistics()
    stats.value = res.data
  } catch {}
}

async function loadList() {
  loading.value = true
  try {
    const res = await getInterviewList({
      page: page.value,
      size: 10,
      status: statusFilter.value,
      keyword: keyword.value
    })
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function openDetail(row) {
  try {
    const res = await getInterviewDetail(row.enrollmentId)
    currentItem.value = res.data
    drawerVisible.value = true
  } catch {
    ElMessage.error('加载详情失败')
  }
}

function goEdit(enrollmentId) {
  router.push(`/enrollment/interview/edit/${enrollmentId}`)
}

async function handleStatusUpdate(row, status) {
  if (!row.id) {
    ElMessage.warning('该候选人暂无面试记录，请先编辑面试信息')
    return
  }
  const label = status === 'passed' ? '通过' : '不通过'
  try {
    await ElMessageBox.confirm(`确定标记「${row.realName}」面试${label}？`, '确认', {
      type: status === 'passed' ? 'success' : 'warning'
    })
    await updateInterviewStatus(row.id, status)
    ElMessage.success(`已标记为面试${label}`)
    loadList()
    loadStats()
  } catch {}
}

onMounted(() => {
  loadStats()
  loadList()
})
</script>

<style scoped>
.interview-view {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
</style>

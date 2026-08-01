<template>
  <div class="enrollment-view">
    <div class="page-header"><h2>报名管理</h2></div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom:20px">
      <el-col :span="6">
        <StatCard label="总申请数" :value="stats.total" icon="Document" icon-bg="#e3f2fd" icon-color="#1976D2" />
      </el-col>
      <el-col :span="6">
        <StatCard label="待审核" :value="stats.pending" icon="Clock" icon-bg="#fff3e0" icon-color="#ff9800" />
      </el-col>
      <el-col :span="6">
        <StatCard label="已通过" :value="stats.approved" icon="CircleCheck" icon-bg="#e8f5e9" icon-color="#4caf50" />
      </el-col>
      <el-col :span="6">
        <StatCard label="通过率" :value="stats.approvalRate + '%'" icon="TrendCharts" icon-bg="#f3e5f5" icon-color="#9c27b0" />
      </el-col>
    </el-row>

    <!-- 筛选与操作 -->
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索姓名/学号/专业" clearable style="width:240px" @input="loadList">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-radio-group v-model="statusFilter" @change="loadList">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="pending">待审核</el-radio-button>
        <el-radio-button value="approved">已通过</el-radio-button>
        <el-radio-button value="rejected">已拒绝</el-radio-button>
      </el-radio-group>
      <el-button type="success" :disabled="!selectedIds.length" @click="handleBatchReview('approved')">
        <el-icon><CircleCheck /></el-icon>批量通过 ({{ selectedIds.length }})
      </el-button>
      <el-button type="danger" :disabled="!selectedIds.length" @click="handleBatchReview('rejected')">
        <el-icon><CircleClose /></el-icon>批量拒绝 ({{ selectedIds.length }})
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table :data="applications" stripe v-loading="loading" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="realName" label="姓名" width="100" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="studentId" label="学号" width="130" />
      <el-table-column prop="major" label="专业" width="180" />
      <el-table-column prop="phone" label="联系方式" width="130" />
      <el-table-column prop="submittedAt" label="提交时间" width="170" :formatter="formatDate" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusTagType[row.status]" size="small">{{ statusLabels[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="openDetail(row)">查看</el-button>
          <template v-if="row.status === 'pending'">
            <el-button type="success" link size="small" @click="handleReview(row, 'approved')">通过</el-button>
            <el-button type="danger" link size="small" @click="handleReview(row, 'rejected')">拒绝</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div style="display:flex;justify-content:flex-end;margin-top:16px">
      <el-pagination v-model:current-page="page" :page-size="10" :total="total" layout="total, prev, pager, next" @current-change="loadList" />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="dialogVisible" :title="`申请详情 - ${currentItem?.realName || ''}`" width="480px" :close-on-click-modal="false" center>
      <el-descriptions v-if="currentItem" :column="1" border>
        <el-descriptions-item label="姓名">{{ currentItem.realName }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ currentItem.username }}</el-descriptions-item>
        <el-descriptions-item label="学号">{{ currentItem.studentId }}</el-descriptions-item>
        <el-descriptions-item label="专业">{{ currentItem.major }}</el-descriptions-item>
        <el-descriptions-item label="手机">{{ currentItem.phone }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ currentItem.submittedAt }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType[currentItem.status]" size="small">{{ statusLabels[currentItem.status] }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 拒绝原因对话框 -->
    <el-dialog v-model="showRejectReason" title="拒绝原因" width="400px">
      <el-input v-model="rejectReason" type="textarea" :rows="3" placeholder="请输入拒绝原因（可选）" />
      <template #footer>
        <el-button @click="showRejectReason = false">取消</el-button>
        <el-button type="danger" @click="confirmReject">确定拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import StatCard from '@/components/StatCard.vue'
import { getApplicationList, reviewApplication, batchReview, getEnrollmentStatistics } from '@/api/enrollment'

const loading = ref(false)
const applications = ref([])
const total = ref(0)
const page = ref(1)
const keyword = ref('')
const statusFilter = ref('')
const selectedIds = ref([])
const stats = ref({ total: 0, pending: 0, approved: 0, rejected: 0, approvalRate: 0 })
const dialogVisible = ref(false)
const currentItem = ref(null)
const showRejectReason = ref(false)
const rejectReason = ref('')

const statusLabels = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
const statusTagType = { pending: 'warning', approved: 'success', rejected: 'danger' }

function formatDate(row, column, cellValue) {
  const val = cellValue !== undefined ? cellValue : row
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return val
  const y = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')
  return `${y}-${mm}-${dd} ${hh}:${mi}:${ss}`
}

async function loadStats() {
  try {
    const res = await getEnrollmentStatistics()
    stats.value = res.data
  } catch {}
}

async function loadList() {
  loading.value = true
  try {
    const res = await getApplicationList({ page: page.value, size: 10, status: statusFilter.value, keyword: keyword.value })
    applications.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function handleSelectionChange(rows) {
  selectedIds.value = rows.filter(r => r.status === 'pending').map(r => r.id)
}

function openDetail(row) {
  currentItem.value = row
  dialogVisible.value = true
}

async function handleReview(row, status) {
  if (status === 'rejected') {
    currentItem.value = row
    showRejectReason.value = true
    return
  }
  try {
    await ElMessageBox.confirm(`确定通过「${row.realName}」的申请？`, '确认', { type: 'success' })
    await reviewApplication(row.id, { status: 'approved' })
    ElMessage.success('已通过')
    loadList()
    loadStats()
  } catch {}
}

async function confirmReject() {
  if (!currentItem.value) return
  await reviewApplication(currentItem.value.id, { status: 'rejected', reason: rejectReason.value })
  ElMessage.success('已拒绝')
  showRejectReason.value = false
  rejectReason.value = ''
  dialogVisible.value = false
  loadList()
  loadStats()
}

async function handleBatchReview(status) {
  const label = status === 'approved' ? '通过' : '拒绝'
  try {
    await ElMessageBox.confirm(`确定批量${label} ${selectedIds.value.length} 条申请？`, '确认', { type: status === 'approved' ? 'success' : 'warning' })
    await batchReview({ ids: selectedIds.value, status })
    ElMessage.success(`批量${label}成功`)
    selectedIds.value = []
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
.enrollment-view {
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

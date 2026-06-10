<template>
  <div class="assignment-view">
    <!-- 第一层：作业列表 -->
    <template v-if="!selectedAssignment">
      <div class="page-header">
        <h2>作业分发</h2>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>发布作业
        </el-button>
      </div>

      <!-- 统计卡片 -->
      <el-row :gutter="20" style="margin-bottom:20px">
        <el-col :span="6">
          <StatCard label="总作业数" :value="stats.total" icon="Document" icon-bg="#e3f2fd" icon-color="#1976D2" />
        </el-col>
        <el-col :span="6">
          <StatCard label="进行中" :value="stats.active" icon="Clock" icon-bg="#fff3e0" icon-color="#ff9800" />
        </el-col>
        <el-col :span="6">
          <StatCard label="已截止" :value="stats.ended" icon="CircleCheck" icon-bg="#e8f5e9" icon-color="#4caf50" />
        </el-col>
        <el-col :span="6">
          <StatCard label="待分发" :value="stats.pending" icon="TrendCharts" icon-bg="#f3e5f5" icon-color="#9c27b0" />
        </el-col>
      </el-row>

      <!-- 作业列表 -->
      <el-table :data="assignments" stripe v-loading="loading" @row-click="enterAssignment">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="作业标题" min-width="200" />
        <el-table-column prop="deadline" label="截止时间" width="160" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType[row.status]" size="small">{{ statusLabels[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assignedCount" label="已分配" width="80" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="enterAssignment(row)">管理</el-button>
            <el-button type="danger" link size="small" @click.stop="deleteAssignment(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="display:flex;justify-content:flex-end;margin-top:16px">
        <el-pagination v-model:current-page="page" :page-size="10" :total="total" layout="total, prev, pager, next" @current-change="loadList" />
      </div>
    </template>

    <!-- 第二层：人员管理 -->
    <template v-else>
      <div class="page-header">
        <div class="breadcrumb">
          <el-button link @click="selectedAssignment = null">
            <el-icon><ArrowLeft /></el-icon> 返回作业列表
          </el-button>
          <span class="separator">/</span>
          <span class="current">{{ selectedAssignment.title }}</span>
        </div>
      </div>

      <el-card class="assignment-info">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="作业标题">{{ selectedAssignment.title }}</el-descriptions-item>
          <el-descriptions-item label="截止时间">{{ selectedAssignment.deadline }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType[selectedAssignment.status]" size="small">{{ statusLabels[selectedAssignment.status] }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <div class="toolbar" style="margin-top:16px">
        <el-input v-model="memberKeyword" placeholder="搜索姓名/学号" clearable style="width:200px" prefix-icon="Search" @input="loadMembers" />
        <el-radio-group v-model="memberFilter" @change="loadMembers">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="assigned">已分配</el-radio-button>
          <el-radio-button value="unassigned">未分配</el-radio-button>
        </el-radio-group>
        <el-button type="primary" @click="openAssignDialog">
          <el-icon><Plus /></el-icon>添加人员
        </el-button>
        <el-button type="success" :disabled="!selectedMembers.length || !selectedMembers.some(m => !m.assigned)" @click="batchAssignSelected">
          批量分配 ({{ selectedMembers.filter(m => !m.assigned).length }})
        </el-button>
        <el-button type="danger" :disabled="!selectedMembers.length || !selectedMembers.some(m => m.assigned)" @click="batchRemove">
          批量移除 ({{ selectedMembers.filter(m => m.assigned).length }})
        </el-button>
      </div>

      <el-table :data="members" stripe v-loading="memberLoading" @selection-change="handleMemberSelect">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="studentName" label="姓名" width="100" />
        <el-table-column prop="studentNo" label="学号" width="130" />
        <el-table-column prop="major" label="专业" width="120" />
        <el-table-column prop="direction" label="方向" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="primary">{{ row.direction }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="分配状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.assigned ? 'success' : 'info'" size="small">
              {{ row.assigned ? '已分配' : '未分配' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assignedAt" label="分配时间" width="160" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.assigned" type="danger" link size="small" @click="removeMember(row)">移除</el-button>
            <el-button v-else type="primary" link size="small" @click="assignMember(row)">分配</el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>

    <!-- 创建作业对话框 -->
    <el-dialog v-model="showCreateDialog" title="发布作业" width="600px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="作业标题" required>
          <el-input v-model="formData.title" placeholder="请输入作业标题" />
        </el-form-item>
        <el-form-item label="作业描述">
          <el-input v-model="formData.description" type="textarea" :rows="4" placeholder="请输入作业描述和要求" />
        </el-form-item>
        <el-form-item label="截止时间" required>
          <el-date-picker v-model="formData.deadline" type="datetime" placeholder="选择截止时间" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm">发布</el-button>
      </template>
    </el-dialog>

    <!-- 添加人员对话框 -->
    <el-dialog v-model="showAssignDialog" title="添加人员" width="600px">
      <div class="assign-dialog-content">
        <el-input v-model="searchStudent" placeholder="搜索姓名/学号" clearable style="margin-bottom:12px" prefix-icon="Search" />
        <el-table :data="filteredStudents" stripe height="300" @selection-change="handleAssignSelect">
          <el-table-column type="selection" width="50" />
          <el-table-column prop="studentName" label="姓名" width="80" />
          <el-table-column prop="studentNo" label="学号" width="110" />
          <el-table-column prop="major" label="专业" width="120" />
          <el-table-column prop="direction" label="方向" width="80">
            <template #default="{ row }">
              <el-tag size="small" type="primary">{{ row.direction }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" @click="batchAssign">确定分配</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import StatCard from '@/components/StatCard.vue'
import {
  getAssignmentList, getAssignmentStats, createAssignment, deleteAssignment as apiDeleteAssignment,
  getAssignmentMembers, allocateStudents, removeAllocation as apiRemoveAllocation,
  batchRemoveAllocations, getStudentPool
} from '@/api/assignment'

const loading = ref(false)
const assignments = ref([])
const total = ref(0)
const page = ref(1)
const stats = ref({ total: 0, active: 0, ended: 0, pending: 0 })
const showCreateDialog = ref(false)
const selectedAssignment = ref(null)

// 人员管理相关
const memberLoading = ref(false)
const members = ref([])
const memberKeyword = ref('')
const memberFilter = ref('')
const selectedMembers = ref([])
const showAssignDialog = ref(false)
const searchStudent = ref('')
const assignSelection = ref([])

const formData = ref({
  title: '',
  description: '',
  deadline: null
})

// 学生池数据（从后端获取）
const allStudents = ref([])
const studentPoolLoading = ref(false)

const filteredStudents = computed(() => {
  if (!searchStudent.value) return allStudents.value
  const kw = searchStudent.value.toLowerCase()
  return allStudents.value.filter(s =>
    (s.studentName || '').toLowerCase().includes(kw) || (s.studentNo || '').includes(kw)
  )
})

const statusLabels = { active: '进行中', ended: '已截止', pending: '待分发' }
const statusTagType = { active: 'warning', ended: 'success', pending: 'info' }

async function loadStats() {
  try {
    const res = await getAssignmentStats()
    stats.value = res.data
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

async function loadList() {
  loading.value = true
  try {
    const res = await getAssignmentList({ page: page.value, size: 10 })
    assignments.value = res.data.list
    total.value = res.data.total
  } catch (e) {
    console.error('加载作业列表失败', e)
  } finally {
    loading.value = false
  }
}

function enterAssignment(row) {
  selectedAssignment.value = row
  loadMembers()
}

async function loadMembers() {
  if (!selectedAssignment.value) return
  memberLoading.value = true
  try {
    const res = await getAssignmentMembers(selectedAssignment.value.id, {
      keyword: memberKeyword.value,
      filter: memberFilter.value
    })
    members.value = res.data
  } catch (e) {
    console.error('加载人员列表失败', e)
  } finally {
    memberLoading.value = false
  }
}

function handleMemberSelect(rows) {
  selectedMembers.value = rows
}

async function assignMember(row) {
  try {
    await allocateStudents(selectedAssignment.value.id, { studentIds: [row.studentId] })
    ElMessage.success(`已分配给 ${row.studentName}`)
    loadMembers()
  } catch (e) {
    ElMessage.error('分配失败')
  }
}

async function removeMember(row) {
  try {
    await apiRemoveAllocation(selectedAssignment.value.id, row.studentId)
    ElMessage.success(`已移除 ${row.studentName}`)
    loadMembers()
  } catch (e) {
    ElMessage.error('移除失败')
  }
}

function batchRemove() {
  const assignedMembers = selectedMembers.value.filter(m => m.assigned)
  ElMessageBox.confirm(`确定移除选中的 ${assignedMembers.length} 人？`, '确认', { type: 'warning' }).then(async () => {
    try {
      await batchRemoveAllocations(selectedAssignment.value.id, {
        studentIds: assignedMembers.map(m => m.studentId)
      })
      ElMessage.success('批量移除成功')
      selectedMembers.value = []
      loadMembers()
    } catch (e) {
      ElMessage.error('批量移除失败')
    }
  }).catch(() => {})
}

function batchAssignSelected() {
  const unassignedMembers = selectedMembers.value.filter(m => !m.assigned)
  if (!unassignedMembers.length) {
    ElMessage.warning('请选择未分配的人员')
    return
  }
  ElMessageBox.confirm(`确定分配选中的 ${unassignedMembers.length} 人？`, '确认', { type: 'success' }).then(async () => {
    try {
      await allocateStudents(selectedAssignment.value.id, {
        studentIds: unassignedMembers.map(m => m.studentId)
      })
      ElMessage.success('批量分配成功')
      selectedMembers.value = []
      loadMembers()
    } catch (e) {
      ElMessage.error('批量分配失败')
    }
  }).catch(() => {})
}

function handleAssignSelect(rows) {
  assignSelection.value = rows
}

async function batchAssign() {
  if (!assignSelection.value.length) {
    ElMessage.warning('请选择要分配的人员')
    return
  }
  try {
    await allocateStudents(selectedAssignment.value.id, {
      studentIds: assignSelection.value.map(s => s.studentId)
    })
    ElMessage.success(`已分配 ${assignSelection.value.length} 人`)
    showAssignDialog.value = false
    assignSelection.value = []
    loadMembers()
    loadList()
  } catch (e) {
    ElMessage.error('分配失败')
  }
}

async function submitForm() {
  if (!formData.value.title || !formData.value.deadline) {
    ElMessage.warning('请填写必填项')
    return
  }
  try {
    await createAssignment({
      title: formData.value.title,
      description: formData.value.description,
      deadline: formData.value.deadline
    })
    ElMessage.success('作业已发布')
    showCreateDialog.value = false
    formData.value = { title: '', description: '', deadline: null }
    loadList()
    loadStats()
  } catch (e) {
    ElMessage.error('发布失败')
  }
}

async function deleteAssignment(row) {
  try {
    await ElMessageBox.confirm(`确定删除作业「${row.title}」？`, '确认', { type: 'warning' })
    await apiDeleteAssignment(row.id)
    ElMessage.success('已删除')
    loadList()
    loadStats()
  } catch (e) {
    if (e !== 'cancel' && e?.message !== 'cancel') ElMessage.error('删除失败')
  }
}

// 打开添加人员弹窗时加载学生池
async function loadStudentPool() {
  if (!selectedAssignment.value) return
  studentPoolLoading.value = true
  try {
    const res = await getStudentPool(selectedAssignment.value.id, { keyword: searchStudent.value })
    allStudents.value = res.data
  } catch (e) {
    console.error('加载学生池失败', e)
  } finally {
    studentPoolLoading.value = false
  }
}

// 监听添加人员弹窗打开
function openAssignDialog() {
  searchStudent.value = ''
  showAssignDialog.value = true
  loadStudentPool()
}

onMounted(() => {
  loadStats()
  loadList()
})
</script>

<style scoped>
.assignment-view {
  padding: 0;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}
.breadcrumb .separator {
  color: #999;
}
.breadcrumb .current {
  font-weight: 600;
  color: #303133;
}
.assignment-info {
  margin-bottom: 16px;
}
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.assign-dialog-content {
  max-height: 400px;
}
</style>
